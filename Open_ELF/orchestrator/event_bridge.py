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
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
OPENCODE_SERVER = "http://localhost:4096"
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
HOOKS_DIR = Path.home() / ".opencode" / "hooks"
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "event_bridge.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("EventBridge")


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

                # Exécuter le hook avec les données en stdin
                proc = subprocess.Popen(
                    [sys.executable, str(hook_file)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.elf_dir),
                    env={
                        **dict(subprocess.os.environ),
                        "ELF_BASE_PATH": str(self.elf_dir),
                    },
                )

                stdout, stderr = proc.communicate(input=hook_input.encode(), timeout=30)

                if proc.returncode == 0:
                    logger.info(f"✅ Hook executed: {hook_type}/{hook_file.name}")
                    if stdout:
                        try:
                            result = json.loads(stdout.decode())
                            logger.debug(f"Hook result: {result}")
                        except:
                            pass
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

    def start(self):
        """Démarre le bridge d'événements."""
        logger.info("=" * 70)
        logger.info("🌉 OpenCode Event Bridge Starting")
        logger.info("=" * 70)

        # Vérifier la connexion à OpenCode
        try:
            response = requests.get(f"{self.base_url}/global/health", timeout=5)
            if response.status_code != 200:
                logger.error("❌ OpenCode server not accessible")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to OpenCode: {e}")
            return False

        logger.info("✅ Connected to OpenCode server")
        self.running = True

        # Démarrer l'écoute des events dans un thread
        events_thread = threading.Thread(target=self._listen_events, daemon=True)
        events_thread.start()

        # Démarrer le serveur HTTP pour le status
        self._start_status_server()

        return True

    def _listen_events(self):
        """Écoute le stream SSE des événements OpenCode."""
        logger.info("👂 Listening to OpenCode events...")

        while self.running:
            try:
                # Se connecter au stream SSE
                response = requests.get(
                    f"{self.base_url}/events",
                    stream=True,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=60,
                )

                if response.status_code != 200:
                    logger.error(
                        f"❌ Failed to connect to event stream: {response.status_code}"
                    )
                    time.sleep(5)
                    continue

                logger.info("✅ Connected to SSE stream")

                # Traiter les events ligne par ligne
                for line in response.iter_lines():
                    if not self.running:
                        break

                    if line:
                        line_str = line.decode("utf-8")
                        self._process_sse_line(line_str)

            except requests.exceptions.ChunkedEncodingError:
                logger.warning("⚠️ SSE stream disconnected, reconnecting...")
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ Error listening to events: {e}")
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
                    logger.debug(f"Failed to parse SSE data: {e}")
        elif line.startswith("event:"):
            # Type d'événement (optionnel)
            pass

    def _handle_event(self, event: Dict[str, Any]):
        """Gère un événement reçu d'OpenCode."""
        event_type = event.get("type", "unknown")
        self.event_count += 1

        logger.debug(f"Event #{self.event_count}: {event_type}")

        # Mapper les événements OpenCode aux hooks ELF
        if event_type == "message":
            self._handle_message_event(event)
        elif event_type == "tool":
            self._handle_tool_event(event)
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

    def _start_status_server(self):
        """Démarre un serveur HTTP simple pour exposer le status."""

        class StatusHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self):
                if handler_self.path == "/status":
                    handler_self.send_response(200)
                    handler_self.send_header("Content-type", "application/json")
                    handler_self.end_headers()

                    status = {
                        "running": self.running,
                        "events_processed": self.event_count,
                        "hooks_dir": str(self.hooks_dir),
                        "opencode_server": self.base_url,
                    }
                    handler_self.wfile.write(json.dumps(status).encode())
                else:
                    handler_self.send_response(404)
                    handler_self.end_headers()

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("localhost", 9998), StatusHandler)
        logger.info("📊 Status server started on http://localhost:9998/status")

        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()


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
        except:
            print("❌ Event bridge not running")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime

    main()
