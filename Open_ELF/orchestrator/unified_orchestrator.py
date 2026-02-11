#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Unified Orchestrator - Service Management and Event Processing

The Unified Orchestrator connects to EventBridge (port 9998) and:
- Listens to events: tool, message, error, failure, service, health
- Manages system services (Learning Capture, Sentinel)
- Autoservices on failure (restart Sentinel, restart Learning Capture)
- Escalates critical issues

Usage:
    python unified_orchestrator.py start

Dependencies:
    - EventBridge must be running on port 9998
    - Uses utils.event_logger for database logging
"""

import asyncio
import json
import logging
import subprocess
import sys
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import aiofiles

# Constants
OPENCODE_SERVER = "http://localhost:4096"
EVENT_BRIDGE_URL = "http://localhost:9998"
ELF_DIR = Path("/home/bamer/.opencode/emergent-learning")
OPEN_ELF_DIR = ELF_DIR / "Open_ELF"

# Path configuration
LEARNING_CAPTURE_SCRIPT = ELF_DIR / "scripts/background-learning-capture.py"
LEARNING_CAPTURE_LOG = OPEN_ELF_DIR / "logs/learning-capture.log"

# Escalation configuration for Sentinel → Orchestrator communication
ESCALATION_DIR = ELF_DIR / ".coordination" / "escalations"
CEO_INBOX_DIR = ELF_DIR / "ceo-inbox"

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnifiedOrchestrator")

# Event logging to database
_database_logging_available = False
try:
    from Open_ELF.utils.elf_logging import log_event as log_orchestrator_db

    _database_logging_available = True
    logger.info("✓ Database logging available")
except ImportError:
    logger.warning("⚠ Database logging unavailable")

# Watchdog for file watching
_watchdog_available = False
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    _watchdog_available = True
    logger.info("✓ Watchdog file watching available")
except ImportError:
    _watchdog_available = False
    logger.warning("⚠ Watchdog not available - escalation processing disabled")


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


class EscalationFileHandler(FileSystemEventHandler):
    """File system handler for Sentinel escalation files.

    Monitors .coordination/escalations/ directory for new escalation files from Sentinel.
    """

    def __init__(self, orchestrator: "UnifiedOrchestrator"):
        self.orchestrator = orchestrator

    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if not event.is_directory and event.src_path.endswith(".md"):
            # Extract just filename for logging
            filename = Path(event.src_path).name
            logger.info(f"📬 New escalation file detected: {filename}")
            # Schedule async processing in event loop (thread-safe)
            try:
                loop = self.orchestrator._event_loop
            except AttributeError:
                # Fallback: try to get running event loop
                try:
                    loop = asyncio.get_event_loop()
                    # Store reference for future use
                    self.orchestrator._event_loop = loop
                except RuntimeError:
                    # No event loop running - skip processing
                    logger.error(
                        "❌ No event loop available, cannot process escalation"
                    )
                    return

            # Schedule the coroutine in the event loop
            asyncio.run_coroutine_threadsafe(
                self.orchestrator.process_sentinel_escalation(event.src_path), loop
            )


class UnifiedOrchestrator:
    """Unified Orchestrator manages system services and processes events.

    The orchestrator connects to running EventBridge and:
    1. Registers as a listener for events
    2. Processes events asyncronously
    3. Manages service health (Learning Capture, Sentinel)
    4. Autoservices failed services
    5. Escalates critical issues
    """

    def __init__(self):
        self.running = False
        self.events: List[Event] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.bridge = None  # No EventBridge instance - we poll database instead
        self._event_loop = None  # Will be set in _start_async

        # Service tracking
        self.learning_capture_active = False
        self.learning_capture_pid: Optional[str] = None
        self.sentinel_pid: Optional[str] = None

        # Health tracking
        self._services_health: Dict[str, bool] = {}
        self._service_alerts: Dict[str, int] = {}
        self._last_health_check: Optional[datetime] = None
        self.started_at: Optional[datetime] = None

        # Event polling tracking
        self.last_event_timestamp: Optional[str] = None  # For polling event_chronicle

        # AI Analysis timing (Tier-based like sentinel/sentinel)
        self.main_loop_interval = 10  # seconds (basic cycle)
        self.ai_analysis_interval = 900  # seconds (15 minutes for AI analysis)
        self.cycle_count = 0

        # AgentManager integration
        self.agent_manager = None
        try:
            sys.path.insert(0, str(OPEN_ELF_DIR / "agents"))
            from agent_manager import AgentManager, get_agent_manager

            self.agent_manager = get_agent_manager()
            logger.info(
                "✅ AgentManager initialized successfully in UnifiedOrchestrator"
            )
        except Exception as e:
            logger.warning(f"⚠️ AgentManager not available: {e}")

        # Escalation processing
        self.escalation_observer = None
        self.processed_escalations = set()
        self.last_autonomous_check = datetime.now()

    async def process_sentinel_escalation(self, filepath: str):
        """Process a Sentinel escalation file from L1 agent."""
        escalation_file = Path(filepath)
        filename = escalation_file.name

        try:
            logger.info(f"📬 Processing Sentinel escalation: {filename}")

            if str(escalation_file) in self.processed_escalations:
                logger.debug(f"Already processed, skipping: {filename}")
                return

            async with aiofiles.open(escalation_file, mode="r") as f:
                content = await f.read()

            severity = "info"
            if "**Status:**" in content:
                status_line = [l for l in content.split("\n") if "**Status:**" in l][0]
                severity_text = status_line.lower()
                if "critical" in severity_text:
                    severity = "critical"
                elif "warning" in severity_text:
                    severity = "warning"

            self._log_to_sentinel_log(
                escalation_file,
                f"Processed (severity: {severity})",
                {"severity": severity},
            )
            self.processed_escalations.add(str(escalation_file))

            # 🔥 NEW: Forward to CEO inbox for L3 processing (not archive)
            await self._forward_to_ceo_inbox(escalation_file, content, severity)

            logger.info(f"✅ Sentinel escalation processed: {filename}")

        except Exception as e:
            logger.error(f"❌ Failed to process escalation {filename}: {e}")

    async def _forward_to_ceo_inbox(
        self, escalation_file: Path, content: str, severity: str
    ):
        """Forward escalation from Orchestrator to CEO inbox for L3 processing."""
        try:
            ceo_inbox = CEO_INBOX_DIR / "inbox"
            ceo_inbox.mkdir(parents=True, exist_ok=True)

            # Create CEO escalation with same filename (CEO monitor will pick it up)
            ceo_escalation_path = ceo_inbox / escalation_file.name

            # Add header indicating it's from Orchestrator
            ceo_content = f"""# CEO Escalation (from Orchestrator)
**Severity**: {severity}
**Forwarded At**: {datetime.now().isoformat()}
**Source File**: {escalation_file.name}

---

{content}
"""

            # Write to CEO inbox
            await asyncio.to_thread(ceo_escalation_path.write_text, ceo_content)
            logger.info(f"✅ Escalation forwarded to CEO inbox: {escalation_file.name}")

            # Archive the original from .coordination/escalations
            escalation_archive_dir = ESCALATION_DIR / "archive"
            escalation_archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = escalation_archive_dir / escalation_file.name
            await self._archive_escalation(escalation_file, archive_path)

        except Exception as e:
            logger.error(f"❌ Failed to forward escalation to CEO: {e}")

    def _log_to_sentinel_log(
        self, escalation_file: Path, action_taken: str, assessment: Dict[str, Any]
    ):
        """Log escalation processing to sentinel-log.md."""
        try:
            sentinel_log = ELF_DIR / ".coordination" / "sentinel-log.md"
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | STATUS: processed | NOTES: Processed escalation {escalation_file.name} | Action: {action_taken}\n"
            with open(sentinel_log, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"❌ Failed to log to sentinel-log.md: {e}")

    async def _archive_escalation(self, source_file: Path, target_file: Path):
        """Archive processed escalation file."""
        try:
            await asyncio.to_thread(source_file.rename, target_file)
        except Exception as e:
            logger.error(f"❌ Failed to archive escalation: {e}")

    async def _check_services_health_async(self) -> Dict[str, bool]:
        """Check health of all managed services asynchronously."""
        health_status = {
            "event_bridge": False,
            "sentinel": False,
            "learning_capture": False,
        }

        try:
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            health_status["event_bridge"] = response.status_code == 200
        except:
            pass

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["pgrep", "-f", "core/sentinel.py"],
                capture_output=True,
                text=True,
            )
            health_status["sentinel"] = result.stdout.strip() != ""
        except:
            pass

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["pgrep", "-f", "background-learning-capture.py"],
                capture_output=True,
                text=True,
            )
            health_status["learning_capture"] = result.stdout.strip() != ""
        except:
            pass

        self._services_health = health_status
        self._last_health_check = datetime.now()
        return health_status

    async def _run_autonomous_system_checks(self):
        """Run autonomous system checks every 15 minutes."""
        while self.running:
            try:
                logger.info("🤖 Running autonomous system checks (Level 2)")

                service_health = await self._check_services_health_async()
                learnings_count = self._count_recent_learnings()
                heuristics_count = self._count_recent_heuristics()

                # Check database integrity
                db_integrity = await self._check_database_integrity()

                self._log_autonomous_checks(
                    {
                        "service_health": service_health,
                        "learnings_count": learnings_count,
                        "heuristics_count": heuristics_count,
                        "database_integrity": db_integrity,
                        "time_since_last_check_hours": 0.25,
                    }
                )

                logger.info(
                    f"✅ Autonomous checks completed: "
                    f"services={sum(1 for s in service_health.values() if s)}/3, "
                    f"db_integrity={'✓' if db_integrity.get('valid') else '✗'}"
                )

            except Exception as e:
                logger.error(f"❌ Error in autonomous system checks: {e}")

            await asyncio.sleep(900)

    async def _check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity and auto-fix if needed.

        Returns:
            Dict with integrity status and any actions taken
        """
        result = {
            "valid": True,
            "errors": [],
            "action_taken": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Import migrations module
            import importlib.util
            import sys

            migrations_path = ELF_DIR / "query" / "migrations.py"
            if not migrations_path.exists():
                logger.warning(
                    "⚠️  Migrations module not found, skipping DB integrity check"
                )
                return result

            spec = importlib.util.spec_from_file_location(
                "migrations", str(migrations_path)
            )
            migrations = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migrations)

            # Get database path
            db_path = migrations.get_db_path()

            if not db_path.exists():
                logger.info("ℹ️  Database doesn't exist yet, skipping integrity check")
                return result

            # Check integrity
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            try:
                is_valid, errors = migrations.check_integrity(conn)
                result["valid"] = is_valid
                result["errors"] = errors

                if not is_valid:
                    logger.warning(
                        f"⚠️  Database integrity issues detected: {len(errors)} errors"
                    )
                    for error in errors[:3]:  # Log first 3 errors
                        logger.warning(f"   - {error[:100]}...")

                    # Try to fix with REINDEX first
                    logger.info("🔧 Attempting to fix with REINDEX...")
                    try:
                        cursor = conn.cursor()
                        cursor.execute("REINDEX")
                        conn.commit()

                        # Check again
                        is_valid_after, errors_after = migrations.check_integrity(conn)
                        if is_valid_after:
                            logger.info("✅ Database integrity fixed with REINDEX")
                            result["action_taken"] = "REINDEX fixed"
                            result["valid"] = True
                            result["errors"] = []
                        else:
                            # REINDEX didn't work, need full rebuild
                            logger.error("❌ REINDEX failed to fix integrity issues")
                            logger.error(
                                "⚠️  Database requires full rebuild - scheduling rebuild"
                            )

                            # Schedule rebuild for next cycle (don't do it synchronously)
                            result["action_taken"] = "rebuild_required"
                            result["valid"] = False

                            # Log to database if available
                            if _database_logging_available:
                                log_orchestrator_db(
                                    event_type="database_integrity_failure",
                                    source="unified_orchestrator",
                                    summary=f"Database integrity check failed with {len(errors)} errors",
                                    data={
                                        "errors": errors,
                                        "db_path": str(db_path),
                                        "rebuild_required": True,
                                    },
                                    status="critical",
                                )

                            # Create escalation for critical DB issues
                            await self._escalate_database_corruption(errors)

                    except Exception as fix_error:
                        logger.error(
                            f"❌ Error attempting to fix database: {fix_error}"
                        )
                        result["action_taken"] = f"fix_failed: {str(fix_error)}"
                        result["valid"] = False
                else:
                    logger.debug("✓ Database integrity check passed")

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"❌ Error checking database integrity: {e}")
            result["valid"] = False
            result["errors"] = [str(e)]
            result["action_taken"] = "check_failed"

        return result

    async def _escalate_database_corruption(self, errors: List[str]):
        """Escalate database corruption to CEO inbox.

        Args:
            errors: List of integrity check errors
        """
        try:
            ceo_inbox = CEO_INBOX_DIR / "inbox"
            ceo_inbox.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            escalation_path = ceo_inbox / f"orchestrator_db_corruption_{timestamp}.md"

            error_details = "\n".join([f"- {err[:200]}" for err in errors[:5]])

            content = f"""# 🔴 CRITICAL: Database Corruption Detected

**Source**: UnifiedOrchestrator (Level 2)  
**Severity**: critical  
**Detected At**: {datetime.now().isoformat()}  
**Component**: SQLite Database Integrity

## Summary

Database integrity check failed with {len(errors)} error(s). Automatic REINDEX did not resolve the issue.

## Errors Detected

{error_details}

## Auto-Remediation Attempted

1. ✅ Integrity check performed
2. ✅ REINDEX executed
3. ❌ REINDEX failed to resolve corruption
4. ⏳ Full rebuild required

## Recommended Actions

### Immediate (CEO Decision Required)

1. **Schedule Maintenance Window** - Database rebuild requires brief downtime
2. **Approve Database Rebuild** - Run `python3 scripts/rebuild_corrupted_db.py`
3. **Verify Data After Rebuild** - Check critical tables for data integrity

### Scripts Available

```bash
# Rebuild database (creates backup automatically)
cd {ELF_DIR}
python3 scripts/rebuild_corrupted_db.py

# Verify integrity after rebuild
python3 -c "import sqlite3; conn = sqlite3.connect('memory/index.db'); cursor = conn.cursor(); cursor.execute('PRAGMA integrity_check'); print('Integrity:', cursor.fetchall()); conn.close()"
```

## Impact Assessment

- **Data at Risk**: Learnings, heuristics, events, escalations
- **Services Affected**: Query system, EventBridge logging, Learning Capture
- **Auto-Recovery**: Not possible without CEO approval
- **Downtime Required**: ~2-5 minutes for rebuild

---

**Orchestrator Instructions**: CEO approval required for database rebuild. Do not proceed without explicit authorization.
"""

            # Write escalation file
            await asyncio.to_thread(escalation_path.write_text, content)
            logger.error(
                f"🔴 Database corruption escalated to CEO: {escalation_path.name}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to escalate database corruption: {e}")

    def _count_recent_learnings(self) -> int:
        """Count learnings in last hour."""
        try:
            import sqlite3

            db = Path.home() / ".opencode/emergent-learning/memory/index.db"
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM learnings WHERE timestamp > datetime('now', '-1 hour')"
            )
            count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _count_recent_heuristics(self) -> int:
        """Count heuristics in last 24 hours."""
        try:
            import sqlite3

            db = Path.home() / ".opencode/emergent-learning/memory/index.db"
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM heuristics WHERE created_at > datetime('now', '-1 day')"
            )
            count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _log_autonomous_checks(self, checks: Dict[str, Any]):
        """Log autonomous system checks to sentinel-log.md."""
        try:
            sentinel_log = ELF_DIR / ".coordination" / "sentinel-log.md"
            log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | STATUS: autonomous-check | NOTES: L2 check | EventBridge: {checks['service_health'].get('event_bridge')} | Sentinel: {checks['service_health'].get('sentinel')} | Learning: {checks['service_health'].get('learning_capture')} | Learnings: {checks['learnings_count']} | Heuristics: {checks['heuristics_count']}\n"
            with open(sentinel_log, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"❌ Failed to log autonomous checks: {e}")

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
        # Store reference to running event loop for escalation sentinel
        self._event_loop = asyncio.get_running_loop()

        # 1. Connect to existing EventBridge
        if not self._connect_to_eventbridge():
            return

        # 2. Register as listener
        self._register_listeners()

        # 3. Start event processor
        processor = asyncio.create_task(self._process_events())
        logger.info("⚙️  Event processor started")

        # 4. Start escalation file sentinel
        if _watchdog_available:
            self.escalation_observer = Observer()
            event_handler = EscalationFileHandler(self)
            ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
            self.escalation_observer.schedule(
                event_handler, path=str(ESCALATION_DIR), recursive=False
            )
            self.escalation_observer.start()
            logger.info("📂 Escalation file sentinel started")
        else:
            logger.warning("⚠️ Escalation processing not available (watchdog missing)")

        # 5. Start periodic autonomous checks
        # (separate task that runs every 15 minutes)
        autonomous_checker = asyncio.create_task(self._run_autonomous_system_checks())
        logger.info("🤖 Autonomous system checks started (every 15 min)")

        # Main loop with AI Analysis tiers
        tick = 0
        try:
            while self.running:
                tick += 1
                self.cycle_count += 1

                # Poll event_chronicle for new events (every 2 ticks = 20 seconds)
                if tick % 2 == 0:
                    events = self._poll_events_from_database()
                    if events > 0:
                        logger.info(f"📊 Poll event_chronicle: {events} new events")

                # Health check (every 10 ticks = 100 seconds)
                if tick % 10 == 0:
                    logger.info(f"⏰ Tick #{tick}")
                    self._check_services_health()

                # AI Analysis (every AI Analysis Interval)
                should_run_ai = (
                    self.cycle_count
                    % (self.ai_analysis_interval // self.main_loop_interval)
                ) == 0  # = 900/10 = 90 cycles

                if should_run_ai and self.agent_manager:
                    logger.info("🤖 Running AI analysis cycle via AgentManager")
                    self._analyze_with_ai()
                else:
                    if not self.agent_manager and tick % 10 == 0:
                        logger.info(
                            "📋 Running basic health check (AgentManager unavailable)"
                        )

                await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")

        # Cleanup
        processor.cancel()

        if self.escalation_observer:
            self.escalation_observer.stop()
            logger.info("✅ Escalation file sentinel stopped")

        autonomous_checker.cancel()
        logger.info("✅ Autonomous system checks stopped")

        logger.info("✅ Unified Orchestrator stopped")

    def _connect_to_eventbridge(self) -> bool:
        """Check if EventBridge is running.

        UnifiedOrchestrator polls event_chronicle for events instead of connecting
        via callbacks. No EventBridge instance is created.

        Returns:
            True if EventBridge is running, False otherwise.
        """
        try:
            # Just check if EventBridge is running via HTTP API
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            if response.status_code != 200:
                logger.error(f"❌ EventBridge returned status {response.status_code}")
                return False

            logger.info(f"✅ EventBridge is running ({EVENT_BRIDGE_URL}/status)")
            logger.info("📊 UnifiedOrchestrator will poll event_chronicle for events")

            # No bridge instance created - we poll event_chronicle instead
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to EventBridge: {e}")
            logger.error(
                f"\nMake sure EventBridge is running:\n"
                f"  cd {ELF_DIR / 'core'}\n"
                f"  python event_bridge_v2.py start"
            )
            return False

    def _register_listeners(self):
        """Register with global EventBridge v2 listener registry."""
        logger.info("📡 Registering with EventBridge v2 global listeners")
        try:
            # Import the global listener functions from event_bridge_v2
            from core.event_bridge_v2 import register_global_listener

            # Register our callback directly with EventBridge v2
            register_global_listener(
                listener_id="unified_orchestrator",
                callback=self._on_event_received_sync,
                event_types=["tool", "message", "error", "failure", "service", "health"]
            )
            logger.info("✅ Registered for events via EventBridge v2 global listeners")
        except Exception as e:
            logger.error(f"❌ Failed to register listeners: {e}")

    def _on_event_received_sync(self, event_data: Dict):

    def _poll_events_from_database(self) -> int:
        """Poll event_chronicle for new events.

        Returns:
            Number of new events processed.

        Polling is safer than callbacks - no EventBridge instance created,
        no duplicate logs from __init__, and orchestrator is independent.
        """
        import sqlite3

        db_path = ELF_DIR / "memory" / "index.db"
        if not db_path.exists():
            return 0

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        events_processed = 0

        try:
            cursor.execute(
                """
                SELECT id, timestamp, event_type, source, summary, data, status
                FROM event_chronicle
                WHERE created_at > COALESCE(?, datetime('1970-01-01'))
                ORDER BY created_at ASC
                LIMIT 100
            """,
                (self.last_event_timestamp,),
            )

            for row in cursor.fetchall():
                event_id, timestamp, event_type, source, summary, data, status = row

                try:
                    data_dict = json.loads(data) if data else {}
                except:
                    data_dict = {}

                event_data = {
                    "type": event_type,
                    "properties": data_dict,
                    "severity": self._map_status_to_severity(status),
                }

                event = Event(
                    id=str(event_id),
                    type=event_type,
                    severity=self._get_severity(event_data),
                    source=source,
                    data=data_dict,
                    timestamp=datetime.now(),
                )

                try:
                    loop = self._event_loop
                    asyncio.run_coroutine_threadsafe(self.event_queue.put(event), loop)
                    events_processed += 1
                except Exception:
                    pass

            if events_processed > 0:
                cursor.execute("SELECT MAX(created_at) FROM event_chronicle")
                result = cursor.fetchone()
                if result and result[0]:
                    self.last_event_timestamp = result[0]

        except Exception as e:
            logger.debug(f"Error polling events: {e}")
        finally:
            conn.close()

        return events_processed

    def _map_status_to_severity(self, status: str) -> str:
        """Map event_chronicle status to severity."""
        if status == "success":
            return "info"
        elif status == "error" or status == "failure":
            return "error"
        elif status == "warning":
            return "warning"
        return "info"

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

        # Sentinel
        elif "sentinel" in service_lower:
            if status.lower() in ["down", "inactive", "stopped", "failed"]:
                logger.info("🔄 Attempting to restart Sentinel...")
                self._restart_sentinel()

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

    def _restart_sentinel(self) -> bool:
        """Restart Sentinel service.

        Returns:
            True if restarted successfully, False otherwise.
        """
        try:
            # Kill existing
            subprocess.run(["pkill", "-f", "core/sentinel.py"], capture_output=True)
            import time

            time.sleep(2)

            # Start new
            process = subprocess.Popen(
                ["python3", str(ELF_DIR / "core" / "sentinel.py")],
                cwd=str(OPEN_ELF_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            time.sleep(3)

            # Verify
            check = subprocess.run(
                ["pgrep", "-f", "core/sentinel.py"],
                capture_output=True,
                text=True,
            )
            if check.returncode == 0:
                logger.info("✅ Sentinel restarted successfully")
                return True

            logger.error("❌ Failed to restart Sentinel")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting Sentinel: {e}")
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
        if _database_logging_available:
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
            health_status: Status dict with keys: event_bridge, sentinel, learning_capture
        """
        health_status = {
            "event_bridge": False,
            "sentinel": False,
            "learning_capture": False,
        }

        # EventBridge (HTTP)
        try:
            response = requests.get(f"{EVENT_BRIDGE_URL}/status", timeout=2)
            health_status["event_bridge"] = response.status_code == 200
        except:
            logger.error(f'❌ Failed health_status["event_bridge"]')
            pass

        # Sentinel (pgrep)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "core/sentinel.py"],
                capture_output=True,
                text=True,
            )
            health_status["sentinel"] = result.returncode == 0
            if result.returncode == 0:
                self.sentinel_pid = result.stdout.strip()
        except:
            logger.error(f'❌ Failed health_status["sentinel"]')
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

    def _analyze_with_ai(self):
        """AI-powered analysis of system state via AgentManager."""
        if not self.agent_manager:
            logger.warning("AgentManager not available for AI analysis")
            return

        try:
            # Call unified-orchestrator agent via AgentManager
            # The AI Agent now receives the DB integrity check and decides what to do

            result = self.agent_manager.ask_agent(
                "unified-orchestrator",
                f"""Analyze the system state and take all appropriate actions based on your mission, your position and the level of severity if needed.

{datetime.now().strftime("%d/%m/%Y %H:%M")}

INSTRUCTIONS:
1. Check for any other system defects or issues : database integrity, events processed, service health, sentinel up and running, CEO up and running, eventBridge, learning processor, Semantic Embeding, Learning Capture, Heuristique persisted, trails pheromone, trails tails,uptime_seconds,...
2. Attempt to fix any issue in your level of severity competence, mission and position. 
3. If you attempt to fix the issues have fail, you have to escalate to CEO.
4. Recommend specific actions to take if needed.

   Be concise but thorough.""",
            )

            if result.get("success"):
                logger.info(
                    f"✅ AI Agent analysis completed: {result.get('response', '')[:100]}..."
                )

            else:
                logger.error(
                    f"❌ AI analysis failed: {result.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"❌ Error in AI analysis: {e}")

    def _format_state_for_ai(self, state: Dict) -> str:
        """Format system state for AI analysis."""
        services = state.get("services_health", {})
        db_integrity = state.get("database_integrity", {})

        db_status = "✅ Valid"
        if not db_integrity.get("valid"):
            db_status = f"❌ Corrupted ({len(db_integrity.get('errors', []))} errors)"

        return f"""
System Health Summary:
- EventBridge: {"✅ Running" if services.get("event_bridge") else "❌ Down"}
- Sentinel: {"✅ Running" if services.get("sentinel") else "❌ Down"}
- Learning Capture: {"✅ Running" if services.get("learning_capture") else "❌ Down"}
- Database Integrity: {db_status}
- Events Processed: {state.get("events_processed", 0)}
- Uptime: {state.get("uptime_seconds", 0):.0f} seconds
- Cycle Count: {state.get("cycle_count", 0)}
"""

    def _log_event(self, event: Event):
        """Log event to database.

        Args:
            event: Event to log
        """
        if not _database_logging_available:
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
                "sentinel": self._services_health.get("sentinel", False),
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
