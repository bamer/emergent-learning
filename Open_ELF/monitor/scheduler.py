#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
ELF Tiered Scheduler - Local Python Scheduler for Monitoring Tiers

This scheduler manages the three-tier monitoring system without systemd:

Level 1 (Sentinel AI):    Every 15 minutes → Basic metrics + simple repairs
Level 2 (Orchestrator AI): Every 30 minutes → System checks + complex repairs
Level 3 (CEO AI):          Every 60 minutes → Learning quality + high-level analysis

Usage:
    python3 scheduler.py start     # Start all tiers
    python3 scheduler.py status    # Show tier status
    python3 scheduler.py stop      # Stop all tiers
"""

import sys
import time
import json
import threading
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent.parent
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Import centralized logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_warning, log_error

    logger = get_logger("elf_scheduler")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("elf_scheduler")

# Paths
SCHEDULER_STATE_FILE = ELF_DIR / "memory" / "scheduler_state.json"
LOGS_DIR = ELF_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Tier intervals in seconds
TIER_INTERVALS = {
    "sentinel": 15 * 60,  # 15 minutes
    "orchestrator": 30 * 60,  # 30 minutes
    "ceo": 60 * 60,  # 60 minutes
}


class ELFTieredScheduler:
    """
    Local scheduler for managing the three-tier monitoring system.

    Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │ Tier 1: Sentinel AI (15 min)                                │
    │   └─ Metrics collection, simple repairs, alert generation   │
    │                                                             │
    │ Tier 2: Orchestrator AI (30 min)                            │
    │   └─ System checks, complex repairs, escalation handling    │
    │                                                             │
    │ Tier 3: CEO AI (60 min)                                     │
    │   └─ Learning quality review, experiment analysis, decisions│
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.running = False
        self.threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.last_runs: Dict[str, Optional[datetime]] = {}
        self.state_lock = threading.Lock()

        # Load state
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load scheduler state from file."""
        if SCHEDULER_STATE_FILE.exists():
            try:
                return json.loads(SCHEDULER_STATE_FILE.read_text())
            except:
                pass
        return {
            "sentinel": {"last_run": None, "enabled": True},
            "orchestrator": {"last_run": None, "enabled": True},
            "ceo": {"last_run": None, "enabled": True},
        }

    def _save_state(self):
        """Save scheduler state to file."""
        with self.state_lock:
            SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            SCHEDULER_STATE_FILE.write_text(
                json.dumps(self.state, indent=2, default=str)
            )

    def _update_last_run(self, tier: str):
        """Update last run timestamp for a tier."""
        self.state[tier]["last_run"] = datetime.now().isoformat()
        self._save_state()

    def run_sentinel_tier(self):
        """
        Tier 1: Sentinel AI - Basic metrics and simple repairs.
        Runs every 15 minutes.
        """
        tier = "sentinel"
        logger.info("🛡️  Sentinel AI Tier starting...")

        while not self.stop_events[tier].is_set():
            try:
                from Open_ELF.monitor.monitor_agent import MonitorAgent

                monitor = MonitorAgent()

                # Collect metrics
                metrics = monitor.collect_metrics()

                # Generate alerts
                alerts = monitor.generate_alerts(metrics)

                # Try simple repairs
                repairs = monitor.simple_repairs(alerts)

                # Log results
                logger.info(
                    f"📊 Sentinel: collected {len(metrics)} metrics, generated {len(alerts)} alerts, performed {len(repairs)} repairs"
                )

                # Update last run
                self._update_last_run(tier)

            except ImportError as e:
                logger.warning(f"Sentinel components not available: {e}")
            except Exception as e:
                logger.error(f"Sentinel tier error: {e}")

            # Wait for next interval or stop signal
            self.stop_events[tier].wait(TIER_INTERVALS[tier])

        logger.info("🛡️  Sentinel AI Tier stopped")

    def run_orchestrator_tier(self):
        """
        Tier 2: Orchestrator AI - System checks and complex repairs.
        Runs every 30 minutes.
        """
        tier = "orchestrator"
        logger.info("🎯 Orchestrator AI Tier starting...")

        while not self.stop_events[tier].is_set():
            try:
                from Open_ELF.agents.orchestrator_ai import OrchestratorAIAgent

                agent = OrchestratorAIAgent()

                # Check for Sentinel escalations
                escalations = agent.check_escalations()

                # Perform system checks
                checks = agent.perform_system_checks()

                # Execute complex repairs
                repairs = agent.execute_repairs(escalations)

                # Review learning trails
                trail_review = agent.review_learning_trails()

                logger.info(
                    f"🎯 Orchestrator: {len(escalations)} escalations, {len(checks)} checks, {len(repairs)} repairs, trail review: {trail_review}"
                )

                self._update_last_run(tier)

            except ImportError as e:
                logger.warning(f"Orchestrator components not available: {e}")
            except Exception as e:
                logger.error(f"Orchestrator tier error: {e}")

            self.stop_events[tier].wait(TIER_INTERVALS[tier])

        logger.info("🎯 Orchestrator AI Tier stopped")

    def run_ceo_tier(self):
        """
        Tier 3: CEO AI - High-level analysis and decisions.
        Runs every 60 minutes.
        """
        tier = "ceo"
        logger.info("👑 CEO AI Tier starting...")

        while not self.stop_events[tier].is_set():
            try:
                from Open_ELF.agents.ceo_inbox_monitor import CEOInboxMonitor

                # Process any pending escalations first
                ceo_monitor = CEOInboxMonitor()
                pending = ceo_monitor.get_pending_escalations()
                if pending:
                    logger.info(
                        f"👑 CEO: Processing {len(pending)} pending escalations"
                    )
                    for escalation in pending:
                        ceo_monitor.process_escalation(escalation)

                # Perform 60-minute analysis
                analysis = self._perform_ceo_analysis()

                logger.info(
                    f"👑 CEO: Analysis complete - {analysis.get('summary', 'no results')}"
                )

                self._update_last_run(tier)

            except ImportError as e:
                logger.warning(f"CEO components not available: {e}")
            except Exception as e:
                logger.error(f"CEO tier error: {e}")

            self.stop_events[tier].wait(TIER_INTERVALS[tier])

        logger.info("👑 CEO AI Tier stopped")

    def _perform_ceo_analysis(self) -> Dict[str, Any]:
        """Perform the 60-minute CEO analysis."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": None,
            "heuristics_reviewed": 0,
            "golden_rules_promoted": 0,
            "experiments_reviewed": 0,
            "decisions_made": 0,
        }

        try:
            import sqlite3

            DB_PATH = ELF_DIR / "memory" / "index.db"

            if not DB_PATH.exists():
                return analysis

            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Review heuristics for promotion
            cursor.execute("""
                SELECT COUNT(*) as count FROM heuristics 
                WHERE is_golden = 0 AND confidence >= 0.9 AND times_validated >= 10
            """)
            promotion_candidates = cursor.fetchone()["count"]

            # Check active experiments
            EXPERIMENTS_DIR = ELF_DIR / "memory" / "experiments" / "active"
            if EXPERIMENTS_DIR.exists():
                experiments = list(EXPERIMENTS_DIR.glob("*.md"))
                analysis["experiments_reviewed"] = len(experiments)

            # Review recent learnings
            cursor.execute(
                "SELECT COUNT(*) as count FROM learnings WHERE created_at > datetime('now', '-24 hours')"
            )
            recent_learnings = cursor.fetchone()["count"]

            conn.close()

            analysis["heuristics_reviewed"] = recent_learnings
            analysis["golden_rules_promoted"] = promotion_candidates
            analysis["summary"] = (
                f"{recent_learnings} learnings, {promotion_candidates} promotion candidates, {analysis['experiments_reviewed']} active experiments"
            )

        except Exception as e:
            logger.error(f"CEO analysis error: {e}")

        return analysis

    def start(self):
        """Start all monitoring tiers."""
        logger.info("=" * 60)
        logger.info("🚀 ELF Tiered Scheduler Starting")
        logger.info(
            f"   Sentinel (15 min):     {'✅' if self.state['sentinel']['enabled'] else '❌'}"
        )
        logger.info(
            f"   Orchestrator (30 min): {'✅' if self.state['orchestrator']['enabled'] else '❌'}"
        )
        logger.info(
            f"   CEO (60 min):          {'✅' if self.state['ceo']['enabled'] else '❌'}"
        )
        logger.info("=" * 60)

        self.running = True

        # Start each tier in its own thread
        tiers = ["sentinel", "orchestrator", "ceo"]
        for tier in tiers:
            if self.state[tier]["enabled"]:
                self.stop_events[tier] = threading.Event()
                self.threads[tier] = threading.Thread(
                    target=getattr(self, f"run_{tier}_tier"), name=f"elf_{tier}_tier"
                )
                self.threads[tier].daemon = True
                self.threads[tier].start()
                logger.info(f"   ✅ {tier.upper()} tier started")
            else:
                logger.info(f"   ❌ {tier.upper()} tier disabled")

        # Main thread waits for signal
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop all monitoring tiers."""
        logger.info("👋 ELF Tiered Scheduler stopping...")
        self.running = False

        # Signal all threads to stop
        for tier in self.stop_events:
            self.stop_events[tier].set()

        # Wait for threads to finish
        for tier, thread in self.threads.items():
            thread.join(timeout=5)
            logger.info(f"   ✅ {tier.upper()} tier stopped")

        logger.info("✅ ELF Tiered Scheduler stopped")

    def status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        status = {
            "running": self.running,
            "tiers": {},
            "timestamp": datetime.now().isoformat(),
        }

        for tier in ["sentinel", "orchestrator", "ceo"]:
            tier_info = {
                "enabled": self.state[tier]["enabled"],
                "last_run": self.state[tier]["last_run"],
                "running": self.threads[tier].is_alive()
                if tier in self.threads
                else False,
                "interval_minutes": TIER_INTERVALS[tier] // 60,
            }

            # Calculate time since last run
            if tier_info["last_run"]:
                try:
                    last = datetime.fromisoformat(tier_info["last_run"])
                    since = (datetime.now() - last).total_seconds()
                    tier_info["minutes_ago"] = int(since // 60)
                except:
                    tier_info["minutes_ago"] = None

            status["tiers"][tier] = tier_info

        return status


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ELF Tiered Scheduler")
    parser.add_argument(
        "command",
        choices=["start", "status", "stop"],
        help="start: Run scheduler, status: Show status, stop: Stop scheduler",
    )

    args = parser.parse_args()

    scheduler = ELFTieredScheduler()

    if args.command == "start":
        scheduler.start()
    elif args.command == "status":
        status = scheduler.status()
        print("\n" + "=" * 60)
        print("   ELF Tiered Scheduler Status")
        print("=" * 60)
        print(f"   Running: {'Yes' if status['running'] else 'No'}")
        print()
        for tier, info in status["tiers"].items():
            icon = "🟢" if info["running"] else "🔴"
            last_run = info.get("minutes_ago", "N/A")
            print(
                f"   {icon} {tier.upper():15} | {info['interval_minutes']} min interval | Last: {last_run} min ago"
            )
        print("=" * 60)
    elif args.command == "stop":
        scheduler.stop()


if __name__ == "__main__":
    main()
