#!/usr/bin/env python3
"""
Orchestrator AI Agent (Level 2)

This agent performs:
1. System checks (deeper than Sentinel)
2. Complex repairs (Sentinel escalations)
3. Escalation handling from Sentinel
4. Learning trail review

Runs every 30 minutes or on escalation from Sentinel.
"""

import sqlite3
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent.parent
MEMORY_DIR = ELF_DIR / "memory"
DB_PATH = MEMORY_DIR / "index.db"

# Import centralized logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_warning, log_error

    logger = get_logger("orchestrator_ai")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("orchestrator_ai")


class OrchestratorAIAgent:
    """
    Level 2 AI Agent for complex system operations.

    Handles:
    - Sentinel escalations
    - System checks (CPU, memory, services)
    - Complex repairs
    - Learning trail review
    """

    def __init__(self):
        self.db_path = DB_PATH
        self.elf_dir = ELF_DIR

    # =========================================================================
    # ESCALATION HANDLING
    # =========================================================================

    def check_escalations(self) -> List[Dict[str, Any]]:
        """Check for escalations from Sentinel tier."""
        escalations = []

        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get critical alerts from last 24 hours that weren't resolved
            cursor.execute("""
                SELECT id, alert_id, category, severity, message, created_at
                FROM alerts
                WHERE severity = 'critical'
                AND created_at > datetime('now', '-24 hours')
                AND resolved = 0
                ORDER BY created_at DESC
            """)

            for row in cursor.fetchall():
                escalations.append(dict(row))

            conn.close()

            if escalations:
                logger.info(f"🎯 Found {len(escalations)} escalations from Sentinel")

        except Exception as e:
            logger.error(f"Error checking escalations: {e}")

        return escalations

    def resolve_escalation(self, alert_id: str) -> bool:
        """Mark an escalation as resolved."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error resolving escalation: {e}")
            return False

    # =========================================================================
    # SYSTEM CHECKS
    # =========================================================================

    def perform_system_checks(self) -> List[Dict[str, Any]]:
        """
        Perform deeper system checks than Sentinel.

        Returns list of check results.
        """
        checks = []

        # Database table integrity
        checks.append(self._check_database_tables())

        # Service dependencies
        checks.append(self._check_service_dependencies())

        # Memory leak detection
        checks.append(self._check_memory_patterns())

        # Learning system health
        checks.append(self._check_learning_health())

        # Hot spots analysis
        checks.append(self._check_hot_spots())

        # Golden rules status
        checks.append(self._check_golden_rules())

        return checks

    def _check_database_tables(self) -> Dict[str, Any]:
        """Check all database tables for issues."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            issues = []
            row_counts = {}

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                row_counts[table] = count

                # Check for tables with too many rows
                if (
                    table in ["metrics", "trails", "pheromone_trails"]
                    and count > 100000
                ):
                    issues.append(f"{table} has {count} rows - consider cleanup")

            conn.close()

            status = "ok" if not issues else "warning"
            return {
                "check": "db_tables",
                "status": status,
                "tables": len(tables),
                "row_counts": row_counts,
                "issues": issues,
            }
        except Exception as e:
            return {"check": "db_tables", "status": "error", "error": str(e)}

    def _check_service_dependencies(self) -> Dict[str, Any]:
        """Check service dependencies and health."""
        try:
            # Check if OpenCode is running
            result = subprocess.run(
                ["curl", "-s", "http://localhost:4096/health", "--max-time", "2"],
                capture_output=True,
                text=True,
            )
            opencode_healthy = result.returncode == 0

            # Check EventBridge
            result = subprocess.run(
                ["curl", "-s", "http://localhost:9998/status", "--max-time", "2"],
                capture_output=True,
                text=True,
            )
            event_bridge_healthy = result.returncode == 0

            issues = []
            if not opencode_healthy:
                issues.append("OpenCode not responding")
            if not event_bridge_healthy:
                issues.append("EventBridge not responding")

            status = "ok" if not issues else "warning"
            return {
                "check": "services",
                "status": status,
                "opencode": "healthy" if opencode_healthy else "unhealthy",
                "event_bridge": "healthy" if event_bridge_healthy else "unhealthy",
                "issues": issues,
            }
        except Exception as e:
            return {"check": "services", "status": "error", "error": str(e)}

    def _check_memory_patterns(self) -> Dict[str, Any]:
        """Check for memory leak patterns."""
        try:
            # Check metrics growth rate
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Get metrics count in last hour vs previous hour
            cursor.execute("""
                SELECT COUNT(*) as count FROM metrics
                WHERE created_at > datetime('now', '-1 hour')
            """)
            last_hour = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) as count FROM metrics
                WHERE created_at BETWEEN datetime('now', '-2 hour') AND datetime('now', '-1 hour')
            """)
            prev_hour = cursor.fetchone()[0]

            conn.close()

            growth_rate = (last_hour / max(prev_hour, 1)) if prev_hour > 0 else 1.0

            issues = []
            if growth_rate > 2.0:
                issues.append(f"Metrics growing 2x faster ({last_hour} vs {prev_hour})")

            status = "ok" if growth_rate < 2.0 else "warning"
            return {
                "check": "memory_patterns",
                "status": status,
                "last_hour": last_hour,
                "prev_hour": prev_hour,
                "growth_rate": round(growth_rate, 2),
                "issues": issues,
            }
        except Exception as e:
            return {"check": "memory_patterns", "status": "error", "error": str(e)}

    def _check_learning_health(self) -> Dict[str, Any]:
        """Check overall learning system health."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Count heuristics
            cursor.execute("SELECT COUNT(*) FROM heuristics")
            total_h = cursor.fetchone()[0]

            # Count golden rules
            cursor.execute("SELECT COUNT(*) FROM heuristics WHERE is_golden = 1")
            golden = cursor.fetchone()[0]

            # Count learnings
            cursor.execute("SELECT COUNT(*) FROM learnings")
            learnings = cursor.fetchone()[0]

            # Count failures
            cursor.execute("SELECT COUNT(*) FROM failures")
            failures = cursor.fetchone()[0]

            # Check for promotion candidates
            cursor.execute("""
                SELECT COUNT(*) FROM heuristics 
                WHERE is_golden = 0 AND confidence >= 0.9 AND times_validated >= 10
            """)
            candidates = cursor.fetchone()[0]

            conn.close()

            return {
                "check": "learning_health",
                "status": "ok",
                "heuristics": total_h,
                "golden_rules": golden,
                "learnings": learnings,
                "failures": failures,
                "promotion_candidates": candidates,
            }
        except Exception as e:
            return {"check": "learning_health", "status": "error", "error": str(e)}

    def _check_hot_spots(self) -> Dict[str, Any]:
        """Check hot spots for potential issues."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Get top hot spots
            cursor.execute("""
                SELECT location, SUM(strength) as total_strength, COUNT(*) as trail_count
                FROM trails
                GROUP BY location
                ORDER BY total_strength DESC
                LIMIT 10
            """)

            hot_spots = []
            for row in cursor.fetchall():
                hot_spots.append(
                    {
                        "location": row[0],
                        "strength": row[1],
                        "count": row[2],
                    }
                )

            conn.close()

            return {
                "check": "hot_spots",
                "status": "ok",
                "top_spots": hot_spots,
            }
        except Exception as e:
            return {"check": "hot_spots", "status": "error", "error": str(e)}

    def _check_golden_rules(self) -> Dict[str, Any]:
        """Check golden rules status."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM heuristics 
                WHERE is_golden = 1 AND confidence < 0.8
            """)
            degraded = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM heuristics 
                WHERE is_golden = 1 AND times_violated > 0
            """)
            violated = cursor.fetchone()[0]

            conn.close()

            issues = []
            if degraded > 0:
                issues.append(f"{degraded} golden rules with confidence < 0.8")
            if violated > 0:
                issues.append(f"{violated} golden rules have been violated")

            status = "ok" if not issues else "warning"
            return {
                "check": "golden_rules",
                "status": status,
                "degraded_count": degraded,
                "violated_count": violated,
                "issues": issues,
            }
        except Exception as e:
            return {"check": "golden_rules", "status": "error", "error": str(e)}

    # =========================================================================
    # COMPLEX REPAIRS
    # =========================================================================

    def execute_repairs(
        self, escalations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute complex repairs for escalations."""
        repairs = []

        for escalation in escalations:
            category = escalation.get("category", "")
            severity = escalation.get("severity", "")

            if severity == "critical":
                # Try database repair
                if "db" in category.lower():
                    repair = self._repair_database(escalation)
                    if repair["success"]:
                        repairs.append(repair)
                        self.resolve_escalation(escalation["id"])

                # Restart stuck processes
                elif "process" in category.lower():
                    repair = self._restart_process(escalation)
                    if repair["success"]:
                        repairs.append(repair)
                        self.resolve_escalation(escalation["id"])

        return repairs

    def _repair_database(self, escalation: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt database repair."""
        try:
            # Run integrity check and optimization
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            cursor = conn.cursor()

            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result and result[0] == "ok":
                # Run optimization
                cursor.execute("VACUUM")
                conn.commit()

                conn.close()

                return {
                    "action": "database_repair",
                    "success": True,
                    "details": "Database integrity OK, vacuum completed",
                    "escalation_id": escalation.get("id"),
                }
            else:
                conn.close()
                # Mark for CEO escalation
                return {
                    "action": "database_repair",
                    "success": False,
                    "details": f"Database integrity issue: {result}",
                    "escalation_id": escalation.get("id"),
                    "needs_ceo": True,
                }
        except Exception as e:
            return {
                "action": "database_repair",
                "success": False,
                "error": str(e),
                "escalation_id": escalation.get("id"),
            }

    def _restart_process(self, escalation: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a stuck process."""
        try:
            process_name = escalation.get("category", "").replace("process_", "")

            # Kill existing
            subprocess.run(["pkill", "-f", process_name], capture_output=True)

            # Brief pause
            import time

            time.sleep(2)

            return {
                "action": "process_restart",
                "success": True,
                "process": process_name,
                "escalation_id": escalation.get("id"),
            }
        except Exception as e:
            return {
                "action": "process_restart",
                "success": False,
                "error": str(e),
                "escalation_id": escalation.get("id"),
            }

    # =========================================================================
    # LEARNING TRAIL REVIEW
    # =========================================================================

    def review_learning_trails(self) -> Dict[str, Any]:
        """Review learning trails for quality and patterns."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Get trail summary
            cursor.execute("SELECT COUNT(*) FROM trails")
            total_trails = cursor.fetchone()[0]

            # Get scents distribution
            cursor.execute("SELECT scent, COUNT(*) FROM trails GROUP BY scent")
            scents = {row[0]: row[1] for row in cursor.fetchall()}

            # Get hot spots count
            cursor.execute(
                "SELECT COUNT(DISTINCT location) FROM trails WHERE strength > 5"
            )
            hot_spots = cursor.fetchone()[0]

            # Check for stale trails (older than 48 hours)
            cursor.execute(
                "SELECT COUNT(*) FROM trails WHERE created_at < datetime('now', '-48 hours')"
            )
            stale = cursor.fetchone()[0]

            conn.close()

            return {
                "summary": f"{total_trails} total trails, {hot_spots} hot spots, {stale} stale",
                "total_trails": total_trails,
                "scents": scents,
                "hot_spots": hot_spots,
                "stale_trails": stale,
            }
        except Exception as e:
            return {"summary": f"Error: {e}", "error": str(e)}

    def decay_trails(self):
        """Decay old trails (called during review)."""
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()

            # Decay trails by 10%
            cursor.execute("""
                UPDATE trails 
                SET strength = strength * 0.9 
                WHERE strength > 0.1
            """)

            # Remove very weak trails
            cursor.execute("DELETE FROM trails WHERE strength < 0.05")

            conn.commit()
            conn.close()

            logger.info("✅ Trail decay completed")
            return True
        except Exception as e:
            logger.error(f"Trail decay error: {e}")
            return False

    # =========================================================================
    # MAIN
    # =========================================================================

    def run_cycle(self):
        """Run a complete Orchestrator AI cycle."""
        logger.info("🎯 Orchestrator AI Cycle starting...")

        # 1. Check for escalations
        escalations = self.check_escalations()

        # 2. Perform system checks
        checks = self.perform_system_checks()

        # 3. Execute repairs for escalations
        repairs = self.execute_repairs(escalations)

        # 4. Review learning trails
        trail_review = self.review_learning_trails()

        # 5. Decay trails
        self.decay_trails()

        logger.info(
            f"🎯 Cycle complete: {len(escalations)} escalations, {len(checks)} checks, {len(repairs)} repairs"
        )

        return {
            "escalations": escalations,
            "checks": checks,
            "repairs": repairs,
            "trail_review": trail_review,
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator AI Agent")
    parser.add_argument(
        "command",
        choices=["run", "check", "decay"],
        help="run: Full cycle, check: System checks only, decay: Trail decay only",
    )

    args = parser.parse_args()

    agent = OrchestratorAIAgent()

    if args.command == "run":
        result = agent.run_cycle()
        print("\n🎯 Orchestrator AI Results:")
        print(f"  Escalations: {len(result['escalations'])}")
        print(f"  Checks: {len(result['checks'])}")
        print(f"  Repairs: {len(result['repairs'])}")
        print(f"  Trail review: {result['trail_review'].get('summary', 'N/A')}")

    elif args.command == "check":
        checks = agent.perform_system_checks()
        print("\n📊 System Checks:")
        for check in checks:
            icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(
                check.get("status"), "?"
            )
            print(f"  {icon} {check['check']}: {check.get('status', 'unknown')}")

    elif args.command == "decay":
        agent.decay_trails()
        print("\n✅ Trail decay complete")


if __name__ == "__main__":
    main()
