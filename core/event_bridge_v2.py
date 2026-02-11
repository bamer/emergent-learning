#!/usr/bin/env python3
"""
EventBridge v2.0 - Simplified Event Routing

Responsibilities:
- SSE event listening from OpenCode
- Direct logging to database
- Route events to LearningProcessor
- Status API endpoint
- NO hook execution (moved to LearningProcessor)
- NO AI calls (delegates to AgentManager)

This replaces the complex event_bridge.py with a streamlined version.
"""

import json
import sys
import time
import threading
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Configuration
OPENCODE_SERVER = "http://localhost:4096"
LOGS_DIR = ELF_DIR / "logs"
DB_PATH = ELF_DIR / "memory" / "index.db"
COORDINATION_DIR = ELF_DIR / ".coordination"
EVENT_BRIDGE_HEARTBEAT = COORDINATION_DIR / "event-bridge-heartbeat.json"
EVENT_BRIDGE_PID = COORDINATION_DIR / "event_bridge_v2.pid"
EVENT_BRIDGE_PORT = 9998

# Setup logging
import logging

try:
    from Open_ELF.utils.elf_logging import get_logger

    logger = get_logger("event_bridge", level=logging.DEBUG)
except ImportError:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("event_bridge")


class EventBridge:
    """
    Simplified EventBridge for routing OpenCode events.

    Flow:
    OpenCode SSE → EventBridge → Database logging
                             → LearningProcessor (for tool events)

    Key responsibilities:
    - Listen to SSE events from OpenCode
    - Poll sessions to detect tool usage (fallback)
    - Parse message.part.updated events for tool_use parts
    - Route tool events to LearningProcessor
    """

    def __init__(self):
        self.running = False
        self.event_count = 0
        self.started_at: Optional[datetime] = None
        self.last_event_time: Optional[str] = None
        self.session_tools: Dict[str, list] = {}
        self.seen_messages: Dict[str, set] = {}  # Track seen messages per session

        # Stats
        self.event_stats: Dict[str, int] = {}

        # HTTP session for connection pooling (reuse connections, better performance)
        self.http_session = requests.Session()
        self.http_session.headers.update({"User-Agent": "EventBridge-v2 ELF"})

        # Import LearningProcessor
        self.learning_processor = None
        try:
            from core.learning_processor import LearningProcessor, ToolEvent

            self.learning_processor = LearningProcessor()
            self.ToolEvent = ToolEvent
            logger.info("✅ LearningProcessor loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load LearningProcessor: {e}", exc_info=True)

        # Singleton lock tracking
        self._lock_acquired = False

    def _check_singleton_lock(self) -> "tuple[bool, str]":
        """
        Check if EventBridge is already running using PID file.

        Returns:
            (is_locked, message): Tuple indicating if locked and descriptive message
        """
        if not EVENT_BRIDGE_PID.exists():
            return False, ""

        try:
            existing_pid = int(EVENT_BRIDGE_PID.read_text().strip())

            # Check if process is running
            import os

            try:
                os.kill(existing_pid, 0)  # Signal 0 doesn't kill, just checks existence
                return True, f"EventBridge is already running (PID: {existing_pid})"
            except OSError:
                # Process not running, stale lock file
                EVENT_BRIDGE_PID.unlink()
                return False, ""
        except (ValueError, IOError) as e:
            logger.warning(f"Invalid PID file, removing: {e}")
            try:
                EVENT_BRIDGE_PID.unlink()
            except:
                pass
            return False, ""

    def _acquire_singleton_lock(self) -> bool:
        """
        Acquire singleton lock by creating PID file.

        Returns:
            True if lock acquired, False if already locked
        """
        # First check if already running
        is_locked, msg = self._check_singleton_lock()
        if is_locked:
            logger.error(f"⚠️  {msg}")
            logger.error("⚠️  Only one EventBridge instance can run at a time")
            return False

        # Create pid
        import os

        try:
            pid = os.getpid()
            COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
            EVENT_BRIDGE_PID.write_text(str(pid), encoding="utf-8")
            self._lock_acquired = True
            logger.info(f"🔒 Singleton lock acquired (PID: {pid})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to acquire singleton lock: {e}")
            return False

    def _release_singleton_lock(self):
        """Release singleton lock by removing PID file."""
        if not self._lock_acquired:
            return

        try:
            if EVENT_BRIDGE_PID.exists():
                EVENT_BRIDGE_PID.unlink()
                self._lock_acquired = False
                logger.info("🔓 Singleton lock released")
        except Exception as e:
            logger.warning(f"⚠️  Failed to release singleton lock: {e}")

    def _get_db_connection(self):
        """Get database connection."""
        if not DB_PATH.exists():
            return None
        try:
            import sqlite3

            return sqlite3.connect(str(DB_PATH), timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}", exc_info=True)
            return None

    def _log_event(
        self, event_type: str, details: str = "", data: Optional[Dict] = None
    ):
        """Log event to database."""
        self.event_count += 1
        self.last_event_time = datetime.now().isoformat()
        self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1

        # Log to database
        conn = self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, timestamp)
                    VALUES (?, ?, 1, ?, ?, ?)
                """,
                    (
                        "event",
                        event_type,
                        f"details:{details[:50]}",
                        json.dumps(data) if data else "",
                        self.last_event_time,
                    ),
                )
                conn.commit()
            except Exception as e:
                logger.debug(f"Failed to log event: {e}")
            finally:
                conn.close()

        # Update heartbeat periodically (every 30 events to avoid excessive writes)
        if self.event_count % 30 == 0:
            self._write_heartbeat()

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
                "status_server_running": True,  # We assume it's running if we can write heartbeat
                "health": "healthy" if self.running else "degraded",
                "event_stats": {
                    "total_types": len(self.event_stats),
                    "top_events": dict(top_events),
                    "last_updated": datetime.now().isoformat(),
                },
            }
            # Ensure coordination directory exists
            COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
            EVENT_BRIDGE_HEARTBEAT.write_text(json.dumps(heartbeat), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write heartbeat: {e}")
            # Note: Don't fail completely, but log the error for visibility

    def start(self) -> bool:
        """Start the EventBridge."""
        logger.info("=" * 70)
        logger.info("🌉 EventBridge v2.0 Starting")
        logger.info("=" * 70)

        # Check singleton lock - ensure only one instance runs
        if not self._acquire_singleton_lock():
            return False

        # Check OpenCode connection using /global/health
        try:
            response = self.http_session.get(
                f"{OPENCODE_SERVER}/global/health", timeout=30
            )
            if response.status_code != 200:
                logger.error("❌ OpenCode server not accessible")
                return False
            health_data = response.json()
            logger.info(
                f"✅ Connected to OpenCode server (v{health_data.get('version', '?')})"
            )
        except Exception as e:
            logger.error(f"❌ Cannot connect to OpenCode: {e}")
            return False

        self.running = True
        self.started_at = datetime.now()

        # Start SSE listener on /global/event endpoint
        sse_thread = threading.Thread(target=self._listen_events, daemon=True)
        sse_thread.start()
        logger.info("👂 SSE listener started on /global/event")

        # Start session polling as backup (for tools not captured via SSE)
        # polling_thread = threading.Thread(target=self._poll_sessions, daemon=True)
        # polling_thread.start()
        # logger.info("🔄 Session polling started (backup)")

        # Start status server (health and status endpoints)
        self._start_status_server()
        logger.info(f"✅ Status server on port {EVENT_BRIDGE_PORT}")

        # Write initial heartbeat
        self._write_heartbeat()
        logger.info("✅ Initial heartbeat written")

        return True

    def stop(self):
        """Stop the EventBridge and clean up resources."""
        logger.info("🛑 Stopping EventBridge...")
        self.running = False

        # Write final heartbeat
        self._write_heartbeat()

        # Release singleton lock
        self._release_singleton_lock()

        # Close HTTP session (releases connections)
        if hasattr(self, "http_session"):
            self.http_session.close()
            logger.info("✅ HTTP session closed")

        logger.info("✅ EventBridge stopped")

    def _listen_events(self):
        """Listen to OpenCode SSE stream."""
        logger.info("Listening to OpenCode events...")

        while self.running:
            try:
                response = self.http_session.get(
                    f"{OPENCODE_SERVER}/global/event",
                    stream=True,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=60,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Failed to connect to event stream: {response.status_code}"
                    )
                    time.sleep(20)
                    continue

                logger.info("✅ Connected to SSE stream")

                for line in response.iter_lines():
                    if not self.running:
                        break

                    if line:
                        line_str = line.decode("utf-8")
                        self._process_sse_line(line_str)

            except requests.exceptions.ChunkedEncodingError:
                logger.info("⚠️ SSE stream disconnected, reconnecting...")
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ Error listening to events: {e}")
                time.sleep(5)

    def _process_sse_line(self, line: str):
        """Process a single SSE line."""
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str:
                try:
                    data = json.loads(data_str)
                    self._handle_event(data)
                except json.JSONDecodeError:
                    pass

    def _handle_event(self, event: Dict[str, Any]):
        """Handle an event from OpenCode."""
        # Support both formats: {"type": "...", "properties": {...}}
        # and {"payload": {"type": "...", "properties": {...}}}
        if "payload" in event:
            payload = event["payload"]
            event_type = payload.get("type", "unknown")
            event_properties = payload.get("properties", {})
        else:
            event_type = event.get("type", "unknown")
            event_properties = event.get("properties", {})

        # Handle message.part.updated events (contains tool_use parts)
        if event_type == "message.part.updated":
            self._handle_message_part_updated_event(event)
            return

        # Extract details
        details = ""
        if event_type == "tool":
            tool_name = event_properties.get("tool", "unknown")
            details = f"Tool: {tool_name}"

            # Process through LearningProcessor
            if self.learning_processor:
                self._process_tool_event(event)

        elif event_type == "message":
            content_preview = event_properties.get("content", "")[:50]
            details = f"Message: {content_preview}..."
        elif event_type == "error":
            error_msg = event_properties.get("error", "Unknown error")
            details = f"Error: {error_msg[:100]}"

        # Log event
        self._log_event(event_type, details, event_properties)

        # Log to console (throttled)
        if event_type in ["tool", "error", "failure"]:
            logger.info(f"📡 Event: {event_type} | {details}")

    def _process_tool_event(self, event: Dict[str, Any]):
        """Process tool events through LearningProcessor."""
        if not self.learning_processor:
            return

        try:
            props = event.get("properties", {})
            tool_name = props.get("tool", "unknown")
            tool_input = props.get("input", {})
            tool_output = props.get("output", {})
            session_id = props.get("session_id", "")

            # Create ToolEvent
            tool_event = self.ToolEvent(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
            )

            # Process post-tool
            result = self.learning_processor.post_tool_process(tool_event)

            # Log tool event to database
            self._log_event(
                "tool",
                details=f"Tool: {tool_name}",
                data={
                    "tool": tool_name,
                    "session_id": session_id,
                    "input": tool_input,
                    "outcome": result.get("outcome", "unknown"),
                },
            )

        except Exception as e:
            logger.error(f"Error processing tool event: {e}")

    def _handle_message_part_updated_event(self, event: Dict[str, Any]):
        """Handle message.part.updated events (contains tool_use parts)."""
        props = event.get("properties", {})
        part = props.get("part", {})
        part_type = part.get("type", "")
        session_id = props.get("session_id", "")

        logger.debug(
            f"📝 Message part updated: {part_type} | Session: {session_id[:8]}..."
        )

        # Check for tool_use or tool part types
        if part_type in ["tool_use", "tool"]:
            tool_name = part.get("tool", "unknown")
            # Get tool_input and tool_output from state
            state = part.get("state", {})
            tool_input = state.get("input", {})
            tool_output = state.get("output", "")

            # Synthesize a tool event
            tool_event = {
                "type": "tool",
                "properties": {
                    "tool": tool_name,
                    "input": tool_input,
                    "output": tool_output,
                    "session_id": session_id,
                    "success": state.get("status") == "completed",
                },
            }

            # Process as a regular tool event
            self._process_tool_event(tool_event)

    def _poll_sessions(self):
        """Poll sessions to detect tool usage (fallback for events not captured via SSE)."""
        logger.info("🔄 Starting session polling...")

        while self.running:
            try:
                # Get all sessions
                response = self.http_session.get(
                    f"{OPENCODE_SERVER}/session", timeout=10
                )
                if response.status_code != 200:
                    time.sleep(5)
                    continue

                sessions = response.json()
                total_tools_found = 0

                for session in sessions:
                    session_id = session.get("id")
                    if not session_id:
                        continue

                    # Initialize tracker for this session
                    if session_id not in self.seen_messages:
                        self.seen_messages[session_id] = set()

                    # Get messages for this session
                    msg_response = self.http_session.get(
                        f"{OPENCODE_SERVER}/session/{session_id}/message", timeout=10
                    )

                    if msg_response.status_code != 200:
                        continue

                    messages = msg_response.json()

                    # Process new messages
                    for msg in messages:
                        msg_id = msg.get("info", {}).get("id")
                        if not msg_id or msg_id in self.seen_messages[session_id]:
                            continue

                        self.seen_messages[session_id].add(msg_id)

                        # Check for tools in message parts
                        parts = msg.get("parts", [])
                        for part in parts:
                            part_type = part.get("type")
                            # OpenCode envoie les outils dans "step-start", pas "tool_use"
                            if part_type in ["tool_use", "tool", "step-start"]:
                                # Pour step-start, extraire le tool_name du contenu
                                if part_type == "step-start":
                                    content = part.get("content", {})
                                    tool_name = content.get("type", "unknown")
                                    # Essayer d'extraire le tool name de step_name
                                    step_name = part.get("step_name", "")
                                    if not tool_name or tool_name == "unknown":
                                        tool_name = (
                                            step_name.replace(" ", "_").lower()
                                            or "step"
                                        )
                                else:
                                    tool_name = part.get("tool", "unknown")
                                # Get tool_input and tool_output from state
                                state = part.get("state", {})
                                tool_input = state.get("input", {})
                                tool_output = state.get("output", "")

                                total_tools_found += 1

                                # Synthesize and process tool event
                                tool_event = {
                                    "type": "tool",
                                    "properties": {
                                        "tool": tool_name,
                                        "input": tool_input,
                                        "output": tool_output,
                                        "session_id": session_id,
                                        "success": state.get("status") == "completed",
                                    },
                                }
                                self._process_tool_event(tool_event)

                if total_tools_found > 0:
                    logger.debug(f"📊 Poll: {total_tools_found} tools processed")

                # Wait before next poll ( réduit à 2 secondes pour réactivité )
                time.sleep(2)

            except Exception as e:
                logger.error(f"❌ Error polling sessions: {e}")
                time.sleep(3)

    def _start_status_server(self):
        """Start HTTP status server."""
        bridge = self

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
                        "event_stats": bridge.event_stats,
                        "opencode_server": OPENCODE_SERVER,
                        "started_at": bridge.started_at.isoformat()
                        if bridge.started_at
                        else None,
                        "uptime_seconds": uptime_seconds,
                        "last_event_time": bridge.last_event_time,
                        "version": "2.0",
                    }
                    self.wfile.write(json.dumps(status).encode())

                elif self.path == "/api/v1/health":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()

                    health = {
                        "status": "healthy",
                        "service": "event_bridge",
                        "running": bridge.running,
                        "events": bridge.event_count,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.wfile.write(json.dumps(health).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                # Suppress request logs
                pass

        server = HTTPServer(("", EVENT_BRIDGE_PORT), StatusHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="EventBridge v2.0")
    parser.add_argument("start", nargs="?", help="Start the bridge")
    parser.add_argument("status", nargs="?", help="Show status")

    args = parser.parse_args()

    bridge = EventBridge()

    if len(sys.argv) > 1 and sys.argv[1] == "start":
        if bridge.start():
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n👋 Shutting down EventBridge...")
                bridge.stop()
    else:
        # Show status
        try:
            response = bridge.http_session.get(
                f"http://localhost:{EVENT_BRIDGE_PORT}/status", timeout=2
            )
            if response.status_code == 200:
                status = response.json()
                print(json.dumps(status, indent=2))
            else:
                logger.error("EventBridge not running")
        except Exception as e:
            logger.error(
                f"EventBridge not running or not accessible: {e}", exc_info=True
            )


if __name__ == "__main__":
    main()
