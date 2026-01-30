#!/usr/bin/env python3
"""
ELF Learning Daemon - Continuously monitors for unprocessed session logs
and triggers learning extraction when new logs are available.

This daemon runs in the background like the sentinel, checking every 5 minutes
for new session logs that haven't been processed by the learning extractor.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Paths
EMERGENT_LEARNING_PATH = Path(__file__).resolve().parent.parent
SESSIONS_LOGS_DIR = EMERGENT_LEARNING_PATH / "sessions" / "logs"
PROCESSED_MARKER = EMERGENT_LEARNING_PATH / "sessions" / ".processed"
EXTRACTOR_SCRIPT = (
    EMERGENT_LEARNING_PATH / "agents" / "learning-extractor" / "run_extractor.py"
)


def log_message(level, message):
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()


def get_unprocessed_files():
    """Get list of unprocessed log files."""
    if not SESSIONS_LOGS_DIR.exists():
        return []

    # Get all session log files
    log_files = list(SESSIONS_LOGS_DIR.glob("*_session.jsonl"))
    if not log_files:
        return []

    # If no processed marker exists, all files are unprocessed
    if not PROCESSED_MARKER.exists():
        return log_files

    # Load processed files
    try:
        with open(PROCESSED_MARKER, "r") as f:
            data = json.load(f)
            processed_files = set(data.get("processed_files", []))
    except (json.JSONDecodeError, IOError):
        processed_files = set()

    # Filter out processed files
    unprocessed = []
    for f in log_files:
        if f.name not in processed_files:
            unprocessed.append(f)

    return unprocessed


def trigger_learning_extractor(log_files):
    """Trigger the learning extractor for the given log files."""
    if not EXTRACTOR_SCRIPT.exists():
        log_message("ERROR", f"Learning extractor script not found: {EXTRACTOR_SCRIPT}")
        return False

    if not log_files:
        return True

    try:
        # Build command
        cmd = [sys.executable, str(EXTRACTOR_SCRIPT)] + [str(f) for f in log_files]

        # Run extractor in background
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        log_message(
            "INFO", f"Triggered learning extractor for {len(log_files)} file(s)"
        )
        return True

    except Exception as e:
        log_message("ERROR", f"Failed to trigger learning extractor: {e}")
        return False


def main():
    """Main daemon loop."""
    log_message("INFO", "ELF Learning Daemon started")
    log_message("INFO", f"Monitoring: {SESSIONS_LOGS_DIR}")
    log_message("INFO", f"Extractor: {EXTRACTOR_SCRIPT}")

    # Check interval (5 minutes)
    check_interval = 300

    try:
        while True:
            try:
                # Check for unprocessed files
                unprocessed_files = get_unprocessed_files()

                if unprocessed_files:
                    log_message(
                        "INFO",
                        f"Found {len(unprocessed_files)} unprocessed log file(s)",
                    )
                    trigger_learning_extractor(unprocessed_files)
                else:
                    log_message("DEBUG", "No unprocessed log files found")

                # Wait before next check
                time.sleep(check_interval)

            except KeyboardInterrupt:
                log_message("INFO", "Received interrupt signal, shutting down...")
                break
            except Exception as e:
                log_message("ERROR", f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    except Exception as e:
        log_message("ERROR", f"Fatal error: {e}")
        sys.exit(1)
    finally:
        log_message("INFO", "ELF Learning Daemon stopped")


if __name__ == "__main__":
    main()
