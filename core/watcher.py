#!/usr/bin/env python3
"""
ELF Watcher v3.0 - Consolidated Monitoring Agent

Level 1 Agent: Watcher
Merged functionality from Watcher + Sentinel:
- Health checks for all services (from Watcher)
- Pattern detection and learning (from Sentinel)
- AI analysis via AgentManager
- Escalation to CEO inbox
- Metrics collection and reporting

Hierarchy:
  Level 1: Watcher (this file) - Monitoring and detection
  Level 2: Orchestrator - Service management and coordination
  Level 3: CEO - Strategic decisions and escalations
"""

import json
import sys
import time
import sqlite3
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent
CORE_DIR = SCRIPT_DIR
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# Import AgentManager
try:
    from Open_ELF.agents.agent_manager import AgentManager, get_agent_manager

    AGENT_MANAGER_AVAILABLE = True
except ImportError:
    AGENT_MANAGER_AVAILABLE = False

# Setup logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_watcher_check

    logger = get_logger("watcher")
    LOGGING_AVAILABLE = True
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("watcher")
    LOGGING_AVAILABLE = False

    def log_watcher_check(*args, **kwargs):
        return None


# Configuration
OPENCODE_SERVER = "http://localhost:4096"
EVENT_BRIDGE_URL = "http://localhost:9998"
DASHBOARD_BACKEND = "http://localhost:8888"
DASHBOARD_FRONTEND = "http://localhost:3001"
DB_PATH = ELF_DIR / "memory" / "index.db"
CEO_INBOX_DIR = ELF_DIR / "ceo-inbox"
# L1 → L2 escalations (Watcher → Orchestrator)
ESCALATION_DIR = ELF_DIR / ".coordination" / "escalations"

# Monitoring intervals
BASIC_INTERVAL = 60  # seconds - basic health checks
AI_INTERVAL = 300  # seconds - AI analysis (5 minutes)
PATTERN_COOLDOWN = 1800  # seconds - 30 minutes between same pattern reports


class Watcher:
    """
    Consolidated monitoring agent (Level 1).

    Responsibilities:
    1. Service health monitoring
    2. Pattern detection and learning
    3. Metrics collection
    4. AI-powered analysis
    5. Escalation to CEO when critical
    """

    def __init__(self):
        self.cycle_count = 0
        self.escalation_count = 0
        self.pattern_memory = []
        self.pattern_cooldowns = {}
        self.agent_manager = None
        self.last_analysis = None

        # Initialize AgentManager
        if AGENT_MANAGER_AVAILABLE:
            try:
                self.agent_manager = get_agent_manager()
                logger.info("✅ AgentManager initialized")
            except Exception as e:
                logger.error(f"❌ AgentManager failed: {e}")

    def check_service_health(self, url: str, timeout: int = 5) -> bool:
        """Check if a service is healthy."""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False

    def check_process_running(self, pattern: str) -> bool:
        """Check if a process is running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern], capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.cycle_count,
            "services": {},
            "database": {},
            "patterns": [],
        }

        # Service health checks
        metrics["services"] = {
            "opencode_server": self.check_service_health(OPENCODE_SERVER),
            "event_bridge": self.check_service_health(f"{EVENT_BRIDGE_URL}/status"),
            "dashboard_backend": self.check_service_health(f"{DASHBOARD_BACKEND}/docs"),
            "dashboard_frontend": self.check_service_health(DASHBOARD_FRONTEND),
            "learning_capture": self.check_process_running(
                "background-learning-capture.py"
            ),
        }

        # Database metrics
        try:
            if DB_PATH.exists():
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()

                # Count key tables
                cursor.execute("SELECT COUNT(*) FROM learnings")
                metrics["database"]["learnings"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM heuristics")
                metrics["database"]["heuristics"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
                metrics["database"]["golden_rules"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM trails")
                metrics["database"]["trails"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM pheromone_trails")
                metrics["database"]["pheromone_trails"] = cursor.fetchone()[0]

                # Recent activity
                cursor.execute(
                    "SELECT COUNT(*) FROM learnings WHERE created_at > datetime('now', '-1 hour')"
                )
                metrics["database"]["recent_learnings"] = cursor.fetchone()[0]

                conn.close()
        except Exception as e:
            logger.error(f"Database metrics error: {e}")
            metrics["database"]["error"] = str(e)

        return metrics

    def detect_patterns(self, metrics: Dict[str, Any]) -> List[str]:
        """Detect patterns in metrics over time."""
        patterns = []
        now = datetime.now()

        # Store metrics in memory
        self.pattern_memory.append({"timestamp": now, "metrics": metrics})

        # Keep only last 50 entries
        if len(self.pattern_memory) > 50:
            self.pattern_memory = self.pattern_memory[-50:]

        # Need at least 5 entries for pattern detection
        if len(self.pattern_memory) < 5:
            return patterns

        # Check for declining activity
        recent_activity = [
            entry["metrics"]["database"].get("recent_learnings", 0)
            for entry in self.pattern_memory[-5:]
        ]

        if all(
            recent_activity[i] <= recent_activity[i - 1]
            for i in range(1, len(recent_activity))
        ):
            if self._can_report_pattern("declining_activity"):
                patterns.append("Declining activity trend detected")
                self._mark_pattern_reported("declining_activity")

        # Check for service instability
        recent_services = [
            all(entry["metrics"]["services"].values())
            for entry in self.pattern_memory[-10:]
        ]

        if not all(recent_services):
            if self._can_report_pattern("service_instability"):
                patterns.append("Service instability detected")
                self._mark_pattern_reported("service_instability")

        # Check for database growth
        if len(self.pattern_memory) >= 10:
            old_learnings = self.pattern_memory[-10]["metrics"]["database"].get(
                "learnings", 0
            )
            new_learnings = metrics["database"].get("learnings", 0)
            growth = new_learnings - old_learnings

            if growth > 50:  # More than 50 new learnings in last 10 cycles
                if self._can_report_pattern("rapid_learning_growth"):
                    patterns.append(f"Rapid learning growth: +{growth} learnings")
                    self._mark_pattern_reported("rapid_learning_growth")

        return patterns

    def _can_report_pattern(self, pattern_key: str) -> bool:
        """Check if enough time has passed since last report."""
        if pattern_key not in self.pattern_cooldowns:
            return True

        last_reported = self.pattern_cooldowns[pattern_key]
        return (datetime.now() - last_reported).total_seconds() > PATTERN_COOLDOWN

    def _mark_pattern_reported(self, pattern_key: str):
        """Mark a pattern as reported."""
        self.pattern_cooldowns[pattern_key] = datetime.now()

    def analyze_with_ai(
        self, metrics: Dict[str, Any], patterns: List[str]
    ) -> Dict[str, Any]:
        """AI-powered analysis of system state."""
        if not self.agent_manager:
            return self._fallback_analysis(metrics, "AgentManager unavailable")

        try:
            # Build context for AI
            context = {
                "metrics": metrics,
                "patterns": patterns,
                "cycle": self.cycle_count,
                "analysis_type": "watcher_assessment",
            }

            # Query watcher agent
            result = self.agent_manager.watcher(
                request="Analyze the current system state based on the provided metrics and patterns. "
                "Focus on: 1) Overall health status, 2) Any anomalies or concerns, "
                "3) Recommended actions with priority levels.",
                context=context,
            )

            if result.get("success"):
                ai_response = result.get("response", "")

                return {
                    "status": self._parse_status(ai_response),
                    "analysis": ai_response,
                    "anomalies": self._extract_items(ai_response, "anomal"),
                    "recommendations": self._extract_items(ai_response, "recommend"),
                    "priority_actions": self._extract_priority_actions(ai_response),
                    "ai_processed": True,
                    "session_id": result.get("session_id"),
                }
            else:
                return self._fallback_analysis(
                    metrics, result.get("error", "AI analysis failed")
                )

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._fallback_analysis(metrics, str(e))

    def _parse_status(self, response: str) -> str:
        """Extract status from AI response."""
        response_lower = response.lower()
        if any(
            word in response_lower for word in ["critical", "severe", "down", "failure"]
        ):
            return "critical"
        elif any(
            word in response_lower
            for word in ["warning", "degraded", "issue", "problem"]
        ):
            return "warning"
        return "healthy"

    def _extract_items(self, response: str, keyword: str) -> List[str]:
        """Extract list items following a keyword."""
        items = []
        lines = response.split("\n")
        in_section = False

        for line in lines:
            lower_line = line.lower()
            if keyword in lower_line:
                in_section = True
            elif in_section and line.strip().startswith(("-", "*", "•")):
                items.append(line.strip()[1:].strip())
            elif in_section and line.strip() == "":
                in_section = False

        return items

    def _extract_priority_actions(self, response: str) -> List[str]:
        """Extract priority actions from response."""
        actions = []
        lines = response.split("\n")
        in_priority = False

        for line in lines:
            lower_line = line.lower()
            if any(
                word in lower_line
                for word in ["priority", "immediate", "urgent", "action"]
            ):
                in_priority = True
            elif in_priority and line.strip().startswith(("-", "*", "•")):
                actions.append(line.strip()[1:].strip())
            elif in_priority and line.strip() == "":
                in_priority = False

        return actions

    def _fallback_analysis(
        self, metrics: Dict[str, Any], error_msg: str
    ) -> Dict[str, Any]:
        """Basic analysis without AI."""
        services = metrics.get("services", {})
        all_healthy = all(services.values()) if services else False

        if not all_healthy:
            status = "warning"
            analysis = f"Some services are unhealthy. {error_msg}"
        else:
            status = "healthy"
            analysis = f"All systems operational (AI unavailable: {error_msg})"

        return {
            "status": status,
            "analysis": analysis,
            "anomalies": [],
            "recommendations": [],
            "priority_actions": [],
            "ai_processed": False,
            "fallback": True,
        }

    def create_escalation(
        self, analysis: Dict[str, Any], metrics: Dict[str, Any]
    ) -> Optional[str]:
        """Create escalation file for Orchestrator when serious issues detected."""
        # Escalate to Orchestrator for both "warning" and "critical" statuses
        if analysis.get("status") not in ["warning", "critical"]:
            return None

        try:
            # Create escalation directory for L1 → L2 communication
            ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
            CEO_INBOX_DIR.mkdir(parents=True, exist_ok=True)

            escalation_id = f"watcher_esc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            # Write to coordination directory for Orchestrator (L2) to process
            escalation_file = ESCALATION_DIR / f"{escalation_id}.md"

            with open(escalation_file, "w") as f:
                f.write(f"# Watcher Escalation to Orchestrator: {escalation_id}\n\n")
                f.write(f"**Source:** Watcher (Level 1 Agent)\n")
                f.write(f"**Target:** Orchestrator (Level 2 Agent)\n")
                f.write(f"**Time:** {datetime.now().isoformat()}\n")
                f.write(f"**Status:** {analysis.get('status', 'unknown').upper()}\n")
                f.write(
                    f"**Severity:** {'Critical' if analysis.get('status') == 'critical' else 'Warning'}\n\n"
                )

                f.write("## System Metrics\n\n")
                f.write(f"```json\n{json.dumps(metrics, indent=2)}\n```\n\n")

                f.write("## Watcher Analysis\n\n")
                f.write(f"{analysis.get('analysis', 'No analysis available')}\n\n")

                if analysis.get("anomalies"):
                    f.write("## Anomalies Detected\n\n")
                    for anomaly in analysis["anomalies"]:
                        f.write(f"- {anomaly}\n")
                    f.write("\n")

                if analysis.get("priority_actions"):
                    f.write("## Recommended Actions\n\n")
                    f.write("The Watcher recommends the following actions:\n\n")
                    for action in analysis["priority_actions"]:
                        f.write(f"- [ ] {action}\n")
                    f.write("\n")

                f.write("## Orchestrator Instructions\n\n")
                f.write("As the Level 2 agent, please:\n\n")
                f.write("1. Review the Watcher's analysis above\n")
                f.write("2. Perform your own assessment using AgentManager\n")
                f.write("3. Take appropriate autonomous actions\n")
                f.write("4. **If critical**, escalate to CEO (Level 3)\n")
                f.write("5. Document all actions taken\n\n")

                f.write("---\n\n")
                f.write(
                    "This escalation was automatically generated by the Watcher agent (Level 1).\n"
                )

            self.escalation_count += 1
            logger.info(f"🚨 Escalation to Orchestrator created: {escalation_file}")

            # Log to database
            if LOGGING_AVAILABLE:
                log_watcher_check(
                    tier=1,
                    status=analysis.get("status"),
                    summary=f"Escalation to Orchestrator: {escalation_id}",
                    details={"escalation_file": str(escalation_file), **analysis},
                )

            return str(escalation_file)

        except Exception as e:
            logger.error(f"Failed to create escalation: {e}")
            return None

    def log_cycle(
        self,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any],
        patterns: List[str],
        escalation_file: Optional[str],
    ):
        """Log monitoring cycle to database."""
        if LOGGING_AVAILABLE:
            try:
                log_watcher_check(
                    tier=1 if not analysis.get("ai_processed") else 2,
                    status=analysis.get("status", "unknown"),
                    summary=f"Cycle {self.cycle_count}: {analysis.get('analysis', '')[:100]}...",
                    details={
                        "cycle": self.cycle_count,
                        "patterns": patterns,
                        "escalation": escalation_file,
                        "services": metrics.get("services"),
                        "database": metrics.get("database"),
                        "ai_processed": analysis.get("ai_processed", False),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to log cycle: {e}")

    def display_status(
        self,
        metrics: Dict[str, Any],
        analysis: Dict[str, Any],
        patterns: List[str],
        escalation_file: Optional[str],
    ):
        """Display current status."""
        status_emoji = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(
            analysis.get("status", "unknown"), "⚪"
        )

        print(f"\n{'=' * 70}")
        print(
            f"🔍 Watcher v3.0 - Level 1 Agent - {datetime.now().strftime('%H:%M:%S')}"
        )
        print(f"{'=' * 70}")
        print(f"{status_emoji} Status: {analysis.get('status', 'unknown').upper()}")
        print(
            f"🤖 AI Analysis: {'Yes' if analysis.get('ai_processed') else 'No (fallback)'}"
        )
        print(f"📊 Cycle: {self.cycle_count}")
        print(f"🚨 Escalations: {self.escalation_count}")

        # Services
        print(f"\n🌐 Services:")
        for service, healthy in metrics.get("services", {}).items():
            print(f"  {service}: {'🟢' if healthy else '🔴'}")

        # Database
        print(f"\n💾 Database:")
        db = metrics.get("database", {})
        print(f"  Learnings: {db.get('learnings', 0)}")
        print(
            f"  Heuristics: {db.get('heuristics', 0)} ({db.get('golden_rules', 0)} golden)"
        )
        print(
            f"  Trails: {db.get('trails', 0)} | Pheromone: {db.get('pheromone_trails', 0)}"
        )

        # Patterns
        if patterns:
            print(f"\n🔍 Patterns:")
            for pattern in patterns:
                print(f"  • {pattern}")

        # Analysis
        print(f"\n💡 Analysis:")
        print(f"  {analysis.get('analysis', 'No analysis')}")

        if analysis.get("priority_actions"):
            print(f"\n⚡ Priority Actions:")
            for action in analysis["priority_actions"][:3]:  # Show first 3
                print(f"  • {action}")

        if escalation_file:
            print(f"\n🚨 Escalation Created: {escalation_file}")

        print(f"{'=' * 70}\n")

    def run_cycle(self) -> Dict[str, Any]:
        """Execute one monitoring cycle."""
        self.cycle_count += 1
        logger.info(f"Starting cycle {self.cycle_count}")

        # Collect metrics
        metrics = self.collect_metrics()

        # Detect patterns
        patterns = self.detect_patterns(metrics)

        # AI analysis (only every AI_INTERVAL cycles)
        should_run_ai = (self.cycle_count % (AI_INTERVAL // BASIC_INTERVAL)) == 0

        if should_run_ai and self.agent_manager:
            logger.info("Running AI analysis...")
            analysis = self.analyze_with_ai(metrics, patterns)
        else:
            # Basic analysis without AI
            analysis = self._fallback_analysis(
                metrics,
                "AI analysis skipped (interval not reached)"
                if not should_run_ai
                else "AI unavailable",
            )
            analysis["patterns"] = patterns

        # Create escalation if critical
        escalation_file = None
        if analysis.get("status") == "critical":
            escalation_file = self.create_escalation(analysis, metrics)

        # Log cycle
        self.log_cycle(metrics, analysis, patterns, escalation_file)

        # Display status
        self.display_status(metrics, analysis, patterns, escalation_file)

        # Store for next cycle
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "analysis": analysis,
            "patterns": patterns,
            "escalation": escalation_file,
        }

        return self.last_analysis

    def run_continuous(self):
        """Run continuous monitoring."""
        logger.info(f"🚀 Watcher v3.0 starting...")
        logger.info(f"   Basic interval: {BASIC_INTERVAL}s")
        logger.info(f"   AI analysis interval: {AI_INTERVAL}s")
        logger.info(
            f"   AgentManager: {'✅ Available' if self.agent_manager else '❌ Unavailable'}"
        )

        try:
            while True:
                self.run_cycle()
                time.sleep(BASIC_INTERVAL)
        except KeyboardInterrupt:
            logger.info("⏹️  Stopped by user")
        except Exception as e:
            logger.error(f"❌ Watcher crashed: {e}")
            raise


def main():
    """Main entry point."""
    watcher = Watcher()
    watcher.run_continuous()


if __name__ == "__main__":
    main()
