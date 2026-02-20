#!/usr/bin/env python3

# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO 
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
MonitorAgent - Unified Monitoring for ELF System

This adapts and replaces:
- health_daemon.py (basic health checks)
- watchdog_sentinel.py (process monitoring)

Responsibilities:
1. Collect system metrics (CPU, memory, disk, services)
2. Check ELF-specific components (database, processes)
3. Generate alerts for the Sentinel AI tier
4. Attempt simple auto-repairs

Usage:
    python3 monitor_agent.py collect     # Collect metrics once
    python3 monitor_agent.py check        # Check and alert
    python3 monitor_agent.py auto-repair  # Run auto-repairs
"""

import os
import sys
import sqlite3
import shutil
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent.parent
MEMORY_DIR = ELF_DIR / "memory"
DB_PATH = MEMORY_DIR / "index.db"
LOGS_DIR = ELF_DIR / "logs"
LOCK_DIR = ELF_DIR / "locks"

# Import centralized logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_warning, log_error

    logger = get_logger("monitor_agent")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("monitor_agent")


@dataclass
class Metric:
    """A system metric."""

    name: str
    value: Any
    unit: str
    status: str  # ok, warning, critical


@dataclass
class Alert:
    """A system alert."""

    id: str
    tier: str  # sentinel, orchestrator, ceo
    category: str
    severity: str  # info, warning, critical
    message: str
    metric: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.id = (
            f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.category[:8]}"
        )


class MonitorAgent:
    """
    Unified MonitorAgent for ELF system.

    Collects metrics and generates alerts for the Sentinel AI tier.
    """

    def __init__(self):
        self.db_path = DB_PATH
        self.elf_dir = ELF_DIR
        self.alerts: List[Alert] = []

    # =========================================================================
    # METRICS COLLECTION
    # =========================================================================

    def collect_metrics(self) -> List[Dict[str, Any]]:
        """
        Collect all system metrics.

        Returns list of metrics with status (ok, warning, critical).
        """
        metrics = []

        # CPU usage
        metrics.append(self._check_cpu())

        # Memory usage
        metrics.append(self._check_memory())

        # Disk usage
        metrics.append(self._check_disk())

        # Database integrity
        metrics.append(self._check_database_integrity())

        # Database size
        metrics.append(self._check_database_size())

        # ELF process checks
        metrics.extend(self._check_elf_processes())

        # Git status
        metrics.append(self._check_git_status())

        # Lock file check
        metrics.append(self._check_stale_locks())

        # Recent errors in logs
        metrics.append(self._check_recent_errors())

        return metrics

    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            # Read /proc/loadavg for load average
            with open("/proc/loadavg", "r") as f:
                load = f.read().strip().split()
                load_1m = float(load[0])
                load_5m = float(load[1])

            # Determine status based on load (assuming 4 cores)
            cores = 4
            load_per_core = load_1m / cores

            if load_per_core > 2.0:
                status = "critical"
            elif load_per_core > 1.0:
                status = "warning"
            else:
                status = "ok"

            return {
                "name": "cpu_load_1m",
                "value": load_1m,
                "unit": "load",
                "status": status,
                "thresholds": {"warning": 4.0, "critical": 8.0},
            }
        except Exception as e:
            return {
                "name": "cpu_load",
                "value": None,
                "unit": "load",
                "status": "error",
                "error": str(e),
            }

    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()

            total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1)) // 1024
            available = (
                int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1)) // 1024
            )
            used = total - available
            percent = (used / total) * 100

            if percent > 90:
                status = "critical"
            elif percent > 80:
                status = "warning"
            else:
                status = "ok"

            return {
                "name": "memory_percent",
                "value": round(percent, 1),
                "unit": "%",
                "status": status,
                "thresholds": {"warning": 80, "critical": 90},
                "details": {"used_mb": used, "total_mb": total},
            }
        except Exception as e:
            return {
                "name": "memory_percent",
                "value": None,
                "unit": "%",
                "status": "error",
                "error": str(e),
            }

    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage for ELF directory."""
        try:
            usage = shutil.disk_usage(str(self.elf_dir))
            free_gb = usage.free / (1024**3)
            percent = (usage.used / usage.total) * 100

            if percent > 95:
                status = "critical"
            elif percent > 85:
                status = "warning"
            else:
                status = "ok"

            return {
                "name": "disk_percent",
                "value": round(percent, 1),
                "unit": "%",
                "status": status,
                "thresholds": {"warning": 85, "critical": 95},
                "details": {"free_gb": round(free_gb, 2)},
            }
        except Exception as e:
            return {
                "name": "disk_percent",
                "value": None,
                "unit": "%",
                "status": "error",
                "error": str(e),
            }

    def _check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity."""
        try:
            if not self.db_path.exists():
                return {
                    "name": "db_integrity",
                    "value": "missing",
                    "unit": "",
                    "status": "critical",
                }

            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "ok":
                return {
                    "name": "db_integrity",
                    "value": "ok",
                    "unit": "",
                    "status": "ok",
                }
            else:
                return {
                    "name": "db_integrity",
                    "value": result[0] if result else "unknown",
                    "unit": "",
                    "status": "critical",
                }
        except Exception as e:
            return {
                "name": "db_integrity",
                "value": None,
                "unit": "",
                "status": "error",
                "error": str(e),
            }

    def _check_database_size(self) -> Dict[str, Any]:
        """Check database size."""
        try:
            if not self.db_path.exists():
                size_mb = 0
            else:
                size_mb = round(self.db_path.stat().st_size / (1024 * 1024), 2)

            # Warning at 100MB, critical at 500MB
            if size_mb > 500:
                status = "critical"
            elif size_mb > 100:
                status = "warning"
            else:
                status = "ok"

            return {
                "name": "db_size_mb",
                "value": size_mb,
                "unit": "MB",
                "status": status,
                "thresholds": {"warning": 100, "critical": 500},
            }
        except Exception as e:
            return {
                "name": "db_size_mb",
                "value": None,
                "unit": "MB",
                "status": "error",
                "error": str(e),
            }

    def _check_elf_processes(self) -> List[Dict[str, Any]]:
        """Check if ELF processes are running."""
        metrics = []

        # Check for EventBridge
        try:
            result = subprocess.run(
                ["pgrep", "-f", "event_bridge"], capture_output=True, text=True
            )
            event_bridge_running = result.returncode == 0
            metrics.append(
                {
                    "name": "process_event_bridge",
                    "value": "running" if event_bridge_running else "stopped",
                    "unit": "",
                    "status": "ok" if event_bridge_running else "warning",
                }
            )
        except:
            pass

        # Check for LearningProcessor
        try:
            result = subprocess.run(
                ["pgrep", "-f", "learning_processor"], capture_output=True, text=True
            )
            lp_running = result.returncode == 0
            metrics.append(
                {
                    "name": "process_learning_processor",
                    "value": "running" if lp_running else "stopped",
                    "unit": "",
                    "status": "ok" if lp_running else "info",
                }
            )
        except:
            pass

        return metrics

    def _check_git_status(self) -> Dict[str, Any]:
        """Check git repository status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.elf_dir),
                capture_output=True,
                text=True,
            )

            # Count uncommitted files
            uncommitted = (
                len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            )

            status = "ok"
            if uncommitted > 20:
                status = "warning"
            elif uncommitted > 50:
                status = "critical"

            return {
                "name": "git_uncommitted",
                "value": uncommitted,
                "unit": "files",
                "status": status,
                "thresholds": {"warning": 20, "critical": 50},
            }
        except Exception as e:
            return {
                "name": "git_uncommitted",
                "value": None,
                "unit": "files",
                "status": "error",
                "error": str(e),
            }

    def _check_stale_locks(self) -> Dict[str, Any]:
        """Check for stale lock files."""
        try:
            if not LOCK_DIR.exists():
                return {
                    "name": "stale_locks",
                    "value": 0,
                    "unit": "files",
                    "status": "ok",
                }

            locks = list(LOCK_DIR.glob("*.lock"))
            stale_count = 0

            # Check for locks older than 1 hour
            one_hour_ago = datetime.now().timestamp() - 3600
            for lock in locks:
                if lock.stat().st_mtime < one_hour_ago:
                    stale_count += 1

            status = "ok"
            if stale_count > 5:
                status = "warning"
            elif stale_count > 10:
                status = "critical"

            return {
                "name": "stale_locks",
                "value": stale_count,
                "unit": "files",
                "status": status,
                "thresholds": {"warning": 5, "critical": 10},
            }
        except Exception as e:
            return {
                "name": "stale_locks",
                "value": None,
                "unit": "files",
                "status": "error",
                "error": str(e),
            }

    def _check_recent_errors(self) -> Dict[str, Any]:
        """Check for recent errors in logs."""
        try:
            error_count = 0

            # Check last 100 lines of latest log file
            latest_log = (
                sorted(LOGS_DIR.glob("*.log"))[-1]
                if LOGS_DIR.exists() and list(LOGS_DIR.glob("*.log"))
                else None
            )

            if latest_log and latest_log.exists():
                with open(latest_log, "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:]  # Last 100 lines
                    error_count = sum(
                        1
                        for line in recent_lines
                        if "[ERROR]" in line or "[CRITICAL]" in line
                    )

            status = "ok"
            if error_count > 10:
                status = "warning"
            elif error_count > 50:
                status = "critical"

            return {
                "name": "recent_errors",
                "value": error_count,
                "unit": "errors",
                "status": status,
                "thresholds": {"warning": 10, "critical": 50},
            }
        except Exception as e:
            return {
                "name": "recent_errors",
                "value": None,
                "unit": "errors",
                "status": "error",
                "error": str(e),
            }

    # =========================================================================
    # ALERT GENERATION
    # =========================================================================

    def generate_alerts(self, metrics: List[Dict[str, Any]]) -> List[Alert]:
        """Generate alerts from metrics."""
        alerts = []

        for metric in metrics:
            status = metric.get("status", "ok")

            if status == "critical":
                alert = Alert(
                    id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{metric['name']}",
                    tier="sentinel",
                    category=metric["name"],
                    severity="critical",
                    message=f"CRITICAL: {metric['name']} = {metric.get('value', 'N/A')} {metric.get('unit', '')}",
                    metric=metric,
                )
                alerts.append(alert)
            elif status == "warning":
                alert = Alert(
                    id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{metric['name']}",
                    tier="sentinel",
                    category=metric["name"],
                    severity="warning",
                    message=f"WARNING: {metric['name']} = {metric.get('value', 'N/A')} {metric.get('unit', '')}",
                    metric=metric,
                )
                alerts.append(alert)

        return alerts

    def save_alerts(self, alerts: List[Alert]):
        """Save alerts to database."""
        if not self.db_path.exists() or not alerts:
            return

        try:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            for alert in alerts:
                cursor.execute(
                    """
                    INSERT INTO alerts (alert_id, tier, category, severity, message, metric, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert.id,
                        alert.tier,
                        alert.category,
                        alert.severity,
                        alert.message,
                        str(alert.metric),
                        alert.created_at,
                    ),
                )

            conn.commit()
            conn.close()
            logger.info(f"💾 Saved {len(alerts)} alerts to database")

        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")

    # =========================================================================
    # AUTO-REPAIRS (Simple repairs for Sentinel tier)
    # =========================================================================

    def simple_repairs(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """
        Attempt simple auto-repairs for alerts.

        Returns list of repair actions taken.
        """
        repairs = []

        for alert in alerts:
            # Clean old logs for disk space issues
            if alert.category == "disk_percent" and alert.severity == "warning":
                repair = self._clean_old_logs()
                if repair["success"]:
                    repairs.append(repair)

            # Clean stale locks
            if alert.category == "stale_locks" and alert.severity in [
                "warning",
                "critical",
            ]:
                repair = self._clean_stale_locks()
                if repair["success"]:
                    repairs.append(repair)

            # Restart EventBridge if not running
            if alert.category == "process_event_bridge" and alert.severity == "warning":
                repair = self._restart_event_bridge()
                if repair["success"]:
                    repairs.append(repair)

        return repairs

    def _clean_old_logs(self) -> Dict[str, Any]:
        """Clean logs older than 7 days."""
        try:
            seven_days_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
            cleaned = 0

            if LOGS_DIR.exists():
                for log_file in LOGS_DIR.glob("*.log"):
                    if log_file.stat().st_mtime < seven_days_ago:
                        log_file.unlink()
                        cleaned += 1

            return {
                "action": "clean_old_logs",
                "success": True,
                "files_cleaned": cleaned,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"action": "clean_old_logs", "success": False, "error": str(e)}

    def _clean_stale_locks(self) -> Dict[str, Any]:
        """Clean locks older than 1 hour."""
        try:
            one_hour_ago = datetime.now().timestamp() - 3600
            cleaned = 0

            if LOCK_DIR.exists():
                for lock_file in LOCK_DIR.glob("*.lock"):
                    if lock_file.stat().st_mtime < one_hour_ago:
                        lock_file.unlink()
                        cleaned += 1

            return {
                "action": "clean_stale_locks",
                "success": True,
                "files_cleaned": cleaned,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"action": "clean_stale_locks", "success": False, "error": str(e)}

    def _restart_event_bridge(self) -> Dict[str, Any]:
        """Restart EventBridge process."""
        try:
            # Find the EventBridge script
            eb_script = self.elf_dir / "core" / "event_bridge_v2.py"

            if not eb_script.exists():
                return {
                    "action": "restart_event_bridge",
                    "success": False,
                    "error": "Script not found",
                }

            # Kill existing processes
            subprocess.run(["pkill", "-f", "event_bridge_v2"], capture_output=True)

            # Start new process in background
            subprocess.Popen(
                [sys.executable, str(eb_script), "start"],
                cwd=str(self.elf_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return {
                "action": "restart_event_bridge",
                "success": True,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"action": "restart_event_bridge", "success": False, "error": str(e)}

    # =========================================================================
    # MAIN
    # =========================================================================

    def run(self, mode: str = "collect"):
        """Run the monitor agent in specified mode."""
        if mode == "collect":
            metrics = self.collect_metrics()
            print("\n📊 MonitorAgent Metrics:")
            print("-" * 60)
            for m in metrics:
                status_icon = {
                    "ok": "✅",
                    "warning": "⚠️",
                    "critical": "🚨",
                    "error": "❌",
                }.get(m.get("status"), "?")
                value = m.get("value", "N/A")
                unit = m.get("unit", "")
                print(f"  {status_icon} {m['name']}: {value}{unit}")
            print("-" * 60)

        elif mode == "check":
            metrics = self.collect_metrics()
            alerts = self.generate_alerts(metrics)
            self.save_alerts(alerts)

            print(f"\n📊 Collected {len(metrics)} metrics")
            print(f"🚨 Generated {len(alerts)} alerts")

            for alert in alerts:
                icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(
                    alert.severity, "?"
                )
                print(f"  {icon} [{alert.severity.upper()}] {alert.message}")

        elif mode == "auto-repair":
            metrics = self.collect_metrics()
            alerts = self.generate_alerts(metrics)
            repairs = self.simple_repairs(alerts)

            print(f"\n🔧 Performed {len(repairs)} auto-repairs:")
            for repair in repairs:
                icon = "✅" if repair["success"] else "❌"
                print(
                    f"  {icon} {repair.get('action', 'unknown')}: {repair.get('files_cleaned', 0)} files"
                )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MonitorAgent")
    parser.add_argument(
        "mode",
        choices=["collect", "check", "auto-repair"],
        help="collect: Gather metrics, check: Check and generate alerts, auto-repair: Attempt repairs",
    )

    args = parser.parse_args()

    agent = MonitorAgent()
    agent.run(args.mode)


if __name__ == "__main__":
    main()
