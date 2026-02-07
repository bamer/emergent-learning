#!/usr/bin/env python3
"""
Unified Orchestrator - Service Management and Event Processing

The Unified Orchestrator connects to EventBridge (port 9998) and:
- Listens to events: tool, message, error, failure, service, health
- Manages system services (Learning Capture, Watcher)
- Autoservices on failure (restart Watcher, restart Learning Capture)
- Escalates critical issues

Usage:
    python unified_orchestrator.py start

Dependencies:
    - EventBridge must be running on port 9998
    - Uses utils.event_logger for database logging
"""

import asyncio
import logging
import subprocess
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Constants
OPENCODE_SERVER = "http://localhost:4096"
EVENT_BRIDGE_URL = "http://localhost:9998"
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
OPEN_ELF_DIR = ELF_DIR / "Open_ELF"

# Path configuration
LEARNING_CAPTURE_SCRIPT = ELF_DIR / "scripts/background-learning-capture.py"
LEARNING_CAPTURE_LOG = OPEN_ELF_DIR / "logs/learning-capture.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnifiedOrchestrator")

# Event logging to database
DATABASE_LOGGING_AVAILABLE = False
try:
    from utils.event_logger import log_event as log_orchestrator_db

    DATABASE_LOGGING_AVAILABLE = True
    logger.info("✓ Database logging available")
except ImportError:
    logger.warning("⚠ Database logging unavailable")


@dataclass
class Event:
    """System event from EventBridge.

    Attributes:
        id: Unique event identifier
        type: Event type (message, tool, error, failure, service, health)
        severity: Severity level (info, warning, error, critical)
        source: Event source (event_bridge, orchestrator, etc.)
        data: Event properties
        timestamp: Event timestamp
        processed: Whether event was processed
        action: Action taken for this event
    """

    id: str
    type: str
    severity: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    action: Optional[str] = None


class UnifiedOrchestrator:
    """Unified Orchestrator manages system services and processes events.

    The orchestrator connects to running EventBridge and:
    1. Registers as a listener for events
    2. Processes events asyncronously
    3. Manages service health (Learning Capture, Watcher)
    4. Autoservices failed services
    5. Escalates critical issues
    """

    def __init__(self):
        self.running = False
        self.events: List[Event] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.bridge = None  # EventBridge instance (don't create, connect to existing)

        # Service tracking
        self.learning_capture_active = False
        self.learning_capture_pid: Optional[str] = None
        self.watcher_pid: Optional[str] = None

        # Health tracking
        self._services_health: Dict[str, bool] = {}
        self._service_alerts: Dict[str, int] = {}
        self._last_health_check: Optional[datetime] = None
        self.started_at: Optional[datetime] = None

    def start(self):
        """Start orchestrator (sync wrapper)."""
        asyncio.run(self._start_async())

    async def _start_async(self):
        """Start orchestrator and connect to EventBridge."""
        logger.info("=" * 60)
        logger.info("🚀 Unified Orchestrator Starting")
        logger.info("=" * 60)

        self.running = True
        self.started_at = datetime.now()

        # 1. Connect to existing EventBridge
        if not self._connect_to_eventbridge():
            return

        # 2. Register as listener
        self._register_listeners()

        # 3. Start event processor
        processor = asyncio.create_task(self._process_events())
        logger.info("⚙️  Event processor started")

        # Main loop
        tick = 0
        try:
            while self.running:
                tick += 1
                if tick % 10 == 0:
                    logger.info(f"⏰ Tick #{tick}")
                    self._check_services_health()
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")

        # Cleanup
        processor.cancel()
        logger.info("✅ Unified Orchestrator stopped")

    def _connect_to_eventbridge(self) -> bool:
        """Connect to running EventBridge instance.

        Returns:
            True if successfully connected, False otherwise.
        """
        try:
            # Check EventBridge status
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            if response.status_code != 200:
                logger.error(f"❌ EventBridge returned status {response.status_code}")
                return False

            logger.info(f"✅ Connected to EventBridge ({EVENT_BRIDGE_URL}/status)")

            # Create EventBridge instance (don't start, it's already running)
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "event_bridge_module",
                str(OPEN_ELF_DIR / "orchestrator/event_bridge.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.bridge = module.EventBridge()
            self.bridge.running = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to EventBridge: {e}")
            logger.error(
                f"\nMake sure EventBridge is running:\n"
                f"  cd {OPEN_ELF_DIR / 'orchestrator'}\n"
                f"  python event_bridge.py start"
            )
            return False

    def _register_listeners(self):
        """Register as EventBridge listener for relevant events."""
        self.bridge.register_listener(
            listener_id="unified_orchestrator",
            callback=self._on_event_received_sync,
            event_types=["tool", "message", "error", "failure", "service", "health"],
        )
        logger.info(
            "✅ Registered for events: tool, message, error, failure, service, health"
        )

    def _on_event_received_sync(self, event_data: Dict):
        """Callback for EventBridge events (runs in EventBridge thread).

        Args:
            event_data: Event data from EventBridge
        """
        event_type = event_data.get("type", "unknown")
        logger.debug(f"📨 Received event: {event_type}")

        # Create Event object
        event = Event(
            id=str(int(datetime.now().timestamp() * 1_000_000)),
            type=event_type,
            severity=self._get_severity(event_data),
            source="event_bridge",
            data=event_data.get("properties", {}),
            timestamp=datetime.now(),
        )

        # Put in async queue (thread-safe)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        asyncio.run_coroutine_threadsafe(self.event_queue.put(event), loop)

    def _get_severity(self, event_data: Dict) -> str:
        """Determine event severity from type and properties.

        Args:
            event_data: Event data from EventBridge

        Returns:
            Severity level: info, warning, error, or critical
        """
        event_type = event_data.get("type", "").lower()
        severity = event_data.get("severity", "").lower()

        # Check explicit severity
        if severity in ["critical", "error", "warning"]:
            return severity

        # Infer from type
        if any(x in event_type for x in ["crit", "fatal"]):
            return "critical"
        if any(x in event_type for x in ["error", "fail", "exception"]):
            return "error"
        if any(x in event_type for x in ["warn", "alert"]):
            return "warning"
        return "info"

    async def _process_events(self):
        """Process events from queue asyncronously."""
        while self.running:
            try:
                event = await self.event_queue.get()
                event.processed = True
                event.action = await self._decide_action(event)
                self.events.append(event)

                # Handle service events separately
                if event.type.lower() in ["service", "health"]:
                    self._handle_service_event(event)
                else:
                    self._log_event(event)

                logger.info(f"✅ {event.type} -> {event.action}")
                self.event_queue.task_done()

            except Exception as e:
                logger.error(f"❌ Process event error: {e}")
                await asyncio.sleep(1)

    async def _decide_action(self, event: Event) -> str:
        """Decide action to take for an event.

        Simplified decision engine. Future: use AI agent for decisions.

        Args:
            event: Event to decide action for

        Returns:
            Action string: LOG, RETRY, ESCALATE, RESTART, etc.
        """
        if event.severity == "critical":
            return "ESCALATE"
        elif event.severity == "error":
            event_type = event.type.lower()
            if event_type == "service":
                return "RESTART_SERVICE"
            return "LOG_AND_RETRY"
        elif event.severity == "warning":
            return "LOG_AND_MONITOR"
        return "LOG"

    def _handle_service_event(self, event: Event):
        """Handle service/health events and take recovery actions.

        Args:
            event: Service event to handle
        """
        props = event.data
        service = props.get("service", props.get("component", ""))
        status = props.get("status", props.get("state", ""))

        if not service:
            return

        logger.warning(f"⚠️ Service alert: {service} -> {status}")

        # Track alerts
        alert_key = f"{service}_{event.severity}"
        self._service_alerts[alert_key] = self._service_alerts.get(alert_key, 0) + 1

        # Auto-recover based on service type
        service_lower = service.lower()

        # Learning Capture
        if "learning" in service_lower and "capture" in service_lower:
            if status.lower() in ["down", "inactive", "stopped", "failed"]:
                logger.info("🔄 Attempting to restart Learning Capture...")
                self._restart_learning_capture()

        # Watcher
        elif "watcher" in service_lower:
            if status.lower() in ["down", "inactive", "stopped", "failed"]:
                logger.info("🔄 Attempting to restart Watcher...")
                self._restart_watcher()

        # Escalate critical issues
        if event.severity == "critical":
            self._escalate_critical(service, status, props)

    def _restart_learning_capture(self) -> bool:
        """Restart Learning Capture service.

        Returns:
            True if restarted successfully, False otherwise.
        """
        try:
            # Kill existing
            subprocess.run(
                ["pkill", "-f", "background-learning-capture.py"], capture_output=True
            )
            import time

            time.sleep(2)

            # Start new
            LEARNING_CAPTURE_LOG.parent.mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                ["python3", str(LEARNING_CAPTURE_SCRIPT)],
                stdout=open(LEARNING_CAPTURE_LOG, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            time.sleep(2)

            # Verify
            check = subprocess.run(
                ["pgrep", "-f", "background-learning-capture.py"],
                capture_output=True,
                text=True,
            )
            if check.returncode == 0:
                self.learning_capture_active = True
                self.learning_capture_pid = check.stdout.strip()
                logger.info(
                    f"✅ Learning Capture restarted (PID: {self.learning_capture_pid})"
                )
                return True

            logger.error("❌ Failed to restart Learning Capture")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting Learning Capture: {e}")
            return False

    def _restart_watcher(self) -> bool:
        """Restart Watcher service.

        Returns:
            True if restarted successfully, False otherwise.
        """
        try:
            # Kill existing
            subprocess.run(
                ["pkill", "-f", "watcher/elf_watcher.py"], capture_output=True
            )
            import time

            time.sleep(2)

            # Start new
            process = subprocess.Popen(
                ["python3", "watcher/elf_watcher.py"],
                cwd=str(OPEN_ELF_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            time.sleep(3)

            # Verify
            check = subprocess.run(
                ["pgrep", "-f", "watcher/elf_watcher.py"],
                capture_output=True,
                text=True,
            )
            if check.returncode == 0:
                logger.info("✅ Watcher restarted successfully")
                return True

            logger.error("❌ Failed to restart Watcher")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting Watcher: {e}")
            return False

    def _escalate_critical(self, service: str, status: str, details: Dict):
        """Escalate critical issue.

        TODO: Integrate with CEO agent or create incident tickets.

        Args:
            service: Service with critical issue
            status: Service status
            details: Additional details
        """
        logger.error(f"🔴 CRITICAL: {service} is {status} - Escalating")
        if DATABASE_LOGGING_AVAILABLE:
            log_orchestrator_db(
                event_type="critical_alert",
                source="unified_orchestrator",
                summary=f"CRITICAL: {service} - {status}",
                data={"service": service, "status": status, **details},
                status="escalated",
            )

    def _check_services_health(self) -> Dict[str, bool]:
        """Check health of all managed services.

        Args:
            health_status: Status dict with keys: event_bridge, watcher, learning_capture
        """
        health_status = {
            "event_bridge": False,
            "watcher": False,
            "learning_capture": False,
        }

        # EventBridge (HTTP)
        try:
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            health_status["event_bridge"] = response.status_code == 200
        except:
            logger.error(f'❌ Failed health_status["event_bridge"]')
            pass

        # Watcher (pgrep)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "watcher/elf_watcher.py"],
                capture_output=True,
                text=True,
            )
            health_status["watcher"] = result.returncode == 0
            if result.returncode == 0:
                self.watcher_pid = result.stdout.strip()
        except:
            logger.error(f'❌ Failed health_status["watcher"]')
            pass

        # Learning Capture (pgrep)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "background-learning-capture.py"],
                capture_output=True,
                text=True,
            )
            health_status["learning_capture"] = result.returncode == 0
            if result.returncode == 0:
                self.learning_capture_active = True
                self.learning_capture_pid = result.stdout.strip()
            else:
                self.learning_capture_active = False
                self.learning_capture_pid = None
        except:
            logger.error(f'❌ Failed health_status["learning_capture"]')
            pass

        self._services_health = health_status
        self._last_health_check = datetime.now()
        return health_status

    def _log_event(self, event: Event):
        """Log event to database.

        Args:
            event: Event to log
        """
        if not DATABASE_LOGGING_AVAILABLE:
            return

        try:
            log_orchestrator_db(
                event_type=event.type,
                source="unified_orchestrator",
                summary=f"{event.type}: {event.action}",
                data={
                    "severity": event.severity,
                    "action": event.action,
                    "event_data": event.data,
                },
                status=event.action if event.action != "LOG" else "success",
            )
        except Exception as e:
            logger.error(f"❌ Failed to log event: {e}")

    def get_services_status(self) -> Dict[str, Any]:
        """Get current status of managed services.

        Returns:
            Dict with orchestrator status and service health.
        """
        if self.started_at:
            uptime = (datetime.now() - self.started_at).total_seconds()
        else:
            uptime = 0

        return {
            "orchestrator": {"running": self.running, "uptime_seconds": uptime},
            "services": {
                "event_bridge": self._services_health.get("event_bridge", False),
                "watcher": self._services_health.get("watcher", False),
                "learning_capture": {
                    "active": self.learning_capture_active,
                    "pid": self.learning_capture_pid,
                    "health": self._services_health.get("learning_capture", False),
                },
            },
            "alerts": {
                "total_count": sum(self._service_alerts.values()),
                "alerts_by_type": self._service_alerts,
            },
            "last_health_check": self._last_health_check.isoformat()
            if self._last_health_check
            else None,
        }


async def main():
    """Entry point for running orchestrator."""
    import sys

    if len(sys.argv) < 2 or sys.argv[1] != "start":
        print("Usage: python unified_orchestrator.py start")
        return

    orchestrator = UnifiedOrchestrator()
    await orchestrator._start_async()


if __name__ == "__main__":
    asyncio.run(main())

# Singleton accessor for dashboard backend compatibility
_orchestrator_instance = None


def get_orchestrator():
    """Get singleton instance of UnifiedOrchestrator for dashboard backend compatibility."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedOrchestrator()
    return _orchestrator_instance
