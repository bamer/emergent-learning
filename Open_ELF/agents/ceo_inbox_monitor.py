#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
CEO Inbox Monitor - Autonomous escalation processing for CEO agent.

This script runs continuously and:
1. Checks the CEO inbox for pending escalations
2. Invokes the CEO agent to process each escalation
3. Archives processed escalations

Usage:
    python ceo_inbox_monitor.py start  # Run as daemon
    python ceo_inbox_monitor.py once   # Process once and exit
"""

import asyncio
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add agents directory to path
ROOT_DIR = Path(__file__).resolve().parents[2]  # emergent-learning dir
AGENTS_DIR = ROOT_DIR / "agents"
sys.path.insert(0, str(AGENTS_DIR))
sys.path.insert(0, str(ROOT_DIR / "Open_ELF" / "agents"))

# Import centralized elf_logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error, log_warning

    logger = get_logger("ceo_inbox_monitor")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("CEOInboxMonitor")

# Paths
CEO_INBOX_DIR = ROOT_DIR / "ceo-inbox"
CEO_ARCHIVE_DIR = CEO_INBOX_DIR / "archive"

# Configuration
CHECK_INTERVAL = 3600  # 1 hour between CEO analysis cycles (Level 3)

# ELF paths for 60-minute analysis
LEARNING_DIR = ROOT_DIR / "memory"
ELF_DIR = ROOT_DIR


class CEOInboxMonitor:
    """Autonomous CEO inbox monitoring and escalation processing."""

    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.check_interval = CHECK_INTERVAL  # seconds

        # AgentManager integration with longer timeout for CEO agent
        # CEO agent needs more time for strategic decisions - 30 minutes
        self.agent_manager = None
        try:
            from agent_manager import AgentManager

            self.agent_manager = AgentManager(
                opencode_url="http://localhost:4096", timeout=1800
            )
            logger.info(
                "✅ AgentManager initialized for CEO Inbox Monitor (timeout: 1800s)"
            )
        except Exception as e:
            logger.warning(f"⚠️ AgentManager not available: {e}")

        # Escalation tracker for database storage
        self.escalation_tracker = None
        try:
            from escalation_tracker import create_escalation, update_escalation_response

            self.escalation_tracker = {
                "create": create_escalation,
                "update": update_escalation_response,
            }
            logger.info("✅ Escalation tracker initialized")
        except Exception as e:
            logger.warning(f"⚠️ Escalation tracker not available: {e}")

        # Ensure directories exist
        CEO_INBOX_DIR.mkdir(exist_ok=True)
        CEO_ARCHIVE_DIR.mkdir(exist_ok=True)

    def get_pending_escalations(self) -> List[Path]:
        """Get list of pending escalation files."""
        escalations = []

        inbox_path = CEO_INBOX_DIR / "inbox"
        if not inbox_path.exists():
            return escalations

        # Accept any .md file in the CEO inbox as an escalation
        # This covers: ceo_escalation_*.md, orchestrator_*.md, sentinel_esc_*.md, or any other escalation format
        for file in inbox_path.glob("*.md"):
            escalations.append(file)

        return sorted(escalations)

    def process_escalation(self, file_path: Path) -> Dict[str, Any]:
        """Process a single escalation file via CEO agent."""
        logger.info(f"📬 Processing escalation: {file_path.name}")

        escalation_id = None

        try:
            # Read escalation file for reference only (not passed to AI)
            content = file_path.read_text()
            logger.debug(f"Escalation content:\n{content[:500]}...")

            # Extract escalation details for logging only
            escalation_data = self._parse_escalation(content)

            # Create escalation record in database
            if self.escalation_tracker:
                try:
                    escalation_id = self.escalation_tracker["create"](
                        source_agent=escalation_data.get("from_role", "unknown"),
                        target_agent="ceo",
                        escalation_file_path=str(file_path.relative_to(ROOT_DIR)),
                        escalation_content=content,
                        severity=self._extract_severity(content),
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create escalation record: {e}")

            # If AgentManager available, process with CEO agent
            if self.agent_manager:
                logger.info(
                    "🤖 Invoking CEO agent for autonomous escalation processing..."
                )

                # Give instructions to the AI Agent instead of passing full escalation content
                # The CEO Agent will do its own analysis
                prompt = f"""CEO Agent Strategic Analysis - {datetime.now().strftime("%Y-%m-%d %H:%M")}

Your Mission (Level 3 - Final Autonomous):
Review CEO inbox escalations and take strategic action.

Tasks:
1. Check CEO inbox for pending escalations
2. Analyze severity (critical failures, strategic issues, unresolved alerts)
3. Take autonomous actions: approve changes, promote heuristics, restart services
4. Escalate to human when: irreversible actions, high uncertainty, beyond authority

Be decisive but cautious. Document all decisions.

Current time: {datetime.now().strftime("%Y-%m-%d %H:%M")}"""

                result = self.agent_manager.ask_agent("ceo", prompt)

                if result.get("success"):
                    response = result.get("response", "")
                    logger.info(
                        f"✅ CEO agent processed escalation: {response[:200]}..."
                    )

                    # Update escalation record with response
                    if escalation_id and self.escalation_tracker:
                        try:
                            self.escalation_tracker["update"](
                                escalation_id=escalation_id,
                                response_content=response,
                                response_agent="ceo",
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to update escalation record: {e}")

                    return {
                        "status": "processed",
                        "ceo_response": response,
                        "file_path": str(file_path),
                        "timestamp": datetime.now().isoformat(),
                        "escalation_id": escalation_id,
                    }
                else:
                    logger.error(f"❌ CEO agent failed: {result.get('error')}")
                    return {"status": "failed", "error": result.get("error")}

            else:
                # Fallback: basic processing without AI
                logger.info("📋 Basic escalation processing (no AI)")
                return self._basic_escalation_processing(escalation_data, file_path)

        except Exception as e:
            logger.error(f"❌ Error processing escalation: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_escalation(self, content: str) -> Dict[str, Any]:
        """Parse escalation content to extract key information."""
        data = {}

        # Extract sections
        if "From:" in content:
            for line in content.split("\n"):
                if line.startswith("## From:"):
                    data["from_role"] = line.replace("## From:", "").strip()
                elif line.startswith("## To:"):
                    data["to_role"] = line.replace("## To:", "").strip()
                elif line.startswith("## Level:"):
                    data["level"] = line.replace("## Level:", "").strip()
                elif line.startswith("## Time:"):
                    data["timestamp"] = line.replace("## Time:", "").strip()

        # Try to extract rule name from filename or content
        data["rule_name"] = "unknown"

        return data

    def _extract_severity(self, content: str) -> str:
        """Extract severity level from escalation content."""
        content_lower = content.lower()

        # Check for severity indicators
        if "critical" in content_lower or "🚨" in content:
            return "critical"
        elif "urgent" in content_lower or "emergency" in content_lower:
            return "high"
        elif "warning" in content_lower or "⚠️" in content:
            return "medium"
        else:
            return "low"

    def _basic_escalation_processing(
        self, escalation_data: Dict, file_path: Path
    ) -> Dict[str, Any]:
        """Basic escalation processing without AI."""
        # Simple acknowledgment
        return {
            "status": "basic_processed",
            "decision": "Requires human review",
            "file_path": str(file_path),
            "timestamp": datetime.now().isoformat(),
        }

    def archive_escalation(self, file_path: Path, result: Dict[str, Any]):
        """Archive processed escalation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create processed file with result
        processed_content = f"""# Escalation Processed: {file_path.name}

**Processed At**: {datetime.now().isoformat()}
**Status**: {result.get("status", "unknown")}

## Result:
```json
{json.dumps(result, indent=2)}
```

---

## Original Escalation:
{file_path.read_text()}
"""

        # Move to archive directory
        new_name = f"archived_{timestamp}_{file_path.name}"
        archive_path = CEO_ARCHIVE_DIR / new_name
        file_path.rename(archive_path)

        logger.info(f"✅ Escalation archived: {archive_path.name}")

    def run_cycle(self):
        """Run one monitoring cycle (Level 3 CEO Analysis)."""
        self.cycle_count += 1

        logger.info(
            f"👑 CEO Inbox Monitor - Cycle #{self.cycle_count} (60-min analysis)"
        )

        # Check for pending escalations
        pending = self.get_pending_escalations()

        if pending:
            logger.info(f"📬 Found {len(pending)} pending escalations")

            # Process ALL escalations immediately
            max_per_cycle = 10  # Max escalations per cycle
            for i, escalation in enumerate(pending[:max_per_cycle]):
                logger.info(
                    f"🎯 Processing escalation {i + 1}/{min(len(pending), max_per_cycle)}: {escalation.name}"
                )
                result = self.process_escalation(escalation)

                if result.get("status") in ["processed", "basic_processed"]:
                    self.archive_escalation(escalation, result)
                else:
                    logger.warning(
                        f"⚠️  Escalation {escalation.name} not processed: {result.get('error', 'Unknown')}"
                    )

            remaining = len(pending) - max_per_cycle
            if remaining > 0:
                logger.info(f"⚠️  {remaining} escalations remaining for next cycle")
        else:
            logger.info("📭 No pending escalations")

        # Perform 60-minute CEO analysis
        self._perform_60min_analysis()

    def _perform_60min_analysis(self):
        """
        Perform the 60-minute CEO analysis.

        This is the core Level 3 function that runs every hour.
        """
        logger.info("📊 Performing 60-minute CEO analysis...")

        try:
            import sqlite3

            DB_PATH = LEARNING_DIR / "index.db"
            if not DB_PATH.exists():
                logger.warning("Database not found for CEO analysis")
                return

            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Review heuristics for golden rule promotion
            cursor.execute("""
                SELECT COUNT(*) as count FROM heuristics 
                WHERE is_golden = 0 AND confidence >= 0.9 AND times_validated >= 10
            """)
            promotion_candidates = cursor.fetchone()["count"]

            # 2. Review active experiments
            EXPERIMENTS_DIR = ELF_DIR / "memory" / "experiments" / "active"
            experiments = (
                list(EXPERIMENTS_DIR.glob("*.md")) if EXPERIMENTS_DIR.exists() else []
            )

            # 3. Review recent learnings
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM learnings 
                WHERE created_at > datetime('now', '-24 hours')
                GROUP BY type
            """)
            recent_learnings = {row[0]: row[1] for row in cursor.fetchall()}

            # 4. Review heuristics that need attention
            cursor.execute("""
                SELECT COUNT(*) as count FROM heuristics 
                WHERE is_golden = 1 AND confidence < 0.8
            """)
            degraded_golden = cursor.fetchone()["count"]

            # 5. Check unresolved alerts (if table exists)
            unresolved_alerts = 0
            try:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM alerts 
                    WHERE resolved = 0 AND created_at > datetime('now', '-24 hours')
                """)
                unresolved_alerts = cursor.fetchone()["count"]
            except Exception:
                # Alerts table may not exist
                pass

            # 6. Golden rule violations
            cursor.execute("""
                SELECT COUNT(*) as count FROM heuristics 
                WHERE is_golden = 1 AND times_violated > 0
            """)
            golden_violations = cursor.fetchone()["count"]

            conn.close()

            # Log analysis results
            logger.info("👑 CEO 60-min Analysis Results:")
            logger.info(
                f"   - Golden rule promotion candidates: {promotion_candidates}"
            )
            logger.info(f"   - Active experiments: {len(experiments)}")
            logger.info(f"   - Recent learnings: {sum(recent_learnings.values())}")
            logger.info(f"   - Degraded golden rules: {degraded_golden}")
            logger.info(f"   - Unresolved alerts: {unresolved_alerts}")
            logger.info(f"   - Golden rule violations: {golden_violations}")

            # If there are promotion candidates, log them
            if promotion_candidates > 0:
                logger.info(
                    f"   ⚠️  {promotion_candidates} heuristics ready for golden rule promotion"
                )

            # If there are degraded golden rules, log warning
            if degraded_golden > 0:
                logger.warning(
                    f"   ⚠️  {degraded_golden} golden rules have degraded confidence"
                )

            # If there are unresolved alerts, escalate to human
            if unresolved_alerts > 5:
                logger.warning(
                    f"   🚨 {unresolved_alerts} unresolved alerts - human review recommended"
                )

        except Exception as e:
            logger.error(f"CEO 60-min analysis error: {e}")

    def start(self):
        """Start continuous monitoring."""
        logger.info("=" * 60)
        logger.info("🚀 CEO Inbox Monitor Starting")
        logger.info(f"   Check Interval: {self.check_interval}s")
        logger.info("   Processing: AI only (CEO agent)")
        logger.info("=" * 60)

        self.running = True

        try:
            while self.running:
                self.run_cycle()
                logger.info(f"💤 Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down CEO Inbox Monitor...")
        finally:
            self.running = False
            logger.info("✅ CEO Inbox Monitor stopped")

    def run_once(self):
        """Run a single cycle and exit."""
        logger.info("🎯 Running single cycle...")
        self.run_cycle()
        logger.info("✅ Cycle complete")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CEO Inbox Monitor")
    parser.add_argument(
        "command",
        choices=["start", "once"],
        help="start: Run as daemon, once: Run single cycle",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=CHECK_INTERVAL,
        help=f"Seconds between checks (default: {CHECK_INTERVAL})",
    )

    args = parser.parse_args()

    monitor = CEOInboxMonitor()
    monitor.check_interval = args.check_interval

    if args.command == "start":
        monitor.start()
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()
