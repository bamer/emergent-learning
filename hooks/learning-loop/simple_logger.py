#!/usr/bin/env python3
"""
Simple logger for post_tool_learning.py - non-intrusive approach
"""

import sys
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"


def log_message(level: str, message: str):
    """Simple log function that won't interfere."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] [post_tool_learning] {message}\n")


def log_start():
    log_message("INFO", "=== FUNCTION START ===")


def log_success(message: str = "Function completed successfully"):
    log_message("INFO", f"SUCCESS: {message}")


def log_error(error: str):
    log_message("ERROR", f"ERROR: {error}")


def log_partial(message: str):
    log_message("WARNING", f"PARTIAL: {message}")


def log_info(message: str):
    log_message("INFO", f"INFO: {message}")


if __name__ == "__main__":
    log_start()
    print("Simple logger ready")
