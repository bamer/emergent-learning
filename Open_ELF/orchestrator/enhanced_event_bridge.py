#!/usr/bin/env python3
"""
Enhanced Event Bridge with Central Orchestrator Integration
==========================================================

This enhanced event bridge serves as the central orchestrator that:
1. Monitors OpenCode events (original event_bridge functionality)
2. Provides API for components to ask for answers
3. Coordinates between all system components
4. Makes intelligent decisions based on system state

The event bridge becomes the central nervous system that everything works with.
"""

import json
import logging
import requests
import sys
import time
import subprocess
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import asdict

# Import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.central_orchestrator import (
    get_central_orchestrator,
    ask_orchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
    initialize_central_orchestrator,
)
from core.openelf_logging import get_logger, setup_logging
from core.config import get_config
from core.database import get_connection, execute_query

# Setup enhanced logging
setup_logging("enhanced_event_bridge", level="INFO")
logger = get_logger("enhanced_event_bridge")

# Configuration
OPENCODE_SERVER = "http://localhost:4096"
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
HOOKS_DIR = Path.home() / ".opencode" / "hooks"
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
COORDINATION_DIR = ELF_DIR / ".coordination"
EVENT_BRIDGE_HEARTBEAT = COORDINATION_DIR / "enhanced-event-bridge-heartbeat.json"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
COORDINATION_DIR.mkdir(parents=True, exist_ok=True)


class EnhancedHookManager:
    """Enhanced hook manager that coordinates with central orchestrator."""

    def __init__(self):
        self.hooks_dir = HOOKS_DIR
        self.elf_dir = ELF_DIR
        self.session_state = {}

    def run_hook(self, hook_type: str, event_data: Dict[str, Any]) -> bool:
        """Execute hooks with orchestrator coordination."""
        hook_dir = self.hooks_dir / hook_type
        if not hook_dir.exists():
            logger.debug(f"Hook directory not found: {hook_dir}")
            return False

        # Find all Python hooks in this directory
        hook_files = list(hook_dir.glob("*.py"))
        if not hook_files:
            logger.debug(f"No hooks found in {hook_dir}")
            return False

        success = False
        for hook_file in hook_files:
            try:
                # Ask orchestrator if we should run this hook
                hook_decision = asyncio.run(
                    ask_orchestrator(
                        component="hook_manager",
                        request_type="decision",
                        data={
                            "hook_type": hook_type,
                            "hook_file": hook_file.name,
                            "event_data": event_data,
                            "options": ["run", "skip", "delay"],
                        },
                    )
                )

                if hook_decision.data.get("decision") == "skip":
                    logger.debug(f"Orchestrator skipped hook: {hook_file.name}")
                    continue

                # Run the hook
                result = subprocess.run(
                    [sys.executable, str(hook_file)],
                    input=json.dumps(event_data).encode(),
                    capture_output=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    logger.info(f"✅ Hook executed: {hook_type}/{hook_file.name}")
                    success = True

                    # Log hook result if verbose
                    if result.stdout:
                        logger.debug(f"Hook result: {result.stdout.decode()[:200]}")
                else:
                    logger.error(
                        f"❌ Hook failed ({hook_type}/{hook_file.name}): "
                        f"exit={result.returncode}, stderr={result.stderr.decode()[:200]}"
                    )

            except subprocess.TimeoutExpired:
                logger.error(f"⏱️ Hook timeout: {hook_type}/{hook_file.name}")
            except Exception as e:
                logger.error(f"❌ Hook error: {hook_type}/{hook_file.name}: {e}")

        return success


class OrchestratorAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for orchestrator API endpoints."""

    def do_GET(self):
        """Handle GET requests for orchestrator status and queries."""
        if self.path == "/status":
            self._handle_status()
        elif self.path.startswith("/api/v1/health/"):
            self._handle_health_check()
        else:
            self._handle_not_found()

    def do_POST(self):
        """Handle POST requests for orchestrator decisions."""
        if self.path == "/api/v1/ask":
            self._handle_ask_request()
        elif self.path == "/api/v1/mission":
            self._handle_mission_submission()
        elif self.path == "/api/v1/sentinel/coordinate":
            self._handle_sentinel_coordination()
        elif self.path == "/api/v1/sentinel/patterns":
            self._handle_sentinel_patterns()
        else:
            self._handle_not_found()

    def _handle_status(self):
        """Return orchestrator status."""
        status = {
            "service": "enhanced_event_bridge",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "events_processed": getattr(self.server, "event_count", 0),
            "version": "1.0.0",
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())

    def _handle_health_check(self):
        """Handle health check requests."""
        component = self.path.split("/")[-1]

        # Use orchestrator to check health
        async def get_health():
            response = await ask_orchestrator(
                component="health_api",
                request_type="health_check",
                data={"component": component},
            )
            return response

        response = asyncio.run(get_health())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        # Sérialisation correcte des objets datetime
        response_dict = asdict(response)
        response_dict["timestamp"] = response_dict["timestamp"].isoformat()
        self.wfile.write(json.dumps(response_dict).encode())

    def _handle_ask_request(self):
        """Handle ask requests to orchestrator."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            request_data = json.loads(post_data.decode())

            # Use orchestrator to answer
            async def get_answer():
                response = await ask_orchestrator(
                    component=request_data.get("component", "api"),
                    request_type=request_data.get("request_type", "decision"),
                    data=request_data.get("data", {}),
                    priority=request_data.get("priority", 1),
                )
                return response

            response = asyncio.run(get_answer())

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Sérialisation correcte des objets datetime
            response_dict = asdict(response)
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()
            self.wfile.write(json.dumps(response_dict).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_mission_submission(self):
        """Handle mission submission requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            mission_data = json.loads(post_data.decode())

            # Use orchestrator to handle mission
            async def submit_mission():
                response = await ask_orchestrator(
                    component="mission_api",
                    request_type="mission_submission",
                    data=mission_data,
                )
                return response

            response = asyncio.run(submit_mission())

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # Sérialisation correcte des objets datetime
            response_dict = asdict(response)
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()
            self.wfile.write(json.dumps(response_dict).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_sentinel_coordination(self):
        """Handle Sentinel monitoring coordination requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            sentinel_data = json.loads(post_data.decode())

            # Use orchestrator to coordinate Sentinel actions
            async def coordinate_sentinel():
                response = await ask_orchestrator(
                    component="sentinel_monitor",
                    request_type="sentinel_coordination",
                    data={
                        "action": "monitoring_cycle",
                        "source": "sentinel_monitor",
                        "timestamp": datetime.now().isoformat(),
                        "data": sentinel_data,
                    },
                )
                return response

            response = asyncio.run(coordinate_sentinel())

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response_dict = asdict(response)
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()
            self.wfile.write(json.dumps(response_dict).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_sentinel_patterns(self):
        """Handle Sentinel pattern coordination requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            pattern_data = json.loads(post_data.decode())

            # Use orchestrator to coordinate patterns
            async def coordinate_patterns():
                response = await ask_orchestrator(
                    component="sentinel_monitor",
                    request_type="pattern_coordination",
                    data={
                        "patterns": pattern_data.get("patterns", []),
                        "metrics": pattern_data.get("metrics", {}),
                        "source": "sentinel_monitor",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return response

            response = asyncio.run(coordinate_patterns())

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response_dict = asdict(response)
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()
            self.wfile.write(json.dumps(response_dict).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_not_found(self):
        """Handle not found requests."""
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def log_message(self, format, *args):
        """Override to use our logger instead of default."""
        logger.info(f"HTTP {format % args}")


class EnhancedEventBridge:
    """Enhanced event bridge with central orchestrator integration."""

    def __init__(self):
        self.base_url = OPENCODE_SERVER
        self.hook_manager = EnhancedHookManager()
        self.running = False
        self.event_count = 0
        self.event_stats = {}
        self.last_event_time = None
        self.last_log_time = {}
        self.started_at = None
        self.status_server_running = False
        self.status_server = None

        # Load configuration
        self.config = self._load_config()
        self.log_throttle_seconds = self.config["logging"]["throttle_seconds"]
        self.important_events = self.config["logging"]["important_events"]
        self.event_summary_interval = self.config["logging"]["summary_interval"]

        # Session tracking
        self.session_tools = {}
        self.seen_messages = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with defaults."""
        default_config = {
            "logging": {
                "throttle_seconds": 5,
                "important_events": ["message", "tool", "error", "session"],
                "summary_interval": 10,
                "max_details_length": 100,
            },
            "status_server": {"default_port": 9998, "fallback_port": 9999},
        }

        # Try to load from config
        config_path = (
            ELF_DIR / "Open_ELF" / "orchestrator" / "enhanced_event_bridge_config.json"
        )

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    return self._merge_configs(default_config, loaded_config)
            except Exception as e:
                logger.warning(f"⚠️ Error loading config, using defaults: {e}")
        else:
            # Create default config
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"✅ Default configuration created at {config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not create config file: {e}")

        return default_config

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge loaded config with defaults."""
        result = default.copy()

        def merge_dicts(d1, d2):
            for k, v in d2.items():
                if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                    merge_dicts(d1[k], v)
                else:
                    d1[k] = v

        merge_dicts(result, loaded)
        return result

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

    def start_status_server(self):
        """Start the orchestrator API server."""
        port = self.config["status_server"]["default_port"]

        try:
            self.status_server = HTTPServer(("localhost", port), OrchestratorAPIHandler)
            self.status_server.event_count = self.event_count  # Share event count

            def run_server():
                logger.info(f"🌐 Orchestrator API server starting on port {port}")
                self.status_server_running = True
                self.status_server.serve_forever()

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            logger.info(
                f"✅ Orchestrator API server started on http://localhost:{port}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to start orchestrator API server: {e}")
            self.status_server_running = False

    async def start(self):
        """Start the enhanced event bridge with orchestrator integration."""
        logger.info("=" * 70)
        logger.info("🌉 Enhanced Event Bridge with Orchestrator Starting")
        logger.info("=" * 70)

        # Initialize central orchestrator
        await initialize_central_orchestrator()

        # Check OpenCode connection
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                logger.error("❌ Cannot connect to OpenCode")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to OpenCode: {e}")
            return False

        logger.info("✅ Connected to OpenCode server")
        self.started_at = datetime.now()
        self.running = True

        # Start orchestrator API server
        self.start_status_server()

        # Start event listeners
        listeners = [
            threading.Thread(target=self._listen_sse_events, daemon=True),
            threading.Thread(target=self._poll_sessions, daemon=True),
        ]

        for listener in listeners:
            listener.start()

        logger.info("👂 Enhanced event listeners started")
        logger.info("🚀 Enhanced Event Bridge is now the central orchestrator")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down Enhanced Event Bridge...")
            self.running = False

        return True

    def _listen_sse_events(self):
        """Listen to OpenCode SSE events."""
        logger.info("👂 Listening to OpenCode SSE events...")

        while self.running:
            try:
                # Connect to SSE stream
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
                    logger.error(
                        f"❌ Failed to connect to event stream: {response.status_code}"
                    )
                    time.sleep(5)
                    continue

                logger.info("✅ Connected to SSE stream")

                # Process SSE events
                for line in response.iter_lines(decode_unicode=True):
                    if not self.running:
                        break

                    if line:
                        self._process_sse_line(line)

            except Exception as e:
                logger.error(f"❌ Error listening to events: {e}")
                time.sleep(5)

    def _poll_sessions(self):
        """Poll sessions for tool usage (backup method)."""
        logger.info("🔍 Starting session polling...")

        seen_messages = {}

        while self.running:
            try:
                # Get active sessions
                sessions_response = requests.get(
                    f"{self.base_url}/sessions", timeout=10
                )
                if sessions_response.status_code != 200:
                    time.sleep(30)
                    continue

                sessions = sessions_response.json()

                for session in sessions:
                    session_id = session.get("id")
                    if not session_id:
                        continue

                    # Get messages for this session
                    msg_response = requests.get(
                        f"{self.base_url}/sessions/{session_id}/messages", timeout=10
                    )

                    if msg_response.status_code != 200:
                        continue

                    messages = msg_response.json()

                    # Initialize tracker for this session
                    if session_id not in seen_messages:
                        seen_messages[session_id] = set()

                    # Process new messages
                    for msg in messages:
                        msg_id = msg.get("info", {}).get("id")
                        if not msg_id or msg_id in seen_messages[session_id]:
                            continue

                        seen_messages[session_id].add(msg_id)

                        # Check if it's a message with tools
                        parts = msg.get("parts", [])
                        for part in parts:
                            if part.get("type") == "tool_use":
                                tool_name = part.get("tool", "unknown")
                                tool_input = part.get("input", {})

                                logger.info(
                                    f"🔧 Tool detected via polling: {tool_name}"
                                )

                                # Trigger hook
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

                # Wait before next poll
                time.sleep(30)

            except Exception as e:
                logger.error(f"❌ Error polling sessions: {e}")
                time.sleep(30)

    def _process_sse_line(self, line: str):
        """Process an SSE line."""
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str:
                try:
                    data = json.loads(data_str)
                    self._handle_event(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse SSE data: {e}")

    def _handle_event(self, event: Dict[str, Any]):
        """Handle an event from OpenCode."""
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

        # Map OpenCode events to ELF hooks
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

    def _record_event(self, event_type: str = "unknown", details: str = ""):
        """Record an event and update heartbeat."""
        self.event_count += 1
        self.last_event_time = datetime.now().isoformat()

        # Track event statistics
        self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1

        # Update heartbeat
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
                logger.error(f"❌ {log_message}")
            elif is_important:
                logger.info(f"🔍 {log_message}")
            else:
                logger.debug(log_message)

            self.last_log_time[event_type] = current_time

    def _handle_message_event(self, event: Dict[str, Any]):
        """Handle message events."""
        props = event.get("properties", {})
        role = props.get("role", "unknown")
        content = props.get("content", "")
        session_id = props.get("session_id")

        if role == "user":
            logger.info(f"👤 User message detected")

            # Equivalent to UserPromptSubmit hook
            hook_data = {
                "event_type": "UserPromptSubmit",
                "session_id": session_id,
                "message": content,
                "timestamp": datetime.now().isoformat(),
            }

            self.hook_manager.run_hook("UserPromptSubmit", hook_data)

            # Prepare context for PostToolUse
            if session_id:
                self.session_tools[session_id] = {
                    "user_message": content,
                    "tools_used": [],
                    "start_time": time.time(),
                }

    def _handle_tool_event(self, event: Dict[str, Any]):
        """Handle tool events."""
        props = event.get("properties", {})
        tool_name = props.get("tool", "unknown")
        tool_input = props.get("input", {})
        tool_output = props.get("output", {})
        session_id = props.get("session_id")
        success = props.get("success", True)

        logger.info(f"🔧 Tool execution: {tool_name} (success={success})")

        # Store tool used
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

        # Equivalent to PostToolUse hook
        hook_data = {
            "event_type": "PostToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "success": success,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

        self.hook_manager.run_hook("PostToolUse", hook_data)

        # Ask orchestrator for tool analysis
        async def analyze_tool_usage():
            response = await ask_orchestrator(
                component="event_bridge",
                request_type="decision",
                data={
                    "tool_name": tool_name,
                    "session_id": session_id,
                    "success": success,
                    "context": "tool_execution",
                },
            )
            return response

        # Run analysis in background
        asyncio.create_task(analyze_tool_usage())

    def _handle_error_event(self, event: Dict[str, Any]):
        """Handle error events."""
        props = event.get("properties", {})
        error_msg = props.get("error", "Unknown error")

        logger.error(f"❌ Error event: {error_msg[:200]}")

        # Ask orchestrator for error handling
        async def handle_error():
            response = await ask_orchestrator(
                component="event_bridge",
                request_type="decision",
                data={
                    "error_type": "opencode_error",
                    "error_message": error_msg,
                    "context": "error_handling",
                },
            )
            return response

        asyncio.create_task(handle_error())

    def _handle_failure_event(self, event: Dict[str, Any]):
        """Handle failure events."""
        props = event.get("properties", {})
        failure_type = props.get("type", "unknown")

        logger.warning(f"⚠️ Failure event: {failure_type}")

    def _handle_session_created(self, event: Dict[str, Any]):
        """Handle session creation events."""
        props = event.get("properties", {})
        session_id = props.get("session_id")

        logger.info(f"📁 Session created: {session_id}")

    def _handle_thinking_event(self, event: Dict[str, Any]):
        """Handle thinking events."""
        logger.debug("🤔 Thinking event detected")


def main():
    """Main function to start the enhanced event bridge."""
    bridge = EnhancedEventBridge()

    # Run in async context
    async def run():
        return await bridge.start()

    # Create event loop and run
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        success = loop.run_until_complete(run())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Enhanced Event Bridge stopped by user")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
