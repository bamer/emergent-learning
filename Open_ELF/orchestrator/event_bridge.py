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
import os
import requests
import sys
import time
import subprocess
import threading
import asyncio
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
# httpx removed - using requests instead

# Configuration
OPENCODE_SERVER = "http://localhost:4096"
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
HOOKS_DIR = ELF_DIR / "hooks"
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
    "ai_analysis": {
        "timeout_seconds": 600,  # 10 minutes for AI processing (covers 5min max)
        "model": "nvidia/minimaxai/minimax-m2",  # Fast testing model
        "session_title": "ELF AI Analysis Session",
    },
}

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class OpenCodeAIClient:
    """Client pour interagir avec OpenCode via HTTP (synchronous)."""

    def __init__(
        self, base_url: str, timeout: int = 600
    ):  # 10 minute timeout for slow models
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.ai_session_id: Optional[str] = None

    def ensure_ai_session(self) -> str:
        """S'assurer qu'une session AI existe et retourner son ID."""
        if self.ai_session_id:
            return self.ai_session_id

        try:
            # Reuse existing AI session to avoid memory issues
            response = requests.get(f"{self.base_url}/session", timeout=self.timeout)
            if response.status_code == 200:
                sessions = response.json()
                # Look for sessions that match our patterns
                for session in sessions:
                    title = session.get("title", "")
                    slug = session.get("slug", "")
                    # Match various patterns for ELF AI sessions
                    if (
                        "AI Analysis" in title
                        or "elf" in slug.lower()
                        or "nvidia" in title.lower()
                        or "minimax" in title.lower()
                    ):
                        self.ai_session_id = session.get("id")
                        if self.ai_session_id:
                            _log_info(
                                f"✅ Reusing existing AI session: {self.ai_session_id[:8]}..."
                            )
                            return self.ai_session_id

            # Créer une nouvelle session AI
            config = DEFAULT_CONFIG.get("ai_analysis", {})
            session_title = config.get(
                "session_title", "ELF AI Analysis Session - nvidia/minimaxai/minimax-m2"
            )

            response = requests.post(
                f"{self.base_url}/session",
                json={
                    "title": session_title,
                    "directory": str(ELF_DIR),
                },
                timeout=self.timeout,
            )

            if response.status_code in [200, 201]:
                session_data = response.json()
                self.ai_session_id = session_data.get("id")
                if self.ai_session_id:
                    _log_info(f"✅ Created new AI session: {self.ai_session_id[:8]}...")
                    return self.ai_session_id
                else:
                    raise Exception(
                        "Failed to create AI session: No session ID received"
                    )
            else:
                raise Exception(f"Failed to create AI session: {response.status_code}")

        except Exception as e:
            _log_error(f"❌ Error managing AI session: {e}")
            raise

    def send_analysis_request(
        self, prompt: str, component: str = "unknown"
    ) -> Dict[str, Any]:
        """Envoyer une requête d'analyse à l'agent AI via OpenCode."""
        try:
            session_id = self.ensure_ai_session()
            config = DEFAULT_CONFIG.get("ai_analysis", {})
            model = config.get("model", "opencode/big-pickle")

            _log_info(
                f"🤖 Sending AI analysis request from {component} (session: {session_id[:8]}...)"
            )

            # Préparer le message avec contexte du composant
            enhanced_prompt = f"""ELF System Analysis Request from {component.upper()} Agent

{prompt}

You are analyzing system state as the {component} agent. Provide agent-specific insights and recommendations. Be concise but informative."""

            # Test with nvidia/minimaxai/minimax-m2 (fast + free for testing)
            available_models = [
                {
                    "providerID": "nvidia",
                    "modelID": "minimaxai/minimax-m2",
                },  # Fast testing model
            ]

            # Try models in order of preference
            last_error = None
            for model_config in available_models:
                try:
                    response = requests.post(
                        f"{self.base_url}/session/{session_id}/message",
                        json={
                            "parts": [{"type": "text", "text": enhanced_prompt}],
                            "model": model_config,
                        },
                        timeout=self.timeout,
                    )

                    if response.status_code == 200:
                        # Success with this model
                        result = response.json()
                        message_info = result.get("info", {})
                        parts = result.get("parts", [])

                        # Extraire la réponse de l'assistant - look for text parts with actual content
                        text_parts = [
                            p
                            for p in parts
                            if p.get("type") == "text" and p.get("text")
                        ]
                        # Extract just the assistant response content
                        ai_response = "".join(
                            part.get("text", "") for part in text_parts
                        )

                        if ai_response.strip():
                            _log_info(
                                f"✅ AI analysis completed successfully with {model_config['providerID']}/{model_config['modelID']}"
                            )
                            return {
                                "success": True,
                                "response": ai_response.strip(),
                                "session_id": session_id,
                                "message_id": message_info.get("id"),
                                "model_used": model_config,
                                "timestamp": datetime.now().isoformat(),
                            }
                    else:
                        last_error = f"Model {model_config['providerID']}/{model_config['modelID']} failed: {response.status_code}"
                        continue  # Try next model
                except Exception as e:
                    last_error = f"Model {model_config['providerID']}/{model_config['modelID']} error: {str(e)}"
                    continue  # Try next model

            # If we get here, all models failed
            raise Exception(f"All AI models failed. Last error: {last_error}")

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"AI analysis timeout after {self.timeout} seconds",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"AI analysis failed: {str(e)}",
            }


# Setup logging (unified + local)
sys.path.insert(0, str(ELF_DIR / "agents"))
sys.path.insert(0, str(ELF_DIR / "Open_ELF" / "utils"))
try:
    from agents.elf_logging import get_logger, log_info, log_error

    logger = get_logger("event_bridge")

    def _log_info(message: str):
        log_info("event_bridge", message)

    def _log_error(message: str):
        log_error("event_bridge", message)

except Exception:
    logging.basicConfig(
        level=logging.INFO,
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


# Add Open_ELF to Python path for imports
OPEN_ELF_DIR = Path(__file__).parent.parent
if str(OPEN_ELF_DIR) not in sys.path:
    sys.path.insert(0, str(OPEN_ELF_DIR))

# Import event_logger for database logging (NEW)
EVENT_LOGGER_AVAILABLE = False
EVENT_LOGGER = None
try:
    from utils.event_logger import log_event

    EVENT_LOGGER_AVAILABLE = True
    EVENT_LOGGER = log_event
    _log_info("Event logger imported for database logging")
except ImportError as e:
    logger.warning(
        f"Event logger not available, events will not be logged to database: {e}"
    )


class HookManager:
    """Gère l'exécution des hooks ELF."""

    def __init__(self):
        self.hooks_dir = HOOKS_DIR
        self.elf_dir = ELF_DIR
        self.session_state = {}

    def run_hook(self, hook_type: str, event_data: Dict[str, Any]) -> bool:
        """Exécute tous les hooks d'un type donné."""
        hook_dir = self.hooks_dir / hook_type

        # Try exact match first (e.g., PostToolUse)
        hook_files = []
        if hook_dir.exists():
            hook_files = list(hook_dir.glob("*.py"))

        # If exact match is empty, try lowercase variant (e.g., posttooluse)
        if not hook_files:
            hook_dir = self.hooks_dir / hook_type.lower()
            if hook_dir.exists():
                hook_files = list(hook_dir.glob("*.py"))

        # If still empty, try snake_case variant (e.g., post_tool_use)
        if not hook_files:
            import re

            snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", hook_type).lower()
            hook_dir = self.hooks_dir / snake_case
            if hook_dir.exists():
                hook_files = list(hook_dir.glob("*.py"))

        if not hook_files:
            return False

        success = False
        for hook_file in hook_files:
            proc = None
            try:
                # Préparer les données pour le hook
                hook_input = json.dumps(event_data)

                # Préparer l'environnement avec le chemin ELF
                hook_env = dict(os.environ)
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
                    _log_info(f"✅ Hook executed: {hook_type}/{hook_file.name}")
                    if stdout:
                        try:
                            result = json.loads(stdout.decode())
                            _log_info(f"Hook result: {result}")
                        except Exception as e:
                            _log_error(
                                f"Failed to parse hook result from {hook_file.name}: {e}"
                            )
                            # Continue with other hooks but log the error
                    success = True
                else:
                    _log_error(
                        f"⚠️ Hook failed: {hook_type}/{hook_file.name} (exit {proc.returncode})"
                    )
                    if stderr:
                        _log_error(f"Hook stderr: {stderr.decode()[:200]}")

            except subprocess.TimeoutExpired:
                _log_error(f"⏱️ Hook timeout: {hook_type}/{hook_file.name}")
                if proc is not None:
                    proc.kill()
            except Exception as e:
                _log_error(f"❌ Hook error: {hook_type}/{hook_file.name}: {e}")
                if proc is not None:
                    proc.kill()

        return success


class EventBridge:
    """Pont entre les events OpenCode et les hooks ELF."""

    def __init__(self):
        self.running = False
        self.base_url = OPENCODE_SERVER
        self.hook_manager = HookManager()
        self.event_count = 0
        self.hooks_executed = 0
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

        # Event listener system for components like UnifiedOrchestrator
        self._listeners = []  # List of registered listeners: [{id, callback, event_types}]

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

    def register_listener(
        self, listener_id: str, callback: Callable[..., Any], event_types: List[str]
    ):
        """Register a listener for specific event types.

        Args:
            listener_id: Unique identifier for this listener
            callback: Function to call when event is received (callback(event_data))
            event_types: List of event types to listen for
        """
        listener = {"id": listener_id, "callback": callback, "event_types": event_types}
        self._listeners.append(listener)
        logger.info(f"🎧 Listener registered: {listener_id} for events: {event_types}")

    def _notify_listeners(self, event_type: str, event_data: Dict[str, Any]):
        """Notify all registered listeners for a specific event type."""
        for listener in self._listeners:
            if event_type in listener.get("event_types", []):
                try:
                    listener["callback"](event_data)
                    logger.debug(
                        f"📨 Notified listener {listener['id']} for event {event_type}"
                    )
                except Exception as e:
                    logger.error(f"❌ Error notifying listener {listener['id']}: {e}")

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

            # Log event to database if available and logger is callable
            if EVENT_LOGGER_AVAILABLE and callable(EVENT_LOGGER):
                try:
                    # Extract severity from event type for classification
                    severity = "info"
                    if "error" in event_type.lower() or "failure" in event_type.lower():
                        severity = "error"
                    elif "warning" in event_type.lower():
                        severity = "warning"
                    elif "critical" in event_type.lower():
                        severity = "critical"

                    # Build summary from log_message
                    summary = log_message.replace("📡", "").strip()
                    if details:
                        summary = f"{summary} - {details[:50]}..."

                    # Create structured data payload
                    event_data = {
                        "event_type": event_type,
                        "source": "event_bridge",
                        "component": "opencodess",
                        "details": details,
                        "severity": severity,
                        "session_id": getattr(self, "opencode_session_id", None),
                        "timestamp": self.last_event_time,
                    }

                    # Log to database
                    EVENT_LOGGER(
                        event_type=event_type,
                        source="event_bridge",
                        summary=summary,
                        data=event_data,
                        status="success",
                    )
                except Exception as e:
                    logger.warning(f"Failed to log event to database: {e}")
            elif not callable(EVENT_LOGGER):
                logger.warning(
                    "Event logger is not callable, skipping database logging"
                )

    def start(self):
        """Démarre le bridge d'événements."""
        _log_info("=" * 70)
        _log_info("🌉 OpenCode Event Bridge Starting")
        _log_info("=" * 70)

        # Vérifier la connexion à OpenCode
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                _log_error("❌ OpenCode server not accessible")
                return False
        except Exception as e:
            _log_error(f"❌ Cannot connect to OpenCode: {e}")
            return False

        _log_info("✅ Connected to OpenCode server")

        # Initialize OpenCode session for EventBridge
        self._initialize_session()

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

    def _initialize_session(self):
        """Initialize or retrieve OpenCode session for EventBridge."""
        try:
            # First, try to find an existing ELF session
            response = requests.get(f"{self.base_url}/session", timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                # Look for an existing ELF EventBridge session
                for session in sessions:
                    if "EventBridge" in session.get(
                        "title", ""
                    ) or "event_bridge" in session.get("slug", ""):
                        self.opencode_session_id = session.get("id")
                        _log_info(
                            f"✅ Found existing EventBridge session: {self.opencode_session_id[:8]}..."
                        )
                        return

            # If no existing session, create a new one
            _log_info("🆕 Creating new EventBridge session...")
            create_response = requests.post(
                f"{self.base_url}/session",
                json={
                    "title": "ELF EventBridge Session",
                    "directory": str(ELF_DIR),
                },
                timeout=10,
            )

            if create_response.status_code in [200, 201]:
                session_data = create_response.json()
                self.opencode_session_id = session_data.get("id")
                _log_info(
                    f"✅ Created EventBridge session: {self.opencode_session_id[:8]}..."
                )
            else:
                _log_error(
                    f"❌ Failed to create session: {create_response.status_code}"
                )
                self.opencode_session_id = None

        except Exception as e:
            _log_error(f"❌ Error initializing session: {e}")
            self.opencode_session_id = None

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

                total_tools_found = 0

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
                            # Vérifier quand même si des parties ont été ajoutées
                            # en comparant le nombre de parties
                            pass

                        seen_messages[session_id].add(msg_id)

                        # Vérifier si c'est un message avec des outils
                        parts = msg.get("parts", [])
                        for part in parts:
                            # Check for both "tool_use" and "tool" part types
                            part_type = part.get("type")
                            if part_type in ["tool_use", "tool"]:
                                tool_name = part.get("tool", "unknown")
                                tool_input = part.get("input", {})
                                total_tools_found += 1

                                _log_info(
                                    f"🔧 Tool detected via polling: {tool_name} ({part_type}) in session {session_id[:8]}"
                                )

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

                if total_tools_found > 0:
                    _log_info(
                        f"✅ Poll complete: {total_tools_found} tools found across {len(sessions)} sessions"
                    )

                # Attendre avant le prochain poll (5s pour capturer plus d'outils)
                time.sleep(5)

            except Exception as e:
                _log_error(f"❌ Error polling sessions: {e}")
                time.sleep(5)

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

        # NEW: Handle tool usage embedded in message.part.updated events
        if event_type == "message.part.updated":
            part = event_properties.get("part", {})
            part_type = part.get("type")
            # Check for both "tool_use" and "tool" part types
            if part_type in ["tool_use", "tool"]:
                # Synthesize a tool event for processing
                tool_event = {
                    "type": "tool",
                    "properties": {
                        "tool": part.get("tool", "unknown"),
                        "input": part.get("input", {}),
                        "output": {},  # Will be populated later
                        "session_id": event_properties.get("session_id", ""),
                        "success": True,
                    },
                }
                # Process as a regular tool event
                self._handle_event(tool_event)
                return  # Already processed

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
        elif event_type == "server.heartbeat":
            uptime = event_properties.get("uptime", "unknown")
            active_sessions = event_properties.get("active_sessions", "unknown")
            details = f"Heartbeat | Uptime: {uptime} | Sessions: {active_sessions}"
        elif event_type == "session.created":
            session_id = event_properties.get("id", "")
            details = f"Session created: {session_id[:8]}..."
        elif event_type == "session.updated":
            session_id = event_properties.get("id", "")
            status = event_properties.get("status", "")
            details = f"Session updated: {session_id[:8]}... | Status: {status}"
        elif event_type == "failure":
            failure_type = event_properties.get("failure_type", "unknown")
            details = f"Failure: {failure_type}"
        else:
            # Generic details for unknown event types - extract some useful info
            keys = list(event_properties.keys())
            if keys:
                details = f"Properties: {', '.join(keys[:5])}"
            else:
                details = "No properties"

        # Log event to database with details
        self._record_event(event_type, details)

        # Notify registered listeners (e.g., UnifiedOrchestrator)
        self._notify_listeners(event_type, event)

        logger.info(f"📡 Processing event #{self.event_count}: {event_type}")

        # Handle tool usage embedded in message.part.updated events
        if event_type == "message.part.updated":
            part = event_properties.get("part", {})
            if part.get("type") == "tool_use":
                # Synthesize a tool event for processing
                tool_event = {
                    "type": "tool",
                    "properties": {
                        "tool": part.get("tool", "unknown"),
                        "input": part.get("input", {}),
                        "output": {},  # Will be populated later
                        "session_id": event_properties.get("session_id", ""),
                        "success": True,
                    },
                }
                # Process as a regular tool event
                self._handle_event(tool_event)
                return  # Already processed

        # Notify registered listeners (e.g., UnifiedOrchestrator)
        self._notify_listeners(event_type, event)

        logger.debug(f"📡 Processing event #{self.event_count}: {event_type}")

        # Mapper les événements OpenCode aux hooks ELF
        if event_type == "message":
            self._handle_message_event(event)
        elif event_type == "message.updated":
            self._handle_message_updated_event(event)
        elif event_type == "message.part.updated":
            self._handle_message_part_updated_event(event)
        elif event_type == "tool":
            self._handle_tool_event(event)
        elif event_type == "error":
            self._handle_error_event(event)
        elif event_type == "failure":
            self._handle_failure_event(event)
        elif event_type == "session.created":
            self._handle_session_created(event)
        elif event_type == "session.updated":
            self._handle_session_updated_event(event)
        elif event_type == "session.status":
            self._handle_session_status_event(event)
        elif event_type == "session.idle":
            self._handle_session_idle_event(event)
        elif event_type == "session.diff":
            self._handle_session_diff_event(event)
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

        # Hook PreSession (équivalent à UserPromptSubmit avant toute session)
        pre_session_data = {
            "event_type": "UserPromptSubmit",
            "session_id": session_id,
            "session_status": "created",
            "timestamp": datetime.now().isoformat(),
        }
        self.hook_manager.run_hook("UserPromptSubmit", pre_session_data)

    def _handle_message_updated_event(self, event: Dict[str, Any]):
        """Gère un event de message (final message envoyé)."""
        props = event.get("properties", {})
        role = props.get("role", "unknown")
        content = props.get("content", "")
        session_id = props.get("session_id")

        if role == "user":
            logger.info(f"👤 User message submitted")

            # Hook UserPromptSubmit (pre_session compact)
            hook_data = {
                "event_type": "UserPromptSubmit",
                "session_id": session_id,
                "message": content,
                "timestamp": datetime.now().isoformat(),
            }
            self.hook_manager.run_hook("UserPromptSubmit", hook_data)

        elif role == "assistant":
            logger.info(f"🤖 Assistant message sent")

            # Hook MessageSendCompleted
            hook_data = {
                "event_type": "MessageSendCompleted",
                "session_id": session_id,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
            self.hook_manager.run_hook("MessageSendCompleted", hook_data)

    def _handle_message_part_updated_event(self, event: Dict[str, Any]):
        """Gère les parties de message mises à jour (progressive)."""
        props = event.get("properties", {})
        part = props.get("part", {})
        part_type = part.get("type", "")
        session_id = props.get("session_id", "")

        logger.debug(
            f"📝 Message part updated: {part_type} | Session: {session_id[:8]}..."
        )

        if part_type == "tool_use":
            # Already handled via tool_event synthesis earlier
            pass
        elif part_type == "text":
            text_content = part.get("text", "")
            logger.debug(f"Text part: {len(text_content)} chars")
            # Could trigger hooks here if needed for streaming text
        elif part_type == "thinking":
            thoughts = part.get("thinking", "")
            logger.debug(f"Thinking part: {len(thoughts)} chars")

    def _handle_session_updated_event(self, event: Dict[str, Any]):
        """Gère les mises à jour de session (post_session)."""
        props = event.get("properties", {})
        session_id = props.get("id")
        status = props.get("status", "unknown")

        logger.info(f"📁 Session updated: {session_id} -> {status}")

        # Si session terminée/fermée, déclencher hook post-session
        if status.lower() in ["closed", "completed", "finished", "ended", "archived"]:
            logger.info(f"🏁 Session ended: {session_id}")

            # Hook SessionEnded
            hook_data = {
                "event_type": "SessionEnded",
                "session_id": session_id,
                "final_status": status,
                "timestamp": datetime.now().isoformat(),
            }
            self.hook_manager.run_hook("SessionEnded", hook_data)

            # Cleanup session tracking
            if session_id in self.session_tools:
                tools_used = self.session_tools[session_id].get("tools_used", [])
                logger.info(f"📊 Session {session_id} used {len(tools_used)} tools")
                del self.session_tools[session_id]

    def _handle_session_status_event(self, event: Dict[str, Any]):
        """Gère les événements de statut de session."""
        props = event.get("properties", {})
        session_id = props.get("id")
        status = props.get("status", "unknown")

        logger.debug(f"📋 Session status: {session_id} -> {status}")

    def _handle_session_idle_event(self, event: Dict[str, Any]):
        """Gère les événements de session idle."""
        props = event.get("properties", {})
        session_id = props.get("id")
        idle_duration = props.get("idle_duration", "unknown")

        logger.info(f"⏸️  Session idle: {session_id} for {idle_duration}")

        # Hook pour session idle
        hook_data = {
            "event_type": "SessionIdle",
            "session_id": session_id,
            "idle_duration": idle_duration,
            "timestamp": datetime.now().isoformat(),
        }
        self.hook_manager.run_hook("SessionIdle", hook_data)

    def _handle_session_diff_event(self, event: Dict[str, Any]):
        """Gère les événements de diff de session (changements)."""
        props = event.get("properties", {})
        session_id = props.get("id")
        diff_data = props.get("diff", "unknown")

        logger.debug(f"📝 Session diff: {session_id}")

        # Hook pour tracking des changements
        hook_data = {
            "event_type": "SessionDiff",
            "session_id": session_id,
            "diff": diff_data,
            "timestamp": datetime.now().isoformat(),
        }
        self.hook_manager.run_hook("SessionDiff", hook_data)

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
                def do_GET(self):
                    if self.path == "/status":
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()

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
                            "opencode_session_id": getattr(
                                bridge, "opencode_session_id", None
                            ),
                            "started_at": bridge.started_at.isoformat()
                            if bridge.started_at
                            else None,
                            "uptime_seconds": uptime_seconds,
                            "last_event_time": bridge.last_event_time,
                        }
                        self.wfile.write(json.dumps(status).encode())
                    elif self.path == "/api/v1/health/mission_bridge":
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        health = {
                            "status": "healthy",
                            "service": "mission_bridge",
                            "running": bridge.running,
                            "hooks_executed": bridge.hooks_executed,
                            "last_heartbeat": datetime.now().isoformat(),
                        }
                        self.wfile.write(json.dumps(health).encode())
                    elif self.path == "/api/v1/health/sentinel_monitor":
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        health = {
                            "status": "healthy",
                            "service": "sentinel_monitor",
                            "running": bridge.running,
                            "events_monitored": bridge.event_count,
                            "last_check": bridge.last_event_time
                            or datetime.now().isoformat(),
                        }
                        self.wfile.write(json.dumps(health).encode())
                    else:
                        self.send_response(404)
                        self.end_headers()

                def do_POST(self):
                    """Handle POST requests for API endpoints."""
                    try:
                        if self.path == "/api/v1/ask":
                            # Parse the request data
                            content_length = int(self.headers.get("Content-Length", 0))
                            request_data = {}
                            if content_length > 0:
                                try:
                                    post_data = self.rfile.read(content_length)
                                    request_data = json.loads(post_data.decode("utf-8"))
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    # If we can't parse the request, use empty dict
                                    pass

                            # Check if this is a watcher request that needs special handling
                            component = request_data.get("component", "")
                            request_type = request_data.get("request_type", "")
                            data = request_data.get("data", {})

                            self.send_response(200)
                            self.send_header("Content-type", "application/json")
                            self.end_headers()

                            # Handle AI analysis requests by actually calling OpenCode
                            if (
                                component == "elf_watcher"
                                and request_type == "system_analysis"
                            ):
                                # Generate prompt based on system state
                                system_state = data.get("system_state", {})
                                analysis_type = data.get("analysis_type", "generic")

                                prompt = bridge._generate_analysis_prompt(
                                    system_state, analysis_type
                                )

                                # Call OpenCode for actual AI analysis (async)
                                _log_info(
                                    f"🤖 Starting AI analysis for {component} via OpenCode (nvidia/minimaxai/minimax-m2 - fast testing)..."
                                )
                                try:
                                    # Run async analysis in thread pool to avoid blocking
                                    with (
                                        concurrent.futures.ThreadPoolExecutor()
                                    ) as executor:
                                        future = executor.submit(
                                            bridge._ask_opencode, prompt, component
                                        )
                                        opencode_result = future.result(
                                            timeout=600  # 10 minutes to allow for slow AI responses
                                        )
                                except concurrent.futures.TimeoutError:
                                    _log_error(
                                        "⏰ AI analysis timed out after 10 minutes (expected max: 5 minutes)"
                                    )
                                    opencode_result = {
                                        "success": False,
                                        "error": "AI analysis timed out after 10 minutes (expected max: 5 minutes)",
                                    }
                                except Exception as e:
                                    _log_error(f"❌ AI analysis thread failed: {e}")
                                    opencode_result = {
                                        "success": False,
                                        "error": f"AI analysis thread failed: {str(e)}",
                                    }

                                if opencode_result["success"]:
                                    response = {
                                        "response_type": "coordination_result",
                                        "data": {
                                            "ai_analysis": opencode_result["response"],
                                            "session_id": opencode_result.get(
                                                "session_id"
                                            ),
                                            "timestamp": datetime.now().isoformat(),
                                            "status": "completed",
                                            "processing_time": "async_completed",
                                        },
                                        "timestamp": datetime.now().isoformat(),
                                        "priority": request_data.get("priority", 2),
                                    }
                                else:
                                    # Fallback response if OpenCode fails
                                    response = {
                                        "response_type": "coordination_result",
                                        "data": {
                                            "ai_analysis": f"Analysis temporarily unavailable: {opencode_result['error']}",
                                            "timestamp": datetime.now().isoformat(),
                                            "status": "error",
                                            "error_details": opencode_result.get(
                                                "error"
                                            ),
                                        },
                                        "timestamp": datetime.now().isoformat(),
                                        "priority": request_data.get("priority", 2),
                                    }
                            elif (
                                component == "elf_watcher"
                                and request_type == "watcher_analysis"
                            ):
                                # Provide more detailed watcher analysis
                                system_state = data.get("system_state", {})
                                prompt = f"""ELF Watcher Analysis Request

WATCHER STATUS: {system_state.get("status", "unknown")}
LAST CHECK: {system_state.get("last_check_time", "unknown")}
SERVICES MONITORED: {len(system_state.get("services", {}))}
ERROR COUNT: {system_state.get("error_count", 0)}

Provide a concise analysis of watcher performance and recommend optimizations."""
                                try:
                                    opencode_result = bridge._ask_opencode(
                                        prompt, component
                                    )
                                    if opencode_result["success"]:
                                        response = {
                                            "response_type": "coordination_result",
                                            "data": {
                                                "ai_analysis": opencode_result[
                                                    "response"
                                                ],
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "completed",
                                                "analysis_type": "watcher_specific",
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                    else:
                                        response = {
                                            "response_type": "coordination_result",
                                            "data": {
                                                "ai_analysis": f"Watcher analysis via OpenCode failed: {opencode_result['error']}",
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "fallback",
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                except Exception as e:
                                    response = {
                                        "response_type": "coordination_result",
                                        "data": {
                                            "ai_analysis": f"Watcher analysis error: {str(e)}",
                                            "timestamp": datetime.now().isoformat(),
                                            "status": "error",
                                        },
                                        "timestamp": datetime.now().isoformat(),
                                        "priority": request_data.get("priority", 2),
                                    }
                            elif component == "unified_orchestrator":
                                # Handle orchestrator requests
                                prompt = f"""ELF Unified Orchestrator Analysis Request

REQUEST TYPE: {request_type}
COMPONENT: {component}
DATA: {str(data)[:200]}...

Provide operational insights for orchestrator optimization."""
                                try:
                                    opencode_result = bridge._ask_opencode(
                                        prompt, component
                                    )
                                    if opencode_result["success"]:
                                        response = {
                                            "component": "event_bridge",
                                            "request_type": request_type,
                                            "data": {
                                                "ai_analysis": opencode_result[
                                                    "response"
                                                ],
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "completed",
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                    else:
                                        response = {
                                            "component": "event_bridge",
                                            "request_type": request_type,
                                            "data": {
                                                "analysis": f"Orchestrator analysis failed: {opencode_result['error']}",
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "error",
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                except Exception as e:
                                    response = {
                                        "component": "event_bridge",
                                        "request_type": request_type,
                                        "data": {
                                            "analysis": f"Orchestrator request error: {str(e)}",
                                            "timestamp": datetime.now().isoformat(),
                                            "status": "error",
                                        },
                                        "timestamp": datetime.now().isoformat(),
                                        "priority": request_data.get("priority", 2),
                                    }
                            else:
                                # Default response for other components with AI enhancement
                                prompt = f"""ELF System Component Analysis

COMPONENT: {component}
REQUEST TYPE: {request_type}
DATA: {str(data)[:300]}...

Provide insights about this component request and system integration."""
                                try:
                                    opencode_result = bridge._ask_opencode(
                                        prompt, component
                                    )
                                    if opencode_result["success"]:
                                        response = {
                                            "component": "event_bridge",
                                            "request_type": request_type
                                            or "generic_request",
                                            "data": {
                                                "analysis": opencode_result["response"],
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "completed",
                                                "ai_enhanced": True,
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                    else:
                                        response = {
                                            "component": "event_bridge",
                                            "request_type": request_type
                                            or "generic_request",
                                            "data": {
                                                "analysis": f"Request processed via Event Bridge with OpenCode integration (AI unavailable: {opencode_result['error'][:50]}...)",
                                                "timestamp": datetime.now().isoformat(),
                                                "status": "completed_fallback",
                                            },
                                            "timestamp": datetime.now().isoformat(),
                                            "priority": request_data.get("priority", 2),
                                        }
                                except Exception as e:
                                    response = {
                                        "component": "event_bridge",
                                        "request_type": request_type
                                        or "generic_request",
                                        "data": {
                                            "analysis": "Request processed via Event Bridge (AI processing failed)",
                                            "timestamp": datetime.now().isoformat(),
                                            "status": "completed",
                                            "error": str(e)[:100],
                                        },
                                        "timestamp": datetime.now().isoformat(),
                                        "priority": request_data.get("priority", 2),
                                    }
                            self.wfile.write(json.dumps(response).encode())
                        else:
                            self.send_response(404)
                            self.end_headers()
                    except Exception as e:
                        # Log error but don't crash the server
                        _log_error(f"Error in POST handler: {e}")
                        try:
                            self.send_response(500)
                            self.send_header("Content-type", "application/json")
                            self.end_headers()
                            error_response = {
                                "error": "Internal server error",
                                "message": str(e),
                            }
                            self.wfile.write(json.dumps(error_response).encode())
                        except:
                            # If we can't even send an error response, just close
                            pass

            # Start the HTTP server
            default_port = self.config.get("status_server", {}).get(
                "default_port", 9998
            )
            fallback_port = self.config.get("status_server", {}).get(
                "fallback_port", 9999
            )

            # Try default port first
            try:
                server_address = ("", default_port)
                httpd = HTTPServer(server_address, StatusHandler)
                _log_info(f"✅ Status server starting on port {default_port}")
            except OSError:
                # Fallback to secondary port if default is in use
                server_address = ("", fallback_port)
                httpd = HTTPServer(server_address, StatusHandler)
                _log_info(f"✅ Status server starting on fallback port {fallback_port}")

            # Start server in daemon thread
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            self.status_server_running = True

        except Exception as e:
            _log_error(f"❌ Failed to start status server: {e}")
            # Propagate error - status server is critical for monitoring
            raise RuntimeError(f"Critical: Status server failed to start: {e}")

    def _ask_opencode(self, prompt: str, component: str = "unknown") -> Dict[str, Any]:
        """Ask OpenCode for AI analysis using synchronous client."""
        config = DEFAULT_CONFIG.get("ai_analysis", {})
        timeout = config.get("timeout_seconds", 300)

        try:
            client = OpenCodeAIClient(self.base_url, timeout=timeout)
            result = client.send_analysis_request(prompt, component)
            return result
        except Exception as e:
            _log_error(f"❌ AI analysis request failed: {e}")
            return {
                "success": False,
                "error": f"AI analysis request failed: {str(e)}",
            }

    def _generate_analysis_prompt(
        self, system_state: Dict[str, Any], analysis_type: str
    ) -> str:
        """Generate prompt for AI analysis based on system state."""
        services_status = system_state.get("services", {})
        services_report = "\n".join(
            [
                f"  - {service}: {'✅ Operational' if healthy else '❌ Down'}"
                for service, healthy in services_status.items()
            ]
        )

        if analysis_type == "watcher_cycle":
            prompt = f"""ELF System Health Analysis Request

SYSTEM STATE:
Timestamp: {system_state.get("timestamp", "Unknown")}
Event Bridge Status: {"✅ Connected" if system_state.get("event_bridge_healthy", False) else "❌ Disconnected"}
Services Status:
{services_report}

ANALYSIS REQUEST:
Provide a concise analysis of the system health status and recommend any necessary actions.
Include:
1. Overall system health assessment
2. Critical issues that need immediate attention
3. Recommended actions to improve system stability
4. Predictive insights about potential future issues

Keep response under 200 words and focus on actionable insights."""
        else:
            prompt = f"""ELF System Analysis Request

SYSTEM STATE:
Timestamp: {system_state.get("timestamp", "Unknown")}
Event Bridge Status: {"✅ Connected" if system_state.get("event_bridge_healthy", False) else "❌ Disconnected"}
Services Status:
{services_report}

PROVIDE A DETAILED ANALYSIS of the system state and recommend appropriate actions.
Focus on operational efficiency and system reliability."""

        return prompt


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


# Singleton accessor for dashboard backend compatibility
_event_bridge_instance = None


def get_event_bridge_singleton():
    """Get singleton instance of EventBridge for dashboard backend compatibility."""
    global _event_bridge_instance
    if _event_bridge_instance is None:
        _event_bridge_instance = EventBridge()
    return _event_bridge_instance
