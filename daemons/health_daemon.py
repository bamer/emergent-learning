#!/usr/bin/env python3
"""
Health Check Daemon for Emergent Learning Framework

Continuously monitors system health and writes metrics to system_health table every 10 seconds.

Monitors:
- Database integrity (PRAGMA integrity_check)
- Database size
- Disk free space
- Git repository status
- Stale locks count

Requirements: Python 3.7+, sqlite3, shutil
"""

import os
import sys
import sqlite3
import json
import time
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
LOG_FILE = (
    Path.home() / ".opencode" / "emergent-learning" / "logs" / "health-daemon.log"
)
PID_FILE = Path.home() / ".opencode" / "emergent-learning" / "health-daemon.pid"
LOCK_DIR = Path.home() / ".opencode" / "emergent-learning" / "locks"

# Configure logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class HealthDaemon:
    """Health monitoring daemon."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.running = True

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        LOCK_DIR.mkdir(parents=True, exist_ok=True)

    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings for concurrent access."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Use WAL mode for concurrent writes
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def check_database_integrity(self) -> str:
        """Check database integrity using PRAGMA integrity_check."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "ok":
                return "ok"
            else:
                return str(result[0]) if result else "unknown"
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return f"error: {e}"

    def get_database_size(self) -> float:
        """Get database size in MB."""
        try:
            if self.db_path.exists():
                size_bytes = self.db_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0.0

    def get_disk_free_space(self) -> float:
        """Get free disk space in MB."""
        try:
            # Get disk usage for the directory containing the database
            stat = shutil.disk_usage(self.db_path.parent)
            free_mb = round(stat.free / (1024 * 1024), 2)
            return free_mb
        except Exception as e:
            logger.error(f"Failed to get disk space: {e}")
            return 0.0

    def get_git_status(self) -> str:
        """Get git repository status."""
        try:
            # Get status from the project root
            project_root = Path.home() / ".opencode" / "emergent-learning"

            # Check if we're in a git repo
            git_dir = project_root / ".git"
            if not git_dir.exists():
                return "not_a_repo"

            # Get git status
            result = subprocess.run(
                ["git", "-C", str(project_root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return f"error: {result.stderr.strip()}"

            # Count changes
            changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
            modified = len([c for c in changes if c.startswith(" M")])
            added = len([c for c in changes if c.startswith("??")])
            staged = len(
                [
                    c
                    for c in changes
                    if c and not c.startswith("??") and not c.startswith(" M")
                ]
            )

            if not any(changes):
                return "clean"

            status_parts = []
            if modified > 0:
                status_parts.append(f"{modified} modified")
            if added > 0:
                status_parts.append(f"{added} untracked")
            if staged > 0:
                status_parts.append(f"{staged} staged")

            return ", ".join(status_parts)

        except subprocess.TimeoutExpired:
            return "timeout"
        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return f"error: {e}"

    def count_stale_locks(self) -> int:
        """Count stale lock files."""
        try:
            if not LOCK_DIR.exists():
                return 0

            current_time = time.time()
            stale_count = 0

            # Consider locks older than 1 hour as stale
            stale_threshold = 3600  # 1 hour in seconds

            for lock_file in LOCK_DIR.glob("*.lock"):
                if lock_file.is_file():
                    # Check file modification time
                    mtime = lock_file.stat().st_mtime
                    if current_time - mtime > stale_threshold:
                        stale_count += 1
                        # Optionally remove stale locks
                        try:
                            lock_file.unlink()
                            logger.info(f"Removed stale lock: {lock_file.name}")
                        except Exception as e:
                            logger.warning(
                                f"Could not remove stale lock {lock_file.name}: {e}"
                            )

            return stale_count
        except Exception as e:
            logger.error(f"Failed to count stale locks: {e}")
            return 0

    def collect_health_metrics(self) -> Dict[str, Any]:
        """Collect all health metrics."""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "db_integrity": self.check_database_integrity(),
            "db_size_mb": self.get_database_size(),
            "disk_free_mb": self.get_disk_free_space(),
            "git_status": self.get_git_status(),
            "stale_locks": self.count_stale_locks(),
            "details": None,
        }

        # Determine overall status
        status_parts = []

        if metrics["db_integrity"] != "ok":
            status_parts.append("db_error")
        if metrics["disk_free_mb"] < 100:  # Less than 100MB free
            status_parts.append("low_disk")
        if metrics["stale_locks"] > 0:
            status_parts.append("stale_locks")
        if "error:" in metrics["git_status"]:
            status_parts.append("git_error")

        if status_parts:
            metrics["status"] = "warning"
            metrics["details"] = f"Issues: {', '.join(status_parts)}"
        else:
            metrics["status"] = "healthy"

        return metrics

    def write_health_record(self, metrics: Dict[str, Any]) -> bool:
        """Write health metrics to database."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    db_integrity TEXT,
                    db_size_mb REAL,
                    disk_free_mb REAL,
                    git_status TEXT,
                    stale_locks INTEGER DEFAULT 0,
                    details TEXT
                )
            """)

            # Insert record
            cursor.execute(
                """
                INSERT INTO system_health (
                    timestamp, status, db_integrity, db_size_mb, 
                    disk_free_mb, git_status, stale_locks, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics["timestamp"],
                    metrics["status"],
                    metrics["db_integrity"],
                    metrics["db_size_mb"],
                    metrics["disk_free_mb"],
                    metrics["git_status"],
                    metrics["stale_locks"],
                    metrics["details"],
                ),
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Health record written: {metrics['status']} "
                f"(DB: {metrics['db_integrity']}, "
                f"Disk: {metrics['disk_free_mb']}MB, "
                f"Git: {metrics['git_status']}, "
                f"Locks: {metrics['stale_locks']})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write health record: {e}")
            return False

    def run_once(self) -> bool:
        """Run one health check cycle."""
        try:
            metrics = self.collect_health_metrics()
            return self.write_health_record(metrics)
        except Exception as e:
            logger.error(f"Health check cycle failed: {e}")
            return False

    def run_daemon(self, interval: int = 10):
        """Run the daemon continuously."""
        logger.info(f"Starting health daemon with {interval}s interval")

        # Write PID file
        try:
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")

        try:
            while self.running:
                start_time = time.time()

                # Run health check
                success = self.run_once()
                if not success:
                    logger.warning("Health check failed, continuing...")

                # Calculate remaining sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)

                # Sleep with interruption handling
                for _ in range(int(sleep_time * 10)):
                    if not self.running:
                        break
                    time.sleep(0.1)

                if not self.running:
                    break

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")

        # Cleanup
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
            logger.info("Health daemon stopped")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def stop(self):
        """Stop the daemon."""
        self.running = False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Health Check Daemon for Emergent Learning Framework"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Check interval in seconds (default: 10)",
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--stop", action="store_true", help="Stop running daemon")
    parser.add_argument(
        "--status", action="store_true", help="Check if daemon is running"
    )

    args = parser.parse_args()

    # Handle stop command
    if args.stop:
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)  # SIGTERM
                logger.info(f"Sent stop signal to daemon PID {pid}")
            except (ValueError, ProcessLookupError, FileNotFoundError) as e:
                logger.error(f"Failed to stop daemon: {e}")
                if PID_FILE.exists():
                    PID_FILE.unlink()
        else:
            logger.info("No daemon PID file found")
        return

    # Handle status command
    if args.status:
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                # Check if process exists
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                logger.info(f"Daemon running with PID {pid}")
            except (ValueError, ProcessLookupError, FileNotFoundError):
                logger.info("Daemon is not running (stale PID file)")
                if PID_FILE.exists():
                    PID_FILE.unlink()
        else:
            logger.info("Daemon is not running")
        return

    # Create daemon instance
    daemon = HealthDaemon()

    # Run once if requested
    if args.once:
        success = daemon.run_once()
        sys.exit(0 if success else 1)

    # Run daemon
    try:
        daemon.run_daemon(interval=args.interval)
    except Exception as e:
        logger.error(f"Daemon crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
