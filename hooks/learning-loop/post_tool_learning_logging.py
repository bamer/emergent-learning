#!/usr/bin/env python3
"""
Enhanced version of post_tool_learning.py with comprehensive logging.
"""

import logging
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str) -> logging.Logger:
    """Setup logger for the function."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# Create logger
logger = setup_logger("post_tool_learning")


def log_start():
    """Log function start."""
    logger.info("Starting post_tool_learning function")


def log_success(message: str = "Function completed successfully"):
    """Log successful completion."""
    logger.info(f"SUCCESS: {message}")


def log_error(error: str):
    """Log error."""
    logger.error(f"ERROR: {error}")


def log_partial(message: str):
    """Log partial success."""
    logger.warning(f"PARTIAL: {message}")


def log_info(message: str):
    """Log info."""
    logger.info(f"INFO: {message}")


if __name__ == "__main__":
    log_start()
    print("Logging setup complete for post_tool_learning")
