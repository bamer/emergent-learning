"""
ELF Sentinel Watchdog

A lightweight watchdog service that monitors the Sentinel agent's log file
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
SENTINEL_LOG_PATH = ELF_DIR / "logs" / "elf_sentinel.log"
SENTINEL_SCRIPT_PATH = ELF_DIR / "Open_ELF" / "sentinel" / "elf_sentinel.py"
MONITOR_INTERVAL = 30  # Check every 30 seconds
SENTINEL_TIMEOUT = 900  # 15 minutes (900 seconds) timeout


def get_last_log_timestamp():
    """Get the timestamp of the last log entry in Sentinel log."""
    try:
        if not SENTINEL_LOG_PATH.exists():
            logger.warning(f"Sentinel log file not found: {SENTINEL_LOG_PATH}")
            return None

        with open(SENTINEL_LOG_PATH, "r", encoding="utf-8") as f:
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
        logger.warning("No valid log entries found in Sentinel log")
        return None
    except Exception as e:
        logger.error(f"Error reading Sentinel log: {e}")
        return None


def is_sentinel_running():
    """Check if Sentinel process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", str(SENTINEL_SCRIPT_PATH)], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking Sentinel process: {e}")
        return False


def start_sentinel():
    """Start the Sentinel agent."""
    try:
        # Kill any existing Sentinel process first
        subprocess.run(["pkill", "-f", str(SENTINEL_SCRIPT_PATH)], capture_output=True)

        # Start new Sentinel process
        process = subprocess.Popen(
            [sys.executable, str(SENTINEL_SCRIPT_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(f"Started Sentinel with PID: {process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start Sentinel: {e}")
        return False


def monitor_sentinel():
    """Main watchdog monitoring loop."""
    logger.info("🚀 ELF Sentinel Watchdog started")
    logger.info(f"Monitoring: {SENTINEL_LOG_PATH}")
    logger.info(f"Timeout: {SENTINEL_TIMEOUT} seconds ({SENTINEL_TIMEOUT / 60} minutes)")

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

            # Check if we need to restart Sentinel
            if last_known_good_time:
                time_since_last_log = (now - last_known_good_time).total_seconds()

                if time_since_last_log > SENTINEL_TIMEOUT:
                    logger.warning(
                        f"⚠️  Sentinel has been unresponsive for {time_since_last_log:.0f} seconds (> {SENTINEL_TIMEOUT}s)"
                    )

                    # Check if Sentinel is still running
                    if is_sentinel_running():
                        logger.info("Restarting Sentinel process...")

                        # Kill existing process
                        subprocess.run(
                            ["pkill", "-f", str(SENTINEL_SCRIPT_PATH)],
                            capture_output=True,
                        )

                        # Start new process
                        if start_sentinel():
                            logger.info("✅ Sentinel restarted successfully")

                            # Log the restart to database if available
                            try:
                                from Open_ELF.utils.elf_logging import log_event

                                log_event(
                                    event_type="watchdog_restart",
                                    source="watchdog_sentinel",
                                    summary="Sentinel restarted due to timeout",
                                    data={
                                        "time_since_last_log": time_since_last_log,
                                        "last_log_time": last_known_good_time.isoformat(),
                                    },
                                )
                            except ImportError:
                                pass
                        else:
                            logger.error("❌ Failed to restart Sentinel")
                    else:
                        logger.info("Sentinel not running, starting...")
                        if start_sentinel():
                            logger.info("✅ Sentinel started successfully")
                        else:
                            logger.error("❌ Failed to start Sentinel")

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
