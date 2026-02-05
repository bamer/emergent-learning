#!/usr/bin/env python3
"""
Unified Orchestrator - Event Bridge + AI Decision Engine
Simple, fully async, no abstractions
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass

# Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnifiedOrchestrator")

# Constants
OPENCODE_SERVER = "http://localhost:4096"
ORCHESTRATOR_PORT = 9999


@dataclass
class Event:
    """System event"""

    id: str
    type: str
    severity: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    action: Optional[str] = None


class UnifiedOrchestrator:
    """Central orchestrator - Event Bridge + AI Brain"""

    def __init__(self):
        self.running = False
        self.events: List[Event] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Start the orchestrator"""
        logger.info("=" * 70)
        logger.info("🚀 Unified Orchestrator Starting")
        logger.info("=" * 70)

        self.running = True
        self.session = aiohttp.ClientSession()

        # Start status server (threaded)
        self._start_status_server()

        # Start listeners
        listeners = [
            asyncio.create_task(self._listen_opencode()),
        ]
        logger.info("👂 Listeners started")

        # Start processor
        processor = asyncio.create_task(self._process_events())
        logger.info("⚙️ Processor started")

        # Main loop
        tick = 0
        try:
            while self.running:
                tick += 1
                if tick % 10 == 0:
                    logger.info(f"⏰ Tick #{tick}")
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")

        # Cleanup
        for l in listeners:
            l.cancel()
        processor.cancel()
        await self.session.close()

    async def _listen_opencode(self):
        """Listen to OpenCode SSE events - FULLY ASYNC"""
        logger.info("🎧 Listening to OpenCode SSE...")

        while self.running:
            try:
                async with self.session.get(
                    f"{OPENCODE_SERVER}/event",
                    headers={"Accept": "text/event-stream"},
                    timeout=aiohttp.ClientTimeout(total=None),
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ SSE error: {response.status}")
                        await asyncio.sleep(5)
                        continue

                    logger.info("✅ Connected to SSE")

                    async for line in response.content:
                        if not self.running:
                            break

                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data:"):
                            await self._process_sse_line(line_str)

            except Exception as e:
                logger.error(f"❌ SSE error: {e}")
                await asyncio.sleep(5)

    async def _process_sse_line(self, line: str):
        """Process SSE line"""
        data_str = line[5:].strip()
        if not data_str:
            return

        try:
            data = json.loads(data_str)
            event = Event(
                id=f"{int(datetime.now().timestamp() * 1000000)}",
                type=data.get("type", "unknown"),
                severity=self._severity(data),
                source="opencode",
                data=data.get("properties", {}),
                timestamp=datetime.now(),
            )
            await self.event_queue.put(event)
            logger.debug(f"📥 Q'd: {event.type}")

        except json.JSONDecodeError:
            pass

    def _severity(self, data: Dict) -> str:
        """Determine severity"""
        t = data.get("type", "").lower()
        if any(x in t for x in ["error", "fail", "exception"]):
            return "error"
        if any(x in t for x in ["crit", "fatal"]):
            return "critical"
        if any(x in t for x in ["warn", "alert"]):
            return "warning"
        return "info"

    async def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                event = await self.event_queue.get()
                event.processed = True
                event.action = await self._decide(event)
                self.events.append(event)
                logger.info(f"✅ {event.type} -> {event.action}")
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"❌ Process error: {e}")
                await asyncio.sleep(1)

    async def _decide(self, event: Event) -> str:
        """AI decision engine (simplified)"""
        if event.severity == "critical":
            return "ESCALATE_TO_CEO"
        elif event.severity == "error":
            return "RETRY_OR_SKIP"
        elif event.severity == "warning":
            return "LOG_AND_CONTINUE"
        return "LOG"

    def _start_status_server(self):
        """Start status endpoint"""
        self_ref = self

        class StatusHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/status":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    status = {
                        "running": self_ref.running,
                        "events_processed": len(
                            [e for e in self_ref.events if e.processed]
                        ),
                        "queue_size": self_ref.event_queue.qsize(),
                        "recent": [
                            {"type": e.type, "severity": e.severity, "action": e.action}
                            for e in self_ref.events[-10:]
                        ],
                    }
                    self.wfile.write(json.dumps(status).encode())

        server = HTTPServer(("localhost", ORCHESTRATOR_PORT), StatusHandler)
        import threading

        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logger.info(f"📊 Status: http://localhost:{ORCHESTRATOR_PORT}/status")


async def main():
    """Main entry"""
    import sys

    if len(sys.argv) < 2 or sys.argv[1] != "start":
        print("Usage: unified_orchestrator.py start")
        return

    orchestrator = UnifiedOrchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
