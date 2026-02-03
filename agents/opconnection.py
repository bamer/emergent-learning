#!/usr/bin/env python3
"""
OpenCode Connection Manager - Singleton pour tous les composants ELF

Gestionnaire unifié des connexions OpenCode.
Remplace la duplication massive dans:
- event_bridge.py
- watcher/launcher.py
- orchestrator.py
- agent_execution_engine.py
- experiment_analyzer.py

Usage:
    from agents.opconnection import get_opconnection

    conn = get_opconnection()
    session = conn.create_session("elf")
    response = conn.send_message(session, "Hello!")
    conn.close_session(session)
"""

import json
import logging
import requests
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

# Logger
_logger = logging.getLogger("opconnection")

# Constants
DEFAULT_BASE_URL = "http://localhost:4096"
DEFAULT_TIMEOUT = 30
DEFAULT_MODEL = "opencode/big-pickle"

# Note on HTTP API:
# OpenCode's /session/{id}/message endpoint is designed for the TUI and waits
# for user interaction. For programmatic use, prefer:
# - agents/opencode_client.py: Handles TUI interaction properly
# - CLI: opencode --model <model> --prompt "<prompt>"
# - OpenCode Task tool: For subagent spawning within OpenCode

# Singleton
_instance = None
_instance_lock = threading.Lock()


class SessionInfo:
    """Informations de session."""

    def __init__(self, session_id: str, title: str, created_at: datetime):
        self.session_id = session_id
        self.title = title
        self.created_at = created_at
        self.last_used = datetime.now(timezone.utc)
        self.message_count = 0
        self.tools_used: List[str] = []

    def update_usage(self):
        self.last_used = datetime.now(timezone.utc)
        self.message_count += 1

    def add_tool(self, tool_name: str):
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)


class OpenCodeConnection:
    """
    Gestionnaire de connexion OpenCode unifié.

    Features:
    - Singleton thread-safe
    - Cache des sessions
    - HTTP requests simples
    - Interface compatible avec code existant
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        model: str = DEFAULT_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.model = model
        self._sessions: Dict[str, SessionInfo] = {}
        self._session_lock = threading.Lock()
        self._session_file = Path(
            "/home/bamer/.opencode/emergent-learning/.coordination/sessions.json"
        )
        self._load_sessions()
        _logger.info(f"OpenCodeConnection: {base_url}")

    def _load_sessions(self):
        """Charge les sessions depuis le fichier."""
        try:
            if self._session_file.exists():
                with open(self._session_file, "r") as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        created_at_str = session_data.get("created_at", "")
                        self._sessions[session_id] = SessionInfo(
                            session_id=session_id,
                            title=session_data.get("title", ""),
                            created_at=datetime.fromisoformat(created_at_str)
                            if created_at_str
                            else datetime.now(timezone.utc),
                        )
        except Exception as e:
            _logger.warning(f"Sessions load error: {e}")

    def _save_sessions(self):
        """Sauvegarde les sessions."""
        try:
            data = {
                session_id: {
                    "title": info.title,
                    "created_at": info.created_at.isoformat(),
                    "message_count": info.message_count,
                    "last_used": info.last_used.isoformat(),
                    "tools_used": info.tools_used,
                }
                for session_id, info in self._sessions.items()
            }
            self._session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._session_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Sessions save error: {e}")

    def create_session(self, title: str = "elf-session") -> Optional[str]:
        """Crée une nouvelle session."""
        try:
            response = requests.post(
                f"{self.base_url}/session",
                json={"title": title},
                timeout=self.timeout,
                headers={"Content-Type": "application/json", "User-Agent": "ELF/1.0"},
            )

            if response.status_code == 200:
                result = response.json()
                session_id = result.get("id")

                # Le timestamp 'created' est en millisecondes (nombre)
                time_data = result.get("time", {})
                created_timestamp = time_data.get("created", 0)
                if isinstance(created_timestamp, (int, float)):
                    created_at = datetime.fromtimestamp(
                        created_timestamp / 1000, tz=timezone.utc
                    )
                else:
                    created_at = datetime.now(timezone.utc)

                with self._session_lock:
                    self._sessions[session_id] = SessionInfo(
                        session_id, title, created_at
                    )

                self._save_sessions()
                _logger.info(f"Session: {session_id[:8]} ({title})")
                return session_id

            _logger.error(f"Session error: {response.status_code}")
            return None

        except Exception as e:
            _logger.error(f"Session create error: {e}")
            return None

    def send_message(
        self, session_id: str, message: str, model: str = None, timeout: int = None
    ) -> Optional[str]:
        """Envoie un message via OpenCode SDK.

        Uses the OpenCode Python SDK for proper programmatic access.
        Falls back to HTTP API if SDK fails.

        Args:
            session_id: The session ID to send the message to
            message: The message text to send
            model: Optional model override
            timeout: Request timeout in seconds (default: self.timeout)

        Returns:
            Response text or None if failed
        """
        if session_id not in self._sessions:
            _logger.warning(f"Session not found: {session_id[:8]}")
            return None

        # Try SDK first
        try:
            from opencode_ai import Opencode

            # Create SDK client
            client = Opencode(base_url=self.base_url)

            # Send message via SDK
            response = client.session.chat(
                id=session_id,
                model_id=model or self.model.split("/")[-1],  # Extract model name
                provider_id=model or self.model.split("/")[0]
                if "/" in (model or self.model)
                else "opencode",
                parts=[{"type": "text", "text": message}],
                timeout=timeout or self.timeout,
            )

            # Extract text from response
            text_content = ""
            if hasattr(response, "parts"):
                for part in response.parts:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_content += part.get("text", "")
                    elif hasattr(part, "type") and part.type == "text":
                        text_content += getattr(part, "text", "")

            if text_content.strip():
                with self._session_lock:
                    if session_id in self._sessions:
                        self._sessions[session_id].update_usage()
                self._save_sessions()
                return text_content.strip()

        except Exception as sdk_error:
            _logger.debug(f"SDK failed, falling back to HTTP API: {sdk_error}")

            # Fall back to HTTP API
            try:
                data = {
                    "model": {"providerID": "opencode", "modelID": model or self.model},
                    "parts": [{"type": "text", "text": message}],
                }

                request_timeout = timeout if timeout is not None else self.timeout

                response = requests.post(
                    f"{self.base_url}/session/{session_id}/message",
                    json=data,
                    timeout=request_timeout,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ELF/1.0",
                    },
                )

                if response.status_code == 200:
                    # Try to parse JSON response
                    try:
                        result = response.json()
                        parts = result.get("parts", [])
                        content = ""
                        for part in parts:
                            if part.get("type") == "text":
                                content += part.get("text", "")

                        with self._session_lock:
                            if session_id in self._sessions:
                                self._sessions[session_id].update_usage()

                        self._save_sessions()
                        return content.strip() if content else None
                    except json.JSONDecodeError:
                        # Response is not JSON - likely OpenCode is waiting for interaction
                        _logger.warning(
                            "OpenCode message endpoint returned non-JSON response. "
                            "This usually means OpenCode is waiting for user interaction in TUI."
                        )
                        return None

                _logger.warning(f"Message failed with status: {response.status_code}")
                return None

            except requests.exceptions.Timeout:
                _logger.warning(
                    "OpenCode message request timed out. "
                    "The endpoint is likely waiting for user interaction."
                )
                return None
            except Exception as http_error:
                _logger.error(f"HTTP API also failed: {http_error}")
                return None

        return None

    def close_session(self, session_id: str) -> bool:
        """Ferme une session."""
        if session_id not in self._sessions:
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/session/{session_id}",
                timeout=self.timeout,
                headers={"User-Agent": "ELF/1.0"},
            )

            if response.status_code in (200, 204):
                with self._session_lock:
                    if session_id in self._sessions:
                        del self._sessions[session_id]
                self._save_sessions()
                _logger.info(f"Session closed: {session_id[:8]}")
                return True

            return False

        except Exception as e:
            _logger.error(f"Close error: {e}")
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Liste les sessions."""
        return [
            {
                "session_id": session_id,
                "title": info.title,
                "created_at": info.created_at.isoformat(),
                "message_count": info.message_count,
            }
            for session_id, info in self._sessions.items()
        ]

    def is_healthy(self) -> bool:
        """Vérifie la santé du serveur."""
        try:
            response = requests.get(f"{self.base_url}/global/health", timeout=5)
            return response.status_code == 200
        except:
            return False


def get_opconnection(**kwargs) -> OpenCodeConnection:
    """Factory singleton."""
    global _instance

    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = OpenCodeConnection(**kwargs)
                _logger.info("Singleton créé")

    return _instance


def reset_opconnection():
    """Reset pour tests."""
    global _instance
    _instance = None


__all__ = [
    "OpenCodeConnection",
    "SessionInfo",
    "get_opconnection",
    "reset_opconnection",
]
