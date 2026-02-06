#!/usr/bin/env python3
"""
OpenCode Event Bridge - Utilise le SDK opencode_ai

Écoute les événements SSE d'OpenCode et déclenche les hooks ELF équivalents.
Utilise le SDK opencode_ai au lieu d'appels HTTP bruts.

Usage:
    python event_bridge_sdk.py start    # Démarre le bridge
    python event_bridge_sdk.py status  # Affiche le statut
"""

import json
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
OPENCODE_SERVER = "http://localhost:4096"
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
HOOKS_DIR = Path.home() / ".opencode" / "hooks"
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
COORDINATION_DIR = ELF_DIR / ".coordination"
EVENT_BRIDGE_HEARTBEAT = COORDINATION_DIR / "event-bridge-heartbeat.json"
EVENT_BRIDGE_CONFIG = ELF_DIR / "Open_ELF/orchestrator/event_bridge_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "logging": {
        "throttle_seconds": 5,
        "important_events": ["message", "tool", "error", "session"],
        "summary_interval": 10,
        "max_details_length": 100,
    },
    "status_server": {"default_port": 9998, "fallback_port": 9999},
}

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "event_bridge_sdk.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("EventBridgeSDK")


logger = _setup_logging()


def _log_info(message: str):
    logger.info(message)


def _log_error(message: str):
    logger.error(message)


class HookManager:
    """Gère l'exécution des hooks ELF."""

    def __init__(self):
        self.hooks_dir = HOOKS_DIR
        self.elf_dir = ELF_DIR
        self.session_state = {}

    def run_hook(self, hook_type: str, event_data: Dict[str, Any]) -> bool:
        """Exécute tous les hooks d'un type donné."""
        hook_dir = self.hooks_dir / hook_type
        if not hook_dir.exists():
            logger.debug(f"Hook directory not found: {hook_dir}")
            return False

        # Trouver tous les hooks Python dans ce répertoire
        hook_files = list(hook_dir.glob("*.py"))
        if not hook_files:
            logger.debug(f"No hooks found in {hook_dir}")
            return False

        success = False
        for hook_file in hook_files:
            try:
                # Exécuter le hook avec les données d'événement
                import subprocess

                result = subprocess.run(
                    [sys.executable, str(hook_file)],
                    input=json.dumps(event_data),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    logger.info(f"✅ Hook executed: {hook_file.name}")
                    success = True
                else:
                    logger.warning(
                        f"⚠️ Hook failed: {hook_type}/{hook_file.name} (exit {result.returncode})"
                    )
                    if result.stderr:
                        logger.debug(f"Hook stderr: {result.stderr.decode()[:200]}")

            except subprocess.TimeoutExpired:
                logger.error(f"⏱️ Hook timeout: {hook_type}/{hook_file.name}")
                proc.kill()
            except Exception as e:
                logger.error(f"❌ Hook error: {hook_type}/{hook_file.name}: {e}")

        return success


class OpenCodeSDKBridge:
    """Pont entre OpenCode SDK et les hooks ELF."""

    def __init__(self):
        self.client = None  # SDK client
        self.running = False
        self.base_url = OPENCODE_SERVER
        self.hook_manager = HookManager()
        self.event_count = 0
        self.session_tools = {}  # Track tools used per session
        self.started_at: Optional[datetime] = None
        self.last_event_time: Optional[str] = None
        self.status_server_running = False
        self.current_session_id = None

        # Load configuration
        self.config = self._load_config()
        logging_config = self.config.get("logging", {})

        # Event deduplication and tracking
        self.last_events = {}
        self.event_stats = {}
        self.last_log_time = {}
        self.log_throttle_seconds = logging_config.get("throttle_seconds", 5)
        self.important_events = set(
            logging_config.get(
                "important_events", ["message", "tool", "error", "session"]
            )
        )
        self.event_summary_interval = logging_config.get("summary_interval", 10)
        self.max_details_length = logging_config.get("max_details_length", 100)

        COORDINATION_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        if EVENT_BRIDGE_CONFIG.exists():
            try:
                with open(EVENT_BRIDGE_CONFIG, "r") as f:
                    config = json.load(f)
                logger.info(f"✅ Configuration loaded from {EVENT_BRIDGE_CONFIG}")
                return config
            except Exception as e:
                logger.warning(f"⚠️ Error loading config, using defaults: {e}")
        # Create default config file
        try:
            EVENT_BRIDGE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
            with open(EVENT_BRIDGE_CONFIG, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            logger.info(f"✅ Default configuration created at {EVENT_BRIDGE_CONFIG}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create config file: {e}")

        return DEFAULT_CONFIG

    def _initialize_client(self):
        """Initialize OpenCode SDK client."""
        try:
            from opencode_ai import Client

            self.client = Client(base_url=self.base_url, timeout=30)
            _log_info("✅ OpenCode SDK client initialized")
            return True
        except ImportError:
            _log_error("❌ opencode_ai SDK not installed. Run: pip install opencode_ai")
            return False

    def _write_heartbeat(self):
        """Write heartbeat for monitoring."""
        try:
            # Get top event types
            top_events = sorted(
                self.event_stats.items(), key=lambda x: x[1], reverse=True
            )[:5]

            heartbeat = {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "last_event_time": self.last_event_time,
                "events_processed": self.event_count,
                "running": self.running,
                "status_server_running": self.status_server_running,
                "health": "healthy" if self.status_server_running else "degraded",
                "event_stats": {
                    "total_types": len(self.event_stats),
                    "top_events": dict(top_events),
                    "last_updated": datetime.now().isoformat(),
                },
            }
            EVENT_BRIDGE_HEARTBEAT.write_text(json.dumps(heartbeat), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write heartbeat: {e}")
            # Note: Don't fail completely, but log error for visibility

    def _check_opencode_server(self) -> bool:
        """Check if OpenCode server is accessible."""
        try:
            if self.client:
                response = self.client.app.get(timeout=5)
                self.status_server_running = True
                return True
        except Exception as e:
            logger.debug(f"OpenCode server check failed: {e}")
            self.status_server_running = False
            return False

    def _process_sse_line(self, line: str):
        """Traite une ligne SSE."""
        # Format SSE: data: {...}
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str:
                try:
                    data = json.loads(data_str)
                    self._handle_event(data)
                except json.JSONDecodeError as e:
                    _log_error(f"Failed to parse SSE data: {e}")
        elif line.startswith("event:"):
            # Type d'événement (optionnel)
            pass

    def _handle_event(self, event: Dict[str, Any]):
        """Gère un événement reçu d'OpenCode."""
        event_type = event.get("type", "unknown")
        event_properties = event.get("properties", {})

        # Extract useful details for logging
        details = ""
        if event_type == "tool":
            tool_name = event_properties.get("tool", "unknown")
            session_id = event_properties.get("session_id", "")
            details = f"Tool: {tool_name} | Session: {session_id[:8] if session_id else 'N/A'}"
        elif event_type == "message":
            content_preview = event_properties.get("content", "")[:50]
            details = f"Content: {content_preview}..."
        elif event_type == "error":
            error_msg = event_properties.get("error", "Unknown error")
            details = f"Error: {error_msg[:100]}"
        elif event_type == "thinking":
            pass  # Ignorer les événements thinking
        else:
            details = f"Type: {event_type}"

        self._record_event(event_type, details)

        logger.debug(f"📡 Processing event #{self.event_count}: {event_type}")

        # Mapper les événements OpenCode aux hooks ELF
        if event_type == "message":
            self._handle_message_event(event)
        elif event_type == "tool":
            self._handle_tool_event(event)
        elif event_type == "error":
            self._handle_error_event(event)
        elif event_type == "failure":
            self._handle_failure_event(event)
        elif event_type == "session.created":
            self._handle_session_created(event)
        elif event_type == "thinking":
            self._handle_thinking_event(event)

    def _record_event(self, event_type: str, details: str):
        """Enregistre un événement avec déduplication."""
        # Update event count
        self.event_count += 1

        # Update event stats
        if event_type not in self.event_stats:
            self.event_stats[event_type] = 0
        self.event_stats[event_type] += 1

        # Update last event time
        self.last_event_time = datetime.now().isoformat()

        # Throttling for non-important events
        if event_type in self.important_events:
            self._log_event_to_file(event_type, details)
        else:
            current_time = time.time()
            last_logged = self.last_log_time.get(event_type, 0)

            if current_time - last_logged >= self.log_throttle_seconds:
                self._log_event_to_file(event_type, details)
                self.last_log_time[event_type] = current_time

    def _log_event_to_file(self, event_type: str, details: str):
        """Écrit un événement dans le fichier de log."""
        try:
            log_file = LOGS_DIR / f"{event_type}_events.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {details}\n")
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")

    def _handle_message_event(self, event: Dict[str, Any]):
        """Gère un event de message (équivalent à UserPromptSubmit)."""
        props = event.get("properties", {})
        role = props.get("role", "unknown")
        content = props.get("content", "")
        session_id = props.get("session_id")

        if role == "user":
            logger.info(f"👤 User message detected")

            # Équivalent à UserPromptSubmit hook
            hook_data = {
                "event_type": "UserPromptSubmit",
                "session_id": session_id,
                "message": content,
                "timestamp": datetime.now().isoformat(),
            }

            self.hook_manager.run_hook("UserPromptSubmit", hook_data)

            # Préparer le contexte pour PostToolUse
            if session_id:
                self.session_tools[session_id] = {
                    "user_message": content,
                    "tools_used": [],
                    "start_time": time.time(),
                }

    def _handle_tool_event(self, event: Dict[str, Any]):
        """Gère un event de tool."""
        props = event.get("properties", {})
        tool_name = props.get("tool", "unknown")
        session_id = props.get("session_id", "")

        if session_id in self.session_tools:
            self.session_tools[session_id]["tools_used"].append(tool_name)
            logger.debug(f"🔧 Tool used: {tool_name} in session {session_id}")

    def _handle_error_event(self, event: Dict[str, Any]):
        """Gère un event d'erreur."""
        logger.error(f"❌ OpenCode error detected: {event}")

    def _handle_failure_event(self, event: Dict[str, Any]):
        """Gère un event de failure."""
        logger.warning(f"⚠️ OpenCode failure detected")

    def _handle_session_created(self, event: Dict[str, Any]):
        """Gère un event de création de session."""
        props = event.get("properties", {})
        session_id = props.get("id", "")
        self.current_session_id = session_id
        logger.info(f"🆕 Session created: {session_id[:8]}")

    def _handle_thinking_event(self, event: Dict[str, Any]):
        """Gère un event de thinking (ignoré)."""
        logger.debug("💭 Thinking event (ignored)")

    def start(self):
        """Démarre le pont Event Bridge."""
        _log_info("🌉 OpenCode Event Bridge SDK Starting")

        # Vérifier la connexion à OpenCode
        if not self._initialize_client():
            _log_error("❌ Cannot initialize OpenCode SDK client")
            return False

        if not self._check_opencode_server():
            _log_error("❌ Cannot connect to OpenCode server")
            _log_error(f"❌ Cannotconnect to OpenCode: {e}")
            return False

        self.running = True
        self.started_at = datetime.now()
        self.status_server_running = True
        _log_info("✅ Connected to OpenCode server")

        # Écouter le stream SSE des événements OpenCode
        _log_info("👂 Listening to OpenCode events...")

        try:
            response = self.client.get(path="/events", stream=True)
            # Le SDK gère le streaming automatiquement
            _log_info("📡 Connected to SSE stream")

            for line in response.text.split("\n"):
                if line.strip():
                    self._process_sse_line(line)

        except Exception as e:
            _log_error(f"❌ Cannot connect to OpenCode: {e}")
            return False

    def stop(self):
        """Arrête le pont Event Bridge."""
        _log_info("🛑 Stopping Event Bridge...")
        self.running = False


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print("Usage: python event_bridge_sdk.py <command>")
        print("Commands:")
        print("  start    Start event bridge")
        print("  status   Show current status")
        sys.exit(1)

    command = sys.argv[1]

    bridge = OpenCodeSDKBridge()

    if command == "start":
        bridge.start()
    elif command == "status":
        print(f"\n=== Event Bridge SDK Status ===")
        if EVENT_BRIDGE_HEARTBEAT.exists():
            with open(EVENT_BRIDGE_HEARTBEAT, "r") as f:
                heartbeat = json.load(f)
                print(json.dumps(heartbeat, indent=2))
        else:
            print("Event Bridge not running")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
