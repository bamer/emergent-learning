#!/usr/bin/env python3
"""
Unified OpenCode Orchestrator - Central Event Processing System
==============================================================

Central orchestrator that unifies the Event Bridge and Orchestrator into a single
intelligent system that monitors events and makes autonomous decisions.

Features:
- Unified event processing from both OpenCode events and file system
- Intelligent decision making for escalations and system issues
- Autonomous restart and recovery mechanisms
- AI-driven decision engine for handling system problems
- Central hub replacing separate Event Bridge and Orchestrator
"""

import json
import logging
import sys
import time
import threading
import asyncio
import aiohttp
import aiofiles
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnifiedOrchestrator")

# Constants
OPENCODE_SERVER = "http://localhost:4096"
TASKS_DIR = Path.home() / ".opencode" / "tasks"
COORDINATION_DIR = Path.home() / ".opencode" / "emergent-learning" / ".coordination"
MISSIONS_DIR = COORDINATION_DIR / "missions"
CEO_INBOX_DIR = Path.home() / ".opencode" / "emergent-learning" / "ceo-inbox"
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

# Import async OpenCode client
try:
    from async_opencode_client import AsyncOpenCodeClient
except ImportError:
    logger.warning(
        "async_opencode_client not available, will simulate client for testing"
    )
    AsyncOpenCodeClient = None


@dataclass
class Event:
    """Represents a system event for processing."""

    id: str
    type: str  # "tool_failure", "error", "system_health", "ceo_escalation", etc.
    severity: str  # "info", "warning", "error", "critical"
    source: str  # "opencode", "file_system", "database", etc.
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    action_taken: Optional[str] = None


@dataclass
class Mission:
    """Represents a mission in progress."""

    id: str
    agent_type: str
    mission: str
    status: str  # pending, in_progress, completed, error
    start_time: datetime
    end_time: Optional[datetime] = None
    response: Optional[str] = None
    session_id: Optional[str] = None
    task_file: Optional[Path] = None


class TaskManager:
    """Manages tasks in ~/.opencode/tasks/"""

    def __init__(self):
        self.tasks_dir = TASKS_DIR
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create_task(self, mission: Mission) -> Path:
        """Creates a task file for the dashboard."""
        # Create a session directory
        session_dir = self.tasks_dir / f"elf_{mission.start_time.strftime('%Y%m%d')}"
        session_dir.mkdir(exist_ok=True)

        # Generate task ID
        task_id = f"{mission.agent_type}_{mission.id}"
        task_file = session_dir / f"{task_id}.json"

        task_data = {
            "id": task_id,
            "subject": f"[{mission.agent_type.upper()}] {mission.mission[:80]}...",
            "description": mission.mission,
            "status": mission.status,
            "session_id": session_dir.name,
            "session_name": f"ELF Unified Orchestrator {mission.start_time.strftime('%Y-%m-%d')}",
            "notes": [
                {
                    "text": f"Mission started at {mission.start_time.isoformat()}",
                    "timestamp": mission.start_time.isoformat(),
                    "source": "orchestrator",
                }
            ],
        }

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        mission.task_file = task_file
        logger.info(f"📝 Task created: {task_file.name}")
        return task_file

    def update_task(self, mission: Mission):
        """Updates the task file with results."""
        if not mission.task_file or not mission.task_file.exists():
            return

        try:
            with open(mission.task_file, "r") as f:
                task_data = json.load(f)

            task_data["status"] = mission.status

            if mission.response:
                task_data["notes"].append(
                    {
                        "text": f"Response: {mission.response[:500]}",
                        "timestamp": datetime.now().isoformat(),
                        "source": mission.agent_type,
                    }
                )

            if mission.end_time:
                task_data["notes"].append(
                    {
                        "text": f"Mission completed at {mission.end_time.isoformat()}",
                        "timestamp": mission.end_time.isoformat(),
                        "source": "orchestrator",
                    }
                )

            with open(mission.task_file, "w") as f:
                json.dump(task_data, f, indent=2)

            logger.info(
                f"📝 Task updated: {mission.task_file.name} -> {mission.status}"
            )
        except Exception as e:
            logger.error(f"Failed to update task: {e}")


class AsyncOpenCodeClient:
    """Async wrapper for AsyncOpenCodeClient - manages lifecycle"""

    def __init__(self):
        if AsyncOpenCodeClient is None:
            raise RuntimeError(
                "AsyncOpenCodeClient is required but not available. "
                "Install aiohttp package."
            )
        self._client: Optional[AsyncOpenCodeClient] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the async client - requires real connection"""
        if not self._initialized:
            self._client = AsyncOpenCodeClient()
            await self._client.__aenter__()
            self._initialized = True
            logger.info("✅ AsyncOpenCodeClient initialized")

    async def shutdown(self):
        """Shutdown the async client"""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
        self._initialized = False
        logger.info("🔌 AsyncOpenCodeClient shut down")

    @property
    def client(self) -> Optional[AsyncOpenCodeClient]:
        """Get the underlying client"""
        return self._client

    async def health_check(self) -> bool:
        """Check if OpenCode server is responsive"""
        if self._client:
            return await self._client.health_check()
        return False

    async def send_message(
        self, message: str, agent: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Send message asynchronously to real OpenCode server"""
        if self._client:
            return await self._client.send_message(message, agent)
        return False, "Client not initialized"

    async def listen_sse(self):
        """Listen to SSE events asynchronously from real OpenCode server"""
        if self._client:
            async for event in self._client.listen_sse():
                yield event
        else:
            raise RuntimeError("Client not initialized")


class UnifiedOrchestrator:
    """Central orchestrator unifying Event Bridge and AI decision engine."""

    def __init__(self):
        self.client = AsyncOpenCodeClient()
        self.decision_engine = None  # Will be initialized after client
        self.running = False
        self.missions: Dict[str, Mission] = {}
        self.processing_missions: set = set()
        self.mission_queue: asyncio.Queue = asyncio.Queue()
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.events: List[Event] = []

    def _determine_severity(self, event_data: Dict) -> str:
        """Determine event severity based on event type and content."""
        event_type = event_data.get("type", "").lower()

        severity_map = {
            "error": "error",
            "fail": "error",
            "exception": "error",
            "critical": "critical",
            "fatal": "critical",
            "warning": "warning",
            "warn": "warning",
            "alert": "warning",
            "info": "info",
            "success": "info",
            "connected": "info",
        }

        for keyword, severity in severity_map.items():
            if keyword in event_type:
                return severity

        return "info"

    async def _monitor_ceo_inbox(self):
        """Monitor CEO inbox directory for new escalations."""
        logger.info(f"👀 Monitoring CEO inbox: {CEO_INBOX_DIR}")
        processed_files = set()

        while self.running:
            try:
                if not CEO_INBOX_DIR.exists():
                    await asyncio.sleep(30)
                    continue

                for file_path in CEO_INBOX_DIR.glob("*.md"):
                    if file_path.name in processed_files:
                        continue

                    try:
                        # Read file content
                        content = file_path.read_text(encoding="utf-8")

                        # Create event for this escalation
                        event = Event(
                            id=f"ceo_{file_path.stem}",
                            type="ceo_escalation",
                            severity="critical",  # CEO escalations are always critical
                            source="file_system",
                            data={
                                "filename": file_path.name,
                                "content": content[:500],  # First 500 chars
                                "full_path": str(file_path),
                            },
                            timestamp=datetime.now(),
                        )

                        # Add to event queue
                        await self.event_queue.put(event)
                        processed_files.add(file_path.name)
                        logger.info(f"📥 New CEO escalation detected: {file_path.name}")

                    except Exception as e:
                        logger.error(
                            f"❌ Error reading CEO inbox file {file_path.name}: {e}"
                        )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"❌ Error monitoring CEO inbox: {e}")
                await asyncio.sleep(60)

    async def _monitor_system_health(self):
        """Monitor system health through database queries."""
        logger.info("🏥 Monitoring system health")

        while self.running:
            try:
                # Check database health
                db_healthy = await self._check_database_health()

                # Create health event
                event = Event(
                    id=f"health_{int(time.time())}",
                    type="system_health",
                    severity="info" if db_healthy else "error",
                    source="database",
                    data={
                        "database_healthy": db_healthy,
                        "status": "healthy" if db_healthy else "degraded",
                    },
                    timestamp=datetime.now(),
                )

                # Add to event queue
                await self.event_queue.put(event)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"❌ Error monitoring system health: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _check_database_health(self) -> bool:
        """Check if database is healthy."""
        try:
            if DB_PATH.exists():
                # Simple existence check for now
                # In a real implementation, this would do deeper health checks
                return True
            else:
                return False
        except Exception:
            return False

    async def _monitor_watcher_events(self):
        """Monitor watcher events from event chronicle."""
        logger.info("👀 Monitoring watcher events")
        EVENT_CHRONICLE_DIR = (
            Path.home() / ".opencode" / "emergent-learning" / "event_chronicle"
        )
        processed_events = set()

        while self.running:
            try:
                if not EVENT_CHRONICLE_DIR.exists():
                    await asyncio.sleep(60)
                    continue

                # Look for recent chronicle files
                chronicle_files = sorted(
                    EVENT_CHRONICLE_DIR.rglob("*.jsonl"), reverse=True
                )[:5]

                for chronicle_file in chronicle_files:
                    try:
                        with open(chronicle_file, "r", encoding="utf-8") as f:
                            for line_num, line in enumerate(f):
                                line_id = f"{chronicle_file.name}:{line_num}"
                                if line_id in processed_events:
                                    continue

                                try:
                                    event_data = json.loads(line.strip())
                                    event_type = event_data.get("event_type", "")

                                    # Look for watcher-related events
                                    if (
                                        "watcher" in event_type.lower()
                                        or "sentinel" in event_type.lower()
                                    ):
                                        # Create watcher event
                                        event = Event(
                                            id=f"watcher_{int(time.time() * 1000000)}",
                                            type="watcher_alert",
                                            severity=self._determine_severity(
                                                {
                                                    "type": event_type,
                                                    "properties": event_data,
                                                }
                                            ),
                                            source="watcher_system",
                                            data=event_data,
                                            timestamp=datetime.now(),
                                        )

                                        # Add to event queue
                                        await self.event_queue.put(event)
                                        processed_events.add(line_id)

                                except json.JSONDecodeError:
                                    continue

                    except Exception as e:
                        logger.error(
                            f"❌ Error reading chronicle file {chronicle_file}: {e}"
                        )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"❌ Error monitoring watcher events: {e}")
                await asyncio.sleep(60)

    async def _process_events(self):
        """Process events from the event queue."""
        while self.running:
            try:
                # Get event from queue (blocking but async)
                event = await self.event_queue.get()

                # Store event for tracking
                self.events.append(event)

                # Process event with decision engine
                action_taken = await self.decision_engine.process_event(event)
                event.processed = True
                event.action_taken = action_taken

                logger.info(
                    f"✅ Processed event {event.type} -> Action: {action_taken}"
                )

                # Mark task as done
                self.event_queue.task_done()

            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                await asyncio.sleep(1)

    async def _process_missions(self):
        """Process missions from the mission queue."""
        while self.running:
            try:
                # Get mission from queue (blocking but async)
                mission_info = await self.mission_queue.get()

                # Process in background task
                asyncio.create_task(self._execute_mission(mission_info))

                # Mark task as done
                self.mission_queue.task_done()

            except Exception as e:
                logger.error(f"❌ Error processing mission queue: {e}")
                await asyncio.sleep(1)

    async def _execute_mission(self, mission_info: dict):
        """Execute a mission asynchronously."""
        mission_file = mission_info["file"]
        mission_data = mission_info["data"]
        agent_type = mission_info["agent_type"]
        description = mission_info["description"]
        task_id = mission_info["task_id"]

        try:
            # Create mission object
            mission = Mission(
                id=task_id,
                agent_type=agent_type,
                mission=description,
                status="pending",
                start_time=datetime.now(),
            )

            self.missions[task_id] = mission

            # Create task file
            self.task_manager.create_task(mission)

            logger.info(f"🎯 Mission started: {agent_type} - {description[:60]}...")

            # Update status to in_progress
            mission.session_id = "persistent-session"
            mission.status = "in_progress"
            self.task_manager.update_task(mission)

            # Update mission file
            mission_data["status"] = "in_progress"
            mission_data["startedAt"] = datetime.now().isoformat()
            async with aiofiles.open(mission_file, "w") as f:
                await f.write(json.dumps(mission_data, indent=2))

            # Send message via optimized client (async)
            logger.info(f"📤 Sending message for mission {task_id}")
            success, response_text = await self.client.send_message(
                description, agent_type
            )

            # Update mission with results
            mission.end_time = datetime.now()

            if success:
                if response_text:
                    mission.response = response_text
                    mission.status = "completed"
                    logger.info(f"✅ Mission completed: {agent_type}")
                else:
                    mission.status = "error"
                    mission.response = "No response received from agent"
                    logger.error(f"❌ No response from {agent_type}")
            else:
                mission.status = "error"
                mission.response = response_text or "Failed to send message to agent"
                logger.error(f"❌ Failed to send message to {agent_type}")

            # Update task file
            self.task_manager.update_task(mission)

            # Update mission file
            mission_data["status"] = mission.status
            mission_data["completedAt"] = mission.end_time.isoformat()
            mission_data["response"] = (
                mission.response[:1000] if mission.response else ""
            )
            async with aiofiles.open(mission_file, "w") as f:
                await f.write(json.dumps(mission_data, indent=2))

            logger.info(f"✅ Mission {mission_file.name} processing completed")

        except Exception as e:
            logger.error(f"❌ Error executing mission {mission_file.name}: {e}")
            # Update with error status
            try:
                mission_data["status"] = "error"
                mission_data["error"] = str(e)
                mission_data["completedAt"] = datetime.now().isoformat()
                async with aiofiles.open(mission_file, "w") as f:
                    await f.write(json.dumps(mission_data, indent=2))
            except:
                pass
        finally:
            # Remove from processing set
            self.processing_missions.discard(mission_file.name)

    def _start_status_server(self):
        """Start HTTP server for status reporting."""
        orchestrator_self = self

        class StatusHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/status":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()

                    status = {
                        "running": orchestrator_self.running,
                        "events_processed": len(
                            [e for e in orchestrator_self.events if e.processed]
                        ),
                        "missions_count": len(orchestrator_self.missions),
                        "processing_count": len(orchestrator_self.processing_missions),
                        "queue_size": orchestrator_self.mission_queue.qsize(),
                        "events_in_queue": orchestrator_self.event_queue.qsize(),
                        "missions": [
                            {
                                "id": m.id,
                                "agent_type": m.agent_type,
                                "status": m.status,
                                "start_time": m.start_time.isoformat()
                                if m.start_time
                                else None,
                                "end_time": m.end_time.isoformat()
                                if m.end_time
                                else None,
                            }
                            for m in orchestrator_self.missions.values()
                        ],
                        "recent_events": [
                            {
                                "type": e.type,
                                "severity": e.severity,
                                "processed": e.processed,
                                "action_taken": e.action_taken,
                                "timestamp": e.timestamp.isoformat(),
                            }
                            for e in orchestrator_self.events[-10:]  # Last 10 events
                        ],
                    }
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer(("localhost", 9999), StatusHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info("📊 Status server started on http://localhost:9999/status")


async def main_async():
    """Async entry point."""
    if len(sys.argv) < 2:
        print("Usage: python unified_orchestrator.py <command> [args]")
        print("Commands:")
        print("  start                    - Start the unified orchestrator")
        print("  status                   - Show current status")
        sys.exit(1)

    command = sys.argv[1]
    orchestrator = UnifiedOrchestrator()

    if command == "start":
        await orchestrator.start()

    elif command == "status":
        try:
            import requests

            response = requests.get("http://localhost:9999/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"Running: {status['running']}")
                print(f"Events processed: {status['events_processed']}")
                print(f"Missions: {status['missions_count']}")
                print(f"Processing: {status['processing_count']}")
                print(f"Event Queue: {status['events_in_queue']}")
                print(f"Mission Queue: {status['queue_size']}")
                for m in status["missions"]:
                    print(f"  - {m['agent_type']}: {m['status']}")
            else:
                print("❌ Orchestrator not running")
        except Exception as e:
            print(f"❌ Orchestrator not running: {e}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
