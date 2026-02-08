#!/usr/bin/env python3
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
    from elf_logging import get_logger, log_info, log_error, log_warning

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
CHECK_INTERVAL = 300  # 5 minutes between checks


class CEOInboxMonitor:
    """Autonomous CEO inbox monitoring and escalation processing."""

    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.check_interval = CHECK_INTERVAL  # seconds

        # AgentManager integration
        self.agent_manager = None
        try:
            from agent_manager import get_agent_manager

            self.agent_manager = get_agent_manager()
            logger.info("✅ AgentManager initialized for CEO Inbox Monitor")
        except Exception as e:
            logger.warning(f"⚠️ AgentManager not available: {e}")

        # Ensure directories exist
        CEO_INBOX_DIR.mkdir(exist_ok=True)
        CEO_ARCHIVE_DIR.mkdir(exist_ok=True)

    def get_pending_escalations(self) -> List[Path]:
        """Get list of pending escalation files."""
        escalations = []
        for file in CEO_INBOX_DIR.glob("escalation_*.md"):
            # Skip archive directory
            if file.parent == CEO_ARCHIVE_DIR:
                continue
            escalations.append(file)
        return sorted(escalations)

    def process_escalation(self, file_path: Path) -> Dict[str, Any]:
        """Process a single escalation file via CEO agent."""
        logger.info(f"📬 Processing escalation: {file_path.name}")

        try:
            # Read escalation file
            content = file_path.read_text()
            logger.debug(f"Escalation content:\n{content[:500]}...")

            # Extract escalation details
            escalation_data = self._parse_escalation(content)

            # If AgentManager available, process with CEO agent
            if self.agent_manager:
                logger.info("🤖 Invoking CEO agent for escalation processing...")

                prompt = f"""You are the CEO agent for the ELF system.

You have received an escalation that requires your attention:

## Escalation Details:
- From: {escalation_data.get("from_role", "Unknown")}
- Level: {escalation_data.get("level", "Unknown")}
- Rule: {escalation_data.get("rule_name", "Unknown")}
- Time: {escalation_data.get("timestamp", "Unknown")}

## Full Escalation Content:
{content}

## Your Task:
1. Analyze this escalation
2. Make a decision or provide guidance
3. Output your decision in the following format:

### CEO Decision

**Status**: [APPROVED/REJECTED/DEFERRED/PENDING]

**Decision Summary**:
[Brief summary of your decision]

**Rationale**:
[Explanation of your reasoning]

**Actions Required**:
- [ ] Action 1
- [ ] Action 2

**Priority**: [P0/P1/P2/P3]

**Follow-up Required**: [YES/NO]
"""

                result = self.agent_manager.ask_agent("ceo", prompt)

                if result.get("success"):
                    response = result.get("response", "")
                    logger.info(
                        f"✅ CEO agent processed escalation: {response[:200]}..."
                    )

                    return {
                        "status": "processed",
                        "ceo_response": response,
                        "file_path": str(file_path),
                        "timestamp": datetime.now().isoformat(),
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
        """Run one monitoring cycle."""
        self.cycle_count += 1

        logger.info(f"🔍 CEO Inbox Monitor - Cycle #{self.cycle_count}")

        # Check for pending escalations
        pending = self.get_pending_escalations()

        if not pending:
            logger.info("📭 No pending escalations")
            return

        logger.info(f"📬 Found {len(pending)} pending escalations")

        # Process ALL escalations immediately (not waiting for AI interval)
        # Si des escalations sont détectées → traitement IMMÉDIAT
        max_per_cycle = 10  # Max escalations per cycle to avoid long runs
        for i, escalation in enumerate(pending[:max_per_cycle]):
            logger.info(
                f"🎯 Processing escalation {i + 1}/{min(len(pending), max_per_cycle)}: {escalation.name}"
            )

            # Always use AI if available (immediate processing when escalation detected)
            result = self.process_escalation(escalation)

            # Archive if processed
            if result.get("status") in ["processed", "basic_processed"]:
                self.archive_escalation(escalation, result)
            else:
                logger.warning(
                    f"⚠️  Escalation {escalation.name} not processed: {result.get('error', 'Unknown')}"
                )

        remaining = len(pending) - max_per_cycle
        if remaining > 0:
            logger.info(f"⚠️  {remaining} escalations remaining for next cycle")

    def start(self):
        """Start continuous monitoring."""
        logger.info("=" * 60)
        logger.info("🚀 CEO Inbox Monitor Starting")
        logger.info(f"   Check Interval: {self.check_interval}s")
        logger.info(f"   AI Interval: {self.ai_interval}s")
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
