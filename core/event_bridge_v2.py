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
EVENT_BRIDGE_PORT = 9998

# Setup logging
try:
    from Open_ELF.utils.elf_logging import get_logger
    logger = get_logger("event_bridge")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("event_bridge")


class EventBridge:
    """
    Simplified EventBridge for routing OpenCode events.
    
    Flow:
    OpenCode SSE → EventBridge → Database logging
                             → LearningProcessor (for tool events)
    """
    
    def __init__(self):
        self.running = False
        self.event_count = 0
        self.started_at: Optional[datetime] = None
        self.last_event_time: Optional[str] = None
        self.session_tools: Dict[str, list] = {}
        
        # Stats
        self.event_stats: Dict[str, int] = {}
        
        # Import LearningProcessor
        self.learning_processor = None
        try:
            from core.learning_processor import LearningProcessor, ToolEvent
            self.learning_processor = LearningProcessor()
            self.ToolEvent = ToolEvent
            logger.info("✅ LearningProcessor loaded")
        except Exception as e:
            logger.warning(f"⚠️ LearningProcessor not available: {e}")
    
    def _get_db_connection(self):
        """Get database connection."""
        if not DB_PATH.exists():
            return None
        try:
            import sqlite3
            return sqlite3.connect(str(DB_PATH), timeout=5.0)
        except:
            return None
    
    def _log_event(self, event_type: str, details: str = "", data: Dict = None):
        """Log event to database."""
        self.event_count += 1
        self.last_event_time = datetime.now().isoformat()
        self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1
        
        # Log to database
        conn = self._get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metrics (metric_type, metric_name, metric_value, tags, context, created_at)
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (
                    "event",
                    event_type,
                    f"details:{details[:50]}",
                    json.dumps(data) if data else "",
                    self.last_event_time
                ))
                conn.commit()
            except Exception as e:
                logger.debug(f"Failed to log event: {e}")
            finally:
                conn.close()
    
    def start(self) -> bool:
        """Start the EventBridge."""
        logger.info("=" * 70)
        logger.info("🌉 EventBridge v2.0 Starting")
        logger.info("=" * 70)
        
        # Check OpenCode connection
        try:
            response = requests.get(f"{OPENCODE_SERVER}/", timeout=5)
            if response.status_code != 200:
                logger.error("❌ OpenCode server not accessible")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to OpenCode: {e}")
            return False
        
        logger.info("✅ Connected to OpenCode server")
        
        self.running = True
        self.started_at = datetime.now()
        
        # Start SSE listener in background thread
        listener_thread = threading.Thread(target=self._listen_events, daemon=True)
        listener_thread.start()
        logger.info("👂 SSE listener started")
        
        # Start status server
        self._start_status_server()
        logger.info(f"✅ Status server on port {EVENT_BRIDGE_PORT}")
        
        return True
    
    def _listen_events(self):
        """Listen to OpenCode SSE stream."""
        logger.info("Listening to OpenCode events...")
        
        while self.running:
            try:
                response = requests.get(
                    f"{OPENCODE_SERVER}/event",
                    stream=True,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=60,
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to connect to event stream: {response.status_code}")
                    time.sleep(5)
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
        event_type = event.get("type", "unknown")
        event_properties = event.get("properties", {})
        
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
                timestamp=datetime.now().isoformat()
            )
            
            # Process post-tool
            result = self.learning_processor.post_tool_process(tool_event)
            
            logger.debug(f"LearningProcessor result: {result}")
            
        except Exception as e:
            logger.error(f"Error processing tool event: {e}")
    
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
                        uptime_seconds = int((datetime.now() - bridge.started_at).total_seconds())
                    
                    status = {
                        "running": bridge.running,
                        "events_processed": bridge.event_count,
                        "event_stats": bridge.event_stats,
                        "opencode_server": OPENCODE_SERVER,
                        "started_at": bridge.started_at.isoformat() if bridge.started_at else None,
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
                bridge.running = False
    else:
        # Show status
        try:
            response = requests.get(f"http://localhost:{EVENT_BRIDGE_PORT}/status", timeout=2)
            if response.status_code == 200:
                status = response.json()
                print(json.dumps(status, indent=2))
            else:
                print("❌ EventBridge not running")
        except:
            print("❌ EventBridge not running or not accessible")


if __name__ == "__main__":
    main()
