"""
ELF Watcher Watchdog

A lightweight watchdog service that monitors the Watcher agent's log file
and restarts it if no updates are detected for 15 minutes.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent  # emergent-learning root
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Import centralized logger
try:
    from Open_ELF.utils import elf_logging

    logger = elf_logging.get_logger("watchdog_sentinel")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("watchdog_sentinel")

# Configuration
WATCHER_LOG_PATH = ELF_DIR / "logs" / "elf_sentinel.log"
WATCHER_SCRIPT_PATH = ELF_DIR / "Open_ELF" / "sentinel" / "elf_sentinel.py"
MONITOR_INTERVAL = 30  # Check every 30 seconds
WATCHER_TIMEOUT = 900  # 15 minutes (900 seconds) timeout


def get_last_log_timestamp():
    """Get the timestamp of the last log entry in Watcher log."""
    try:
        if not WATCHER_LOG_PATH.exists():
            logger.warning(f"Watcher log file not found: {WATCHER_LOG_PATH}")
            return None

        with open(WATCHER_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Look for the last log line
        for line in reversed(lines):
            if line.strip() and "- elf.elf_sentinel - " in line:
                # Extract timestamp from line format: "2026-02-08 21:35:10 - elf.elf_sentinel - INFO - ..."
                parts = line.split(" - ")
                if len(parts) >= 3:
                    timestamp_str = parts[0]
                    try:
                        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
        logger.warning("No valid log entries found in Watcher log")
        return None
    except Exception as e:
        logger.error(f"Error reading Watcher log: {e}")
        return None


def is_sentinel_running():
    """Check if Watcher process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", str(WATCHER_SCRIPT_PATH)], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking Watcher process: {e}")
        return False


def start_sentinel():
    """Start the Watcher agent."""
    try:
        # Kill any existing Watcher process first
        subprocess.run(["pkill", "-f", str(WATCHER_SCRIPT_PATH)], capture_output=True)

        # Start new Watcher process
        process = subprocess.Popen(
            [sys.executable, str(WATCHER_SCRIPT_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(f"Started Watcher with PID: {process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start Watcher: {e}")
        return False


def monitor_sentinel():
    """Main watchdog monitoring loop."""
    logger.info("🚀 ELF Watcher Watchdog started")
    logger.info(f"Monitoring: {WATCHER_LOG_PATH}")
    logger.info(f"Timeout: {WATCHER_TIMEOUT} seconds ({WATCHER_TIMEOUT / 60} minutes)")

    last_known_good_time = None
    last_log_timestamp = None

    while True:
        try:
            # Get current time
            now = datetime.now()

            # Get last log timestamp
            last_log_timestamp = get_last_log_timestamp()

            if last_log_timestamp is not None:
                last_known_good_time = last_log_timestamp
                logger.debug(f"Last log entry: {last_log_timestamp}")
            else:
                logger.debug("No valid log entries found")

            # Check if we need to restart Watcher
            if last_known_good_time:
                time_since_last_log = (now - last_known_good_time).total_seconds()

                if time_since_last_log > WATCHER_TIMEOUT:
                    logger.warning(
                        f"⚠️  Watcher has been unresponsive for {time_since_last_log:.0f} seconds (> {WATCHER_TIMEOUT}s)"
                    )

                    # Check if Watcher is still running
                    if is_sentinel_running():
                        logger.info("Restarting Watcher process...")

                        # Kill existing process
                        subprocess.run(
                            ["pkill", "-f", str(WATCHER_SCRIPT_PATH)],
                            capture_output=True,
                        )

                        # Start new process
                        if start_sentinel():
                            logger.info("✅ Watcher restarted successfully")

                            # Log the restart to database if available
                            try:
                                from Open_ELF.utils.elf_logging import log_event

                                log_event(
                                    event_type="watchdog_restart",
                                    source="watchdog_sentinel",
                                    summary="Watcher restarted due to timeout",
                                    data={
                                        "time_since_last_log": time_since_last_log,
                                        "last_log_time": last_known_good_time.isoformat(),
                                    },
                                )
                            except ImportError:
                                pass
                        else:
                            logger.error("❌ Failed to restart Watcher")
                    else:
                        logger.info("Watcher not running, starting...")
                        if start_sentinel():
                            logger.info("✅ Watcher started successfully")
                        else:
                            logger.error("❌ Failed to start Watcher")

            # Monitor every 30 seconds
            time.sleep(MONITOR_INTERVAL)

        except KeyboardInterrupt:
            logger.info("⏹️ Watchdog stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Watchdog error: {e}")
            time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    monitor_sentinel()
