#!/usr/bin/env python3
"""
OpenCode Connection Manager - Version Simplifiée

Utilise des appels HTTP bruts comme l'ancien opencode_client.py
mais avec structure unifiée et cache des sessions.

Compatible avec le code existant qui attend l'API suivante:
- create_session(title)
- send_message(session_id, message, model)
- close_session(session_id)
"""

import os
import json
import logging
import requests
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
from contextlib import contextmanager

# Logger unifié
_logger = logging.getLogger("opconnection")

# Constants
DEFAULT_BASE_URL = "http://localhost:4096"
DEFAULT_TIMEOUT = 30
DEFAULT_MODEL = "opencode/big-pickle"

# Singleton instance
_instance: Optional["OpenCodeConnection"] = None
_instance_lock = threading.Lock()


class SessionInfo:
    """Informations de session avec timestamps."""

    def __init__(self, session_id: str, title: str, created_at: datetime):
        self.session_id = session_id
        self.title = title
        self.created_at = created_at
        self.last_used = datetime.now(timezone.utc)
        self.message_count = 0
        self.tools_used: List[str] = []

    def update_usage(self):
        """Met à jour l'utilisation."""
        self.last_used = datetime.now(timezone.utc)
        self.message_count += 1

    def add_tool(self, tool_name: str):
        """Ajoute un outil utilisé."""
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)


class OpenCodeConnection:
    """
    Gestionnaire de connexion OpenCode simplifié.

    Features:
    - Appels HTTP bruts (requests)
    - Cache des sessions en mémoire
    - Thread-safety
    - Gestion de health basique
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        model: str = DEFAULT_MODEL,
    ):
        """Initialise le gestionnaire de connexion."""

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.model = model
        self._sessions: Dict[str, SessionInfo] = {}
        self._session_lock = threading.Lock()
        self._session_file = Path(
            "/home/bamer/.opencode/emergent-learning/.coordination/sessions.json"
        )

        # Charger les sessions existantes
        self._load_sessions()

        _logger.info(f"OpenCodeConnection initialisé: {base_url}")

    def _load_sessions(self):
        """Charge les sessions depuis le fichier."""
        try:
            if self._session_file.exists():
                with open(self._session_file, "r") as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        created_at_str = session_data.get("created_at", datetime.now().isoformat())
                        self._sessions[session_id] = SessionInfo(
                            session_id=session_id,
                            title=session_data.get("title", ""),
                            created_at=datetime.fromisoformat(created_at_str),
                        )
                _logger.info(f"Chargé {len(self._sessions)} sessions depuis le fichier")
        except Exception as e:
            _logger.warning(f"Erreur chargement sessions: {e}")

    def _save_sessions(self):
        """Sauvegarde les sessions dans le fichier."""
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
            _logger.error(f"Erreur sauvegarde sessions: {e}")

    def create_session(
        self, title: str = "elf-session", model: str = None
    ) -> Optional[str]:
        """Crée une nouvelle session."""
        session_id = f"ses_{int(datetime.now().timestamp())}"

        session_data = {
            "title": title,
            "model": model or self.model,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "last_used": None,
            "tools_used": [],
        }

        try:
            response = requests.post(
                f"{self.base_url}/session",
                json={"title": title},
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ELF/1.0 (OpenCodeConnection)",
                    "Accept": "application/json",
                },
            )

            if response.status_code == 200:
                result = response.json()
                session_id = result.get("id", session_id)

                # Mettre en cache
                with self._session_lock:
                    if self._session_file.exists():
                        with open(self._session_file, 'r') as f:
                            data = json.load(f)
                            created_at_str = session_data.get("created_at")
                            self._sessions[session_id] = SessionInfo(
                                session_id=session_id,
                                title=title,
                                created_at=datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc).isoformat(),
                            )
                    self._sessions[session_id] = SessionInfo(
                        session_id=session_id,
                        title=title,
                        created_at=datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc).isoformat(),
                        )
                        ),
                    )

                # Sauvegarder
                self._save_sessions()

                _logger.info(f"Session créée: {session_id[:8]} ({title})")
                return session_id

            else:
                _logger.error(f"Erreur création session: {response.status_code}")
                return None

        except Exception as e:
            _logger.error(f"Échec création session: {e}")
            return None

    def send_message(
        self, session_id: str, message: str, model: str = None
    ) -> Optional[str]:
        """Envoie un message dans une session."""
        if session_id not in self._sessions:
            _logger.warning(f"Session {session_id[:8]} non trouvée")
            return None

        session_info = self._sessions[session_id]

        try:
            data = {
                "model": {"providerID": "opencode", "modelID": model or self.model},
                "parts": [
                    {"type": "text", "text": session_info.last_message or ""},
                    {"type": "text", "text": message},
                ],
            }

            response = requests.post(
                f"{self.base_url}/session/{session_id}/message",
                json=data,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ELF/1.0 (OpenCodeConnection)",
                    "Accept": "application/json",
                },
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("content", "")

                # Mettre à jour
                session_info.update_usage()

                # Sauvegarder
                self._save_sessions()

                _logger.debug(f"Message envoyé à {session_id[:8]}: {content[:100]}...")
                return content

            else:
                _logger.error(f"Erreur envoi message: {response.status_code}")
                return None

        except Exception as e:
            _logger.error(f"Échec envoi message: {e}")
            return None

    def close_session(self, session_id: str) -> bool:
        """Ferme une session."""
        if session_id not in self._sessions:
            _logger.warning(f"Session {session_id[:8]} non trouvée")
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/session/{session_id}",
                timeout=self.timeout,
                headers={
                    "User-Agent": "ELF/1.0 (OpenCodeConnection)",
                    "Accept": "application/json",
                },
            )

            if response.status_code in (200, 204):
                # Retirer du cache
                with self._session_lock:
                    if session_id in self._sessions:
                        del self._sessions[session_id]

                # Sauvegarder
                self._save_sessions()

                _logger.info(f"Session fermée: {session_id[:8]}")
                return True

            else:
                _logger.error(f"Erreur fermeture session: {response.status_code}")
                return False

        except Exception as e:
            _logger.error(f"Échec fermeture session: {e}")
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Liste toutes les sessions actives."""
        return [
            {
                "session_id": session_id,
                "title": info.title,
                "created_at": info.created_at.isoformat(),
                "last_used": info.last_used.isoformat(),
                "message_count": info.message_count,
                "tools_used": info.tools_used,
            }
            for session_id, info in self._sessions.items()
        ]

    def is_healthy(self) -> bool:
        """Vérifie si le serveur est accessible."""
        try:
            response = requests.get(f"{self.base_url}/global/health", timeout=5)
            return response.status_code == 200
        except:
            return False


def get_opconnection(**kwargs) -> OpenCodeConnection:
    """Factory pour obtenir le singleton."""
    global _instance

    if _instance is None:
        with _instance_lock:
            _instance = OpenCodeConnection(**kwargs)
            _logger.info("OpenCodeConnection singleton créé")

    return _instance


def reset_opconnection():
    """Réinitialise le singleton."""
    global _instance

    with _instance_lock:
        _instance = None
        _logger.info("OpenCodeConnection singleton réinitialisé")


# Exporter pour compatibilité
__all__ = [
    "OpenCodeConnection",
    "SessionInfo",
    "get_opconnection",
    "reset_opconnection",
]
