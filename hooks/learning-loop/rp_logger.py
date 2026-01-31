#!/usr/bin/env python3
"""
Logger for record_pheromone.py
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


logger = setup_logger("record_pheromone")


def log_start():
    logger.info("Starting record_pheromone function")


def log_success(msg="Function completed successfully"):
    logger.info(f"SUCCESS: {msg}")


def log_error(error):
    logger.error(f"ERROR: {error}")


def log_partial(msg):
    logger.warning(f"PARTIAL: {msg}")


def log_info(msg):
    logger.info(f"INFO: {msg}")


if __name__ == "__main__":
    log_start()
    print("Logger ready for record_pheromone")
