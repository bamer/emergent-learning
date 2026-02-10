#!/usr/bin/env python3
"""
Unified Orchestrator - Service Management and Event Processing

The Unified Orchestrator connects to EventBridge (port 9998) and:
- Listens to events: tool, message, error, failure, service, health
- Manages system services (Learning Capture, Watcher)
- Autoservices on failure (restart Watcher, restart Learning Capture)
- Escalates critical issues
- Processes Watcher escalations from .coordination/escalations/

Usage:
    python unified_orchestrator.py start

Dependencies:
     - EventBridge must be running on port 9998
     - utils.event_logger for database logging
     - watchdog for file watching escalations
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

# NEW: Escalation directory for Watcher → Orchestrator communication
ESCALATION_DIR = ELF_DIR / ".coordination" / "escalations"
CEO_INBOX_DIR = ELF_DIR / "ceo-inbox"

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnifiedOrchestrator")

# Event logging to database
try:
    from Open_ELF.utils.elf_logging import (
        log_event as log_orchestrator_db,
        get_logger,
        log_info,
        log_warning,
        log_error,
    )

    DATABASE_LOGGING_AVAILABLE = True
    logger.info("✓ Database logging available")
except ImportError:
    try:
        from utils.event_logger import log_event as log_orchestrator_db
        from utils.event_logger import get_logger, log_info, log_warning, log_error

        DATABASE_LOGGING_AVAILABLE = True
        logger.info("✓ Database logging available (legacy import)")
    except ImportError:
        DATABASE_LOGGING_AVAILABLE = False
        logger.warning("⚠ Database logging unavailable")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
    logger.info("✓ Watchdog file watching available")
except ImportError:
    WATCHDOG_AVAILABLE = False
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
        """File system handler for Watcher escalation files.

        Monitors .coordination/escalations/ directory for new escalation files from Watcher.
        """

        def __init__(self, orchestrator: "UnifiedOrchestrator"):
            self.orchestrator = orchestrator

        def on_created(self, event):
            """Called when a file is created in the watched directory."""
            if not event.is_directory and event.src_path.endswith(".md"):
                # Extract just filename for logging
                filename = Path(event.src_path).name
                logger.info(f"📬 New escalation file detected: {filename}")
                # Schedule async processing
                asyncio.create_task(
                    self.orchestrator.process_watcher_escalation(event.src_path)
                )

    class UnifiedOrchestrator:
        """Unified Orchestrator manages system services and processes events.

        The orchestrator connects to running EventBridge and:
        1. Registers as a listener for events
        2. Processes events asyncronously
        3. Manages service health (Learning Capture, Watcher)
        4. Autoservices failed services
        5. Escalates critical issues
        6. Processes Watcher escalations from L1 → L3
        """

        def __init__(self):
            self.running = False
            self.events: List[Event] = []
            self.event_queue: asyncio.Queue = asyncio.Queue()
            self.bridge = (
                None  # EventBridge instance (don't create, connect to existing)
            )

            # Service tracking
            self.learning_capture_active = False
            self.learning_capture_pid = None
            self.watcher_pid = None

            # Alert tracking (number of times in row)
            self._service_alerts: Dict[str, int] = {}

            # AI Analysis
            self.main_loop_interval = 10  # seconds
            self.ai_analysis_interval = 900  # seconds (15 minutes)
            self.cycle_count = 0
            self.started_at = None
            self.last_autonomous_check = datetime.now()

            # AgentManager for AI analysis
            self.agent_manager = None
            try:
                from Open_ELF.agents.agent_manager import AgentManager

                self.agent_manager = AgentManager()
                logger.info("✅ AgentManager initialized for Orchestrator")
            except ImportError:
                logger.warning("⚠️ AgentManager not available")

            # Escalation processing
            self.escalation_observer = None
            self.processed_escalations = set()

            # Status tracking
            self._services_health: Dict[str, bool] = {}
            self._last_health_check: Optional[datetime] = None

    def start(self) -> bool:
        """Start orchestrator synchronously (for dashboard compatibility)."""
        return asyncio.run(self._start_async())

    async def _start_async(self):
        """Start orchestrator and connect to EventBridge."""
        logger.info("=" * 60)
        logger.info("🚀 Unified Orchestrator Starting")
        logger.info("=" * 60)

        self.running = True
        self.started_at = datetime.now()

        # 1. Connect to existing EventBridge
        if not await self._connect_to_eventbridge():
            return

        # 2. Register as listener
        self._register_listeners()

        # 3. Start event processor
        processor = asyncio.create_task(self._process_events())
        logger.info("⚙️  Event processor started")

        # 4. NEW: Start escalation file watcher
        if WATCHDOG_AVAILABLE:
            self.escalation_observer = Observer()
            event_handler = EscalationFileHandler(self)
            ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
            self.escalation_observer.schedule(
                event_handler, path=str(ESCALATION_DIR), recursive=False
            )
            self.escalation_observer.start()
            logger.info("📂 Escalation file watcher started")
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

                # Health check (every 10 ticks = 100 seconds)
                if tick % 10 == 0:
                    logger.info(f"⏰ Tick #{tick}")
                    await self._check_services_health()

                # AI Analysis (every AI Analysis Interval)
                should_run_ai = (
                    self.cycle_count
                    % (self.ai_analysis_interval // self.main_loop_interval)
                ) == 0  # = 900/10 = 90 cycles

                if should_run_ai and self.agent_manager:
                    logger.info("🤖 Running AI analysis cycle via AgentManager")
                    await self._analyze_with_ai()
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
            logger.info("✅ Escalation file watcher stopped")

        autonomous_checker.cancel()
        logger.info("✅ Autonomous system checks stopped")

        logger.info("✅ Unified Orchestrator stopped")

    async def _connect_to_eventbridge(self) -> bool:
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

    async def process_watcher_escalation(self, filepath: str):
        """Process a Watcher escalation file from L1 agent.

        This is the core of the L1 → L2 escalation flow:
        1. Read and parse the escalation file
        2. Extract the "Orchestrator Instructions"
        3. Perform autonomous assessment
        4. Take appropriate actions
        5. If critical, escalate to CEO (L3)
        6. Document all actions taken

        Args:
            filepath: Path to the escalation file
        """
        escalation_file = Path(filepath)
        filename = escalation_file.name

        try:
            logger.info(f"📬 Processing Watcher escalation: {filename}")

            # Skip if already processed
            if str(escalation_file) in self.processed_escalations:
                logger.debug(f"  Already processed, skipping: {filename}")
                return

            # Read escalation file
            async with aiofiles.open(escalation_file, mode="r") as f:
                content = await f.read()

            # Extract status and severity from the file
            escalation_status = "unknown"
            severity = "info"
            if "**Status:**" in content:
                status_line = [l for l in content.split("\n") if "**Status:**" in l][0]
                escalation_status = status_line.split("**Status:**")[1].strip()
                if escalation_status:
                    severity_text = status_line.lower()
                    if "critical" in severity_text:
                        severity = "critical"
                    elif "warning" in severity_text:
                        severity = "warning"

            # Extract "Orchestrator Instructions" section if present
            orchestrator_section = ""
            if "## Orchestrator Instructions" in content:
                sections = content.split("## Orchestrator Instructions")
                if len(sections) > 1:
                    orchestrator_section = sections[1].strip()

            # Perform autonomous assessment
            autonomous_result = await self._perform_autonomous_assessment(
                escalation_file, content, severity
            )

            # Take appropriate actions based on severity and assessment
            action_taken = "Logged and assessed"
            if severity == "critical" and autonomous_result.get(
                "requires_ceo_escalation"
            ):
                # L2 → L3 escalation
                ceo_escalation_file = await self._escalate_to_ceo(
                    escalation_file, content, autonomous_result
                )
                action_taken = f"Escalated to CEO: {ceo_escalation_file}"

            # Document to watcher-log.md
            self._log_to_watcher_log(escalation_file, action_taken, autonomous_result)

            # Mark as processed to avoid duplicate processing
            self.processed_escalations.add(str(escalation_file))

            # Move processed escalation to archive
            escalation_archive_dir = ESCALATION_DIR / "archive"
            escalation_archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = escalation_archive_dir / filename

            await self._archive_escalation(escalation_file, archive_path)

            logger.info(f"✅ Watcher escalation processed: {filename}")
            logger.info(f"   Action taken: {action_taken}")

        except Exception as e:
            logger.error(f"❌ Failed to process Watcher escalation {filename}: {e}")
            # Log error to database
            if DATABASE_LOGGING_AVAILABLE:
                log_orchestrator_db(
                    event_type="escalation_error",
                    source="unified_orchestrator",
                    summary=f"Failed to process escalation: {filename}",
                    status="error",
                    data={"error": str(e), "escalation_file": str(escalation_file)},
                )

    async def _perform_autonomous_assessment(
        self, escalation_file: Path, content: str, severity: str
    ) -> Dict[str, Any]:
        """Perform autonomous assessment of the Watcher escalation.

        This includes:
        1. Analyzing the Watcher's analysis
        2. Performing own system checks
        3. Using AgentManager for deeper analysis if critical
        4. Determining required actions

        Args:
            escalation_file: Path to escalation file
            content: Content of escalation file
            severity: Severity level

        Returns:
            Dictionary with assessment results
        """
        assessment = {
            "severity": severity,
            "escalation_file": str(escalation_file),
            "watcher_status": content,
            "orchestrator_assessment": "pending",
            "service_health": {},
            "anomalies_detected": [],
            "actions_taken": [],
            "requires_ceo_escalation": False,
        }

        try:
            # 1. Get current system state
            service_health = await self._check_services_health_async()
            assessment["service_health"] = service_health

            # 2. Check for critical service failures
            critical_services = []
            for service, healthy in service_health.items():
                if not healthy:
                    critical_services.append(service)
                    assessment["anomalies_detected"].append(
                        f"CRITICAL: {service} is down"
                    )

            # 3. If critical or explicit anomaly flagged, use AgentManager
            if (
                severity == "critical"
                or "CRITICAL" in content.upper()
                or "critical" in content.lower()
            ):
                assessment = await self._analyze_with_agent_manager(
                    escalation_file, assessment
                )

            # 4. Set orchestrator assessment status
            assessment["orchestrator_assessment"] = "completed"

            # 5. Determine if CEO escalation is needed
            assessment["requires_ceo_escalation"] = (
                severity == "critical"
                or assessment.get("requires_ceo") is True
                or len(assessment.get("critical_actions", [])) > 0
            )

            logger.info(
                f"🔍 Autonomous assessment completed: "
                f"severity={severity}, "
                f"anomalies={len(assessment['anomalies_detected'])}, "
                f"ceo_escalation={assessment['requires_ceo_escalation']}"
            )

        except Exception as e:
            logger.error(f"❌ Error in autonomous assessment: {e}")
            assessment["orchestrator_assessment"] = "failed"

        return assessment

    async def _analyze_with_agent_manager(
        self, escalation_file: Path, base_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze escalation using AgentManager for deeper analysis.

        Args:
            escalation_file: Path to escalation file
            base_assessment: Base assessment results

        Returns:
            Enhanced assessment with AgentManager insights
        """
        if not self.agent_manager:
            logger.warning("AgentManager not available, using basic assessment")
            return base_assessment

        try:
            # Prepare system context for AgentManager
            system_context = f"""
Watcher Escalation: {escalation_file.name}

Orchestrator Assessment:
{base_assessment.get("orchestrator_assessment", "pending")}

Service Health:
{json.dumps(base_assessment.get("service_health", {}), indent=2)}

Anomalies Detected:
{chr(10).join(f"  - {a}" for a in base_assessment["anomalies_detected"])}
""".strip()

            # Call AgentManager with detailed prompt
            result = await asyncio.to_thread(
                self.agent_manager.ask_agent,
                "unified_orchestrator",
                f"""As the Level 2 Agent, analyze this Watcher escalation and determine:

1. What is the actual problem (not just symptoms)?
2. Can this be resolved autonomously?
3. What specific actions should be taken?
4. Is this critical enough to require CEO (L3) escalation?

{system_context}

Provide your analysis in this format:
ACTUAL_PROBLEM: [your analysis]
AUTONOMOUS_RESOLUTION: [steps we can take autonomously]
CRITICAL_ACTIONS: [if any, mark requires_ceo_escalation]
RECOMMENDATION: [your recommendation]
""",
            )

            if result.get("success"):
                response = result.get("response", "")
                logger.info(f"🎯 AgentManager analysis completed: {response[:200]}...")

                # Parse AgentManager response
                lines = response.strip().split("\n")
                agent_analysis = {
                    "agent_manager_analysis": "completed",
                    "analysis_text": response,
                    "autonomous_resolution": [],
                    "critical_actions": [],
                    "recommendation": "",
                }

                for line in lines:
                    if line.startswith("ACTUAL_PROBLEM:"):
                        agent_analysis["actual_problem"] = line[
                            len("ACTUAL_PROBLEM:") :
                        ].strip()
                    elif line.startswith("AUTONOMOUS_RESOLUTION:"):
                        agent_analysis["autonomous_resolution"] = [
                            line[len("AUTONOMOUS_RESOLUTION:") :].strip()
                        ]
                    elif line.startswith("CRITICAL_ACTIONS:"):
                        if "requires_ceo" in line.lower():
                            agent_analysis["requires_ceo"] = True
                        agent_analysis["critical_actions"].append(
                            line[len("CRITICAL_ACTIONS:") :].strip()
                        )
                    elif line.startswith("RECOMMENDATION:"):
                        agent_analysis["recommendation"] = line[
                            len("RECOMMENDATION:") :
                        ].strip()

                # Merge into base assessment
                base_assessment.update(agent_analysis)

                # Update actions based on resolution
                if agent_analysis.get("autonomous_resolution"):
                    base_assessment["actions_taken"] = agent_analysis[
                        "autonomous_resolution"
                    ]

                # Update CEO escalation flag
                if agent_analysis.get("critical_actions") or agent_analysis.get(
                    "requires_ceo"
                ):
                    base_assessment["requires_ceo_escalation"] = True

            else:
                logger.error(
                    f"❌ AgentManager analysis failed: {result.get('error', 'Unknown')}"
                )

        except Exception as e:
            logger.error(f"❌ Error in AgentManager analysis: {e}")

        return base_assessment

    async def _escalate_to_ceo(
        self,
        watcher_escalation_file: Path,
        watcher_content: str,
        assessment: Dict[str, Any],
    ) -> str:
        """Create a CEO escalation file based on Orchestrator's assessment.

        This is L2 → L3 escalation.

        Args:
            watcher_escalation_file: Original Watcher escalation file
            watcher_content: Original Watcher escalation content
            assessment: Orchestrator's assessment

        Returns:
            Path to created CEO escalation file
        """
        try:
            CEO_INBOX_DIR.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            ceo_id = f"orchestrator_esc_{timestamp}"

            # Create CEO escalation file
            ceo_file = CEO_INBOX_DIR / f"{ceo_id}.md"

            content = f"""# CEO Escalation: {ceo_id}

**Source:** Orchestrator (Level 2)
**Original Watcher Escalation:** {watcher_escalation_file.name}
**Time:** {datetime.now().isoformat()}
**Priority:** Critical

---

## Summary

Watcher (Level 1) has escalated with the following details:

---

### Watcher's Original Concern
{watcher_content}

---

### Orchestrator's Analysis

#### System Health Assessment
```
JSON Output:
{self._format_service_health_for_ceo()}
```

#### Autonomous Analysis
**AgentManager Analysis:**
- {self._extract_agent_analysis_summary(assessment)}

#### Orchestrator Assessment
- Orchestrator reviewed the escalation and determined CEO intervention is required.

---

### Critical Actions Required
"""

            await aiofiles.open(ceo_file, mode="w").write(content)

            # Log to database
            if DATABASE_LOGGING_AVAILABLE:
                log_orchestrator_db(
                    event_type="escalation_to_ceo",
                    source="unified_orchestrator",
                    summary=f"Orchestrator escalated to CEO: {ceo_id}",
                    status="escalated",
                    data={
                        "ceo_escalation_id": ceo_id,
                        "original_escalation": str(watcher_escalation_file),
                        "orchestrator_assessment": assessment.get(
                            "orchestrator_assessment"
                        ),
                        "severity": assessment.get("severity"),
                    },
                )

                logger.info(f"✅ Created CEO escalation: {ceo_file}")
            return str(ceo_file)

        except Exception as e:
            logger.error(f"❌ Failed to create CEO escalation: {e}")
            return ""

    def _format_service_health_for_ceo(self) -> str:
        """Format service health for CEO escalation."""
        if not self._services_health:
            return "No health data available"

        lines = ["System Health:"]
        for service, healthy in self._services_health.items():
            lines.append(f"  - {service}: {'✅ Running' if healthy else '❌ Down'}")
        return "\n".join(lines)

    def _extract_agent_analysis_summary(self, assessment: Dict) -> str:
        """Extract AgentManager analysis summary for CEO escalation."""
        summary_parts = []

        if assessment.get("actual_problem"):
            summary_parts.append(f"**Problem:** {assessment['actual_problem']}")

        if assessment.get("autonomous_resolution"):
            resolution = "\n".join(
                [f"  - {r}" for r in assessment.get("autonomous_resolution", [])]
            )
            resolution = f"**Attempted Resolution:**\n{resolution}"
            summary_parts.append(resolution)

        if assessment.get("critical_actions"):
            critical = "\n".join(
                [f"  - {c}" for c in assessment.get("critical_actions", [])]
            )
            critical = f"**Critical Actions:**\n{critical}"
            summary_parts.append(critical)

        if assessment.get("recommendation"):
            summary_parts.append(f"**Recommendation:** {assessment['recommendation']}")

        return "\n\n".join(summary_parts)

    def _log_to_watcher_log(
        self, escalation_file: Path, action_taken: str, assessment: Dict[str, Any]
    ):
        """Log escalation processing to watcher-log.md."""
        try:
            watcher_log = ELF_DIR / ".coordination" / "watcher-log.md"

            log_entry = f"""{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | STATUS: processed | NOTES: Orchestrator processed escalation {escalation_file.name} | Action: {action_taken}

"""
            # Append to watcher log
            with open(watcher_log, "a") as f:
                f.write(log_entry)

            logger.debug(f"📝 Logged to watcher-log.md")

        except Exception as e:
            logger.error(f"❌ Failed to log to watcher-log.md: {e}")

    async def _archive_escalation(self, source_file: Path, target_file: Path):
        """Archive processed escalation file."""
        try:
            await asyncio.to_thread(source_file.rename, target_file)
            logger.debug(f"📁 Archived escalation to: {target_file}")
        except Exception as e:
            logger.error(f"❌ Failed to archive escalation: {e}")

    async def _check_services_health_async(self) -> Dict[str, bool]:
        """Check health of all managed services asynchronously.

        Returns:
            Dictionary with service names as keys and health status as values
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
            pass

        # Watcher (pgrep)
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["pgrep", "-f", "core/watcher.py"],
                capture_output=True,
                text=True,
            )
            health_status["watcher"] = result.stdout.strip() != ""
        except:
            pass

        # Learning Capture (pgrep)
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
        """Run autonomous system checks every 15 minutes.

        This performs L2's autonomous monitoring responsibilities:
        1. Deep system health analysis
        2. Performance metrics collection
        3. Database health verification
        4. Learning pipeline verification
        5. Pattern anomaly detection
        6. Document findings to watcher-log.md
        """
        while self.running:
            try:
                logger.info("🤖 Running autonomous system checks (Level 2)")

                # Gather system state
                service_health = await self._check_services_health_async()
                time_since_last_check = (
                    datetime.now() - self.last_autonomous_check
                ).total_seconds()

                # Perform checks
                checks = {
                    "service_health": service_health,
                    "learnings_count": self._count_recent_learnings(),
                    "heuristics_count": self._count_recent_heuristics(),
                    "recent_watcher_escalations": self._count_recent_escalations(),
                    "time_since_last_check_hours": time_since_last_check / 3600,
                }

                # Log to watcher-log.md
                self._log_autonomous_checks(checks)

                # Update last check timestamp
                self.last_autonomous_check = datetime.now()

                # TODO: Perform deeper analysis using AgentManager
                # if checks indicate anomalies

                logger.info(
                    f"✅ Autonomous checks completed: "
                    f"services={sum(1 for s in service_health.values() if s)}/3, "
                    f"learnings={checks['learnings_count']}, "
                    f"heuristics={checks['heuristics_count']}"
                )

            except Exception as e:
                logger.error(f"❌ Error in autonomous system checks: {e}")

            # Wait for next cycle (15 minutes)
            await asyncio.sleep(900)

    def _count_recent_learnings(self) -> int:
        """Count learnings in last hour."""
        try:
            import sqlite3
            from pathlib import Path

            db = Path.home() / ".opencode/emergent-learning/memory/index.db"
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM learnings 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _count_recent_heuristics(self) -> int:
        """Count heuristics in last 24 hours."""
        try:
            import sqlite3
            from pathlib import Path

            db = Path.home() / ".opencode/emergent-learning/memory/index.db"
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM heuristics 
                WHERE created_at > datetime('now', '-1 day')
            """)
            count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _count_recent_escalations(self) -> int:
        """Count escalations processed in last hour."""
        try:
            if not ESCALATION_DIR.exists():
                return 0

            recent_files = [
                f
                for f in ESCALATION_DIR.glob("watcher_esc_*.md")
                if f.stat().st_mtime > (datetime.now().timestamp() - 3600)
            ]
            return len(recent_files)
        except:
            return 0

    def _log_autonomous_checks(self, checks: Dict[str, Any]):
        """Log autonomous system checks to watcher-log.md."""
        try:
            watcher_log = ELF_DIR / ".coordination" / "watcher-log.md"

            log_entry = f"""{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | STATUS: autonomous-check | NOTES: L2 autonomous check completed | Services Healthy: {checks["service_health"].get("event_bridge", False)} | Watcher: {checks["service_health"].get("watcher", False)} | Learning Capture: {checks["service_health"].get("learning_capture", False)} | Recent Learnings: {checks["learnings_count"]} | Recent Heuristics: {checks["heuristics_count"]} | Recent Escalations: {checks["recent_watcher_escalations"]} | Time Since Last Check: {checks["time_since_last_check_hours"]:.1f} hrs
"""
            # Append to watcher log
            with open(watcher_log, "a") as f:
                f.write(log_entry)

            logger.debug(f"📝 Logged autonomous checks to watcher-log.md")

        except Exception as e:
            logger.error(f"❌ Failed to log autonomous checks: {e}")
