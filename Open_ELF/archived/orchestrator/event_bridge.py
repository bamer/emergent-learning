#!/usr/bin/env python3
"""
OpenCode Event Bridge - Emulates Claude Code hooks using OpenCode SSE events

Écoute les événements SSE d'OpenCode et déclenche les hooks ELF équivalents.

Usage:
    python event_bridge.py start  # Démarre le bridge
    python event_bridge.py status # Affiche le statut
"""

import json
import logging
import requests
import sys
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
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

# Setup logging (unified + local)
sys.path.insert(0, str(ELF_DIR / "agents"))
try:
    from elf_logging import get_logger, log_info, log_error

    logger = get_logger("event_bridge")

    def _log_info(message: str):
        log_info("event_bridge", message)

    def _log_error(message: str):
        log_error("event_bridge", message)

except Exception:
    logging.basicConfig(
        level=logging.WARNING,  # Reduce verbosity - only warnings and errors
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "event_bridge.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("EventBridge")

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
                # Préparer les données pour le hook
                hook_input = json.dumps(event_data)

                # Préparer l'environnement avec le chemin ELF
                hook_env = dict(subprocess.os.environ)
                hook_env["ELF_BASE_PATH"] = str(self.elf_dir)

                # Ajouter le répertoire ELF au PYTHONPATH pour les imports
                python_path = hook_env.get("PYTHONPATH", "")
                if python_path:
                    hook_env["PYTHONPATH"] = f"{self.elf_dir}:{python_path}"
                else:
                    hook_env["PYTHONPATH"] = str(self.elf_dir)

                # Exécuter le hook avec les données en stdin
                proc = subprocess.Popen(
                    [sys.executable, str(hook_file)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.elf_dir),
                    env=hook_env,
                )

                stdout, stderr = proc.communicate(input=hook_input.encode(), timeout=30)

                if proc.returncode == 0:
                    logger.info(f"✅ Hook executed: {hook_type}/{hook_file.name}")
                    if stdout:
                        try:
                            result = json.loads(stdout.decode())
                            logger.debug(f"Hook result: {result}")
                        except Exception as e:
                            logger.error(
                                f"Failed to parse hook result from {hook_file.name}: {e}"
                            )
                            # Continue with other hooks but log the error
                    success = True
                else:
                    logger.warning(
                        f"⚠️ Hook failed: {hook_type}/{hook_file.name} (exit {proc.returncode})"
                    )
                    if stderr:
                        logger.debug(f"Hook stderr: {stderr.decode()[:200]}")

            except subprocess.TimeoutExpired:
                logger.error(f"⏱️ Hook timeout: {hook_type}/{hook_file.name}")
                proc.kill()
            except Exception as e:
                logger.error(f"❌ Hook error: {hook_type}/{hook_file.name}: {e}")

        return success


class EventBridge:
    """Pont entre les events OpenCode et les hooks ELF."""

    def __init__(self):
        self.running = False
        self.base_url = OPENCODE_SERVER
        self.hook_manager = HookManager()
        self.event_count = 0
        self.session_tools = {}  # Track tools used per session
        self.started_at: Optional[datetime] = None
        self.last_event_time: Optional[str] = None
        self.status_server_running = False  # Track status server health

        # Load configuration
        self.config = self._load_config()
        logging_config = self.config.get("logging", {})

        # Event deduplication and tracking
        self.last_events = {}  # Track last event types to avoid spam
        self.event_stats = {}  # Count events by type
        self.last_log_time = {}  # Track when we last logged specific event types
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
            # Note: Don't fail completely, but log the error for visibility

    def _record_event(self, event_type: str = "unknown", details: str = ""):
        """Increment counters and update heartbeat for any event with smart logging."""
        self.event_count += 1
        self.last_event_time = datetime.now().isoformat()

        # Track event statistics
        self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1

        # Update heartbeat without logging every time
        self._write_heartbeat()

        # Smart logging strategy
        current_time = datetime.now()
        last_log = self.last_log_time.get(event_type, datetime.min)

        # Log important events immediately, others with throttling
        is_important = any(imp in event_type.lower() for imp in self.important_events)

        should_log = (
            is_important
            or (current_time - last_log).total_seconds() > self.log_throttle_seconds
            or self.event_stats[event_type] == 1  # First time we see this event type
        )

        if should_log:
            # Build informative log message
            if self.event_stats[event_type] == 1:
                frequency = " (first time)"
            elif (
                self.event_stats[event_type] % self.event_summary_interval == 0
            ):  # Every Nth occurrence
                frequency = f" (#{self.event_stats[event_type]} total)"
            else:
                frequency = ""

            log_message = (
                f"📡 Event: {event_type}{frequency}"
                f" | Total: {self.event_count}"
                f" | Type count: {self.event_stats[event_type]}"
            )

            if details:
                log_message += (
                    f" | Details: {details[:100]}{'...' if len(details) > 100 else ''}"
                )

            # Use appropriate log level
            if "error" in event_type.lower():
                _log_error(f"❌ {log_message}")
            elif is_important:
                _log_info(f"🔍 {log_message}")
            else:
                logger.debug(log_message)

            self.last_log_time[event_type] = current_time

    def start(self):
        """Démarre le bridge d'événements."""
        _log_info("=" * 70)
        _log_info("🌉 OpenCode Event Bridge Starting")
        _log_info("=" * 70)

        # Vérifier la connexion à OpenCode
        try:
            response = requests.get(f"{self.base_url}/global/health", timeout=5)
            if response.status_code != 200:
                _log_error("❌ OpenCode server not accessible")
                return False
        except Exception as e:
            _log_error(f"❌ Cannot connect to OpenCode: {e}")
            return False

        _log_info("✅ Connected to OpenCode server")
        self.running = True
        self.started_at = datetime.now()
        self._write_heartbeat()

        # Démarrer l'écoute des events dans un thread
        events_thread = threading.Thread(target=self._listen_events, daemon=True)
        events_thread.start()

        # Démarrer le polling des sessions (pour capturer l'activité même sans SSE)
        polling_thread = threading.Thread(target=self._poll_sessions, daemon=True)
        polling_thread.start()

        # Démarrer le serveur HTTP pour le status
        try:
            self._start_status_server()
        except RuntimeError as e:
            _log_error(f"❌ Critical error starting status server: {e}")
            # Status server is critical for monitoring, but don't stop the bridge
            # Instead mark as degraded state
            self.status_server_running = False
        else:
            self.status_server_running = True

        return True

    def _listen_events(self):
        """Écoute le stream SSE des événements OpenCode."""
        _log_info("👂 Listening to OpenCode events...")

        while self.running:
            try:
                # Se connecter au stream SSE
                response = requests.get(
                    f"{self.base_url}/event",
                    stream=True,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=60,
                )

                if response.status_code != 200:
                    _log_error(
                        f"❌ Failed to connect to event stream: {response.status_code}"
                    )
                    time.sleep(5)
                    continue

                _log_info("✅ Connected to SSE stream")

                # Traiter les events ligne par ligne
                for line in response.iter_lines():
                    if not self.running:
                        break

                    if line:
                        line_str = line.decode("utf-8")
                        self._process_sse_line(line_str)

            except requests.exceptions.ChunkedEncodingError:
                _log_info("⚠️ SSE stream disconnected, reconnecting...")
                time.sleep(2)
            except Exception as e:
                _log_error(f"❌ Error listening to events: {e}")
                time.sleep(5)

    def _poll_sessions(self):
        """Poll les sessions actives pour détecter les outils utilisés."""
        _log_info("🔄 Starting session polling...")

        # Tracker les messages déjà vus par session
        seen_messages = {}

        while self.running:
            try:
                # Récupérer toutes les sessions
                response = requests.get(f"{self.base_url}/session", timeout=10)
                if response.status_code != 200:
                    time.sleep(30)
                    continue

                sessions = response.json()

                for session in sessions:
                    session_id = session.get("id")
                    if not session_id:
                        continue

                    # Récupérer les messages de cette session
                    msg_response = requests.get(
                        f"{self.base_url}/session/{session_id}/message", timeout=10
                    )

                    if msg_response.status_code != 200:
                        continue

                    messages = msg_response.json()

                    # Initialiser le tracker pour cette session
                    if session_id not in seen_messages:
                        seen_messages[session_id] = set()

                    # Traiter les nouveaux messages
                    for msg in messages:
                        msg_id = msg.get("info", {}).get("id")
                        if not msg_id or msg_id in seen_messages[session_id]:
                            continue

                        seen_messages[session_id].add(msg_id)

                        # Vérifier si c'est un message avec des outils
                        parts = msg.get("parts", [])
                        for part in parts:
                            if part.get("type") == "tool_use":
                                tool_name = part.get("tool", "unknown")
                                tool_input = part.get("input", {})

                                _log_info(f"🔧 Tool detected via polling: {tool_name}")

                                # Déclencher le hook
                                hook_data = {
                                    "event_type": "PostToolUse",
                                    "tool_name": tool_name,
                                    "tool_input": tool_input,
                                    "tool_output": {},
                                    "success": True,
                                    "session_id": session_id,
                                    "timestamp": datetime.now().isoformat(),
                                }

                                self._record_event(
                                    "tool_poll",
                                    f"Tool: {tool_name} | Session: {session_id[:8]}",
                                )
                                self.hook_manager.run_hook("PostToolUse", hook_data)

                # Attendre avant le prochain poll
                time.sleep(30)

            except Exception as e:
                _log_error(f"❌ Error polling sessions: {e}")
                time.sleep(30)

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
        """Gère un event d'outil (équivalent à PostToolUse)."""
        props = event.get("properties", {})
        tool_name = props.get("tool", "unknown")
        tool_input = props.get("input", {})
        tool_output = props.get("output", {})
        session_id = props.get("session_id")
        success = props.get("success", True)

        logger.info(f"🔧 Tool execution: {tool_name} (success={success})")

        # Stocker l'outil utilisé
        if session_id and session_id in self.session_tools:
            self.session_tools[session_id]["tools_used"].append(
                {
                    "tool": tool_name,
                    "input": tool_input,
                    "output": tool_output,
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Hook PreToolUse (avant exécution - on l'appelle quand même pour la compatibilité)
        pre_tool_data = {
            "event_type": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "session_id": session_id,
        }
        self.hook_manager.run_hook("PreToolUse", pre_tool_data)

        # Hook PostToolUse (après exécution)
        post_tool_data = {
            "event_type": "PostToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "success": success,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

        # Ajouter les heuristiques si disponibles
        if session_id and session_id in self.session_tools:
            session_data = self.session_tools[session_id]
            post_tool_data["user_message"] = session_data.get("user_message", "")
            post_tool_data["tools_used"] = session_data["tools_used"]

        self.hook_manager.run_hook("PostToolUse", post_tool_data)

        # Si échec, déclencher aussi le learning-loop pour enregistrer l'échec
        if not success:
            logger.warning(f"⚠️ Tool {tool_name} failed - triggering learning hooks")
            failure_data = {
                **post_tool_data,
                "event_type": "ToolFailure",
                "failure_reason": tool_output.get("error", "Tool execution failed"),
            }
            self.hook_manager.run_hook("learning-loop", failure_data)

    def _handle_session_created(self, event: Dict[str, Any]):
        """Gère la création d'une session."""
        props = event.get("properties", {})
        session_id = props.get("id")
        logger.info(f"📁 Session created: {session_id}")

        # Initialiser le suivi pour cette session
        if session_id:
            self.session_tools[session_id] = {
                "tools_used": [],
                "start_time": time.time(),
            }

    def _handle_thinking_event(self, event: Dict[str, Any]):
        """Gère un event de thinking (pour la mémoire sémantique)."""
        props = event.get("properties", {})
        thinking_content = props.get("content", "")
        session_id = props.get("session_id")

        logger.debug(f"💭 Thinking event received")

        # Hook pour la mémoire sémantique
        hook_data = {
            "event_type": "Thinking",
            "thinking": thinking_content,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

        self.hook_manager.run_hook("PreToolUse", hook_data)

    def _handle_error_event(self, event: Dict[str, Any]):
        """Gère un event d'erreur - enregistre l'échec pour le learning."""
        props = event.get("properties", {})
        error_message = props.get("message", "Unknown error")
        error_type = props.get("error_type", "error")
        session_id = props.get("session_id")
        tool_name = props.get("tool", "unknown")

        logger.error(f"❌ Error detected: {error_type} - {error_message[:100]}")

        # Hook pour enregistrer l'échec
        hook_data = {
            "event_type": "Error",
            "error_type": error_type,
            "error_message": error_message,
            "tool_name": tool_name,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }

        # Déclencher PostToolUse avec l'échec
        self.hook_manager.run_hook("PostToolUse", hook_data)

        # Déclencher aussi un hook spécifique pour les erreurs
        self.hook_manager.run_hook("learning-loop", hook_data)

    def _handle_failure_event(self, event: Dict[str, Any]):
        """Gère un event de failure - enregistre l'échec pour le learning."""
        props = event.get("properties", {})
        failure_reason = props.get("reason", "Unknown failure")
        session_id = props.get("session_id")
        tool_name = props.get("tool", "unknown")
        tool_input = props.get("input", {})

        logger.error(f"💥 Failure detected: {failure_reason[:100]}")

        # Hook pour enregistrer l'échec
        hook_data = {
            "event_type": "Failure",
            "failure_reason": failure_reason,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
        }

        # Déclencher PostToolUse avec l'échec
        self.hook_manager.run_hook("PostToolUse", hook_data)

        # Déclencher aussi un hook spécifique pour les échecs
        self.hook_manager.run_hook("learning-loop", hook_data)

    def _start_status_server(self):
        """Démarre un serveur HTTP simple pour exposer le status."""
        try:
            bridge = self  # Capture reference to EventBridge instance

            class StatusHandler(BaseHTTPRequestHandler):
                def do_GET(handler_self):
                    if handler_self.path == "/status":
                        handler_self.send_response(200)
                        handler_self.send_header("Content-type", "application/json")
                        handler_self.end_headers()

                        uptime_seconds = None
                        if bridge.started_at:
                            uptime_seconds = int(
                                (datetime.now() - bridge.started_at).total_seconds()
                            )
                        status = {
                            "running": bridge.running,
                            "events_processed": bridge.event_count,
                            "hooks_dir": str(bridge.hook_manager.hooks_dir),
                            "opencode_server": bridge.base_url,
                            "started_at": bridge.started_at.isoformat()
                            if bridge.started_at
                            else None,
                            "uptime_seconds": uptime_seconds,
                            "last_event_time": bridge.last_event_time,
                        }
                        handler_self.wfile.write(json.dumps(status).encode())
                    else:
                        handler_self.send_response(404)
                        handler_self.end_headers()

                def log_message(self, format, *args):
                    pass

            # Utiliser les ports de configuration
            status_config = self.config.get("status_server", {})
            default_port = status_config.get("default_port", 9998)
            fallback_port = status_config.get("fallback_port", 9999)

            port = default_port
            try:
                server = HTTPServer(("localhost", port), StatusHandler)
            except OSError:
                port = fallback_port
                try:
                    server = HTTPServer(("localhost", port), StatusHandler)
                except OSError:
                    _log_error(
                        f"❌ Cannot start status server on ports {default_port}-{fallback_port}"
                    )
                    return

            logger.info(f"📊 Status server started on http://localhost:{port}/status")

            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()

        except Exception as e:
            _log_error(f"❌ Failed to start status server: {e}")
            # Propagate error - status server is critical for monitoring
            raise RuntimeError(f"Critical: Status server failed to start: {e}")


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print("Usage: python event_bridge.py <command>")
        print("Commands:")
        print("  start   - Start the event bridge")
        print("  status  - Show status")
        sys.exit(1)

    command = sys.argv[1]
    bridge = EventBridge()

    if command == "start":
        if bridge.start():
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n👋 Shutting down event bridge...")
                bridge.running = False

    elif command == "status":
        try:
            response = requests.get("http://localhost:9998/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"Event Bridge Status:")
                print(f"  Running: {status['running']}")
                print(f"  Events processed: {status['events_processed']}")
                print(f"  Hooks directory: {status['hooks_dir']}")
            else:
                print("❌ Event bridge not running")
        except Exception as e:
            print(f"❌ Event bridge not running or not accessible: {e}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime

    main()
