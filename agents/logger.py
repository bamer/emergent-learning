#!/usr/bin/env python3
"""
Centralized logging module for ELF agents
Ensures all agents log to the same directory with consistent formatting
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os

# Centralized log directory - Use Open_ELF/logs for unified logging
LOG_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, level=logging.INFO):
    """Setup a standardized logger for ELF agents."""

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger

    # Create formatter with consistent format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - all logs go to the same directory
    log_file = LOG_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def log_critical_error(component: str, error: str):
    """
    Log a critical error and potentially crash the system.
    This implements the "it works or it crashes" policy.
    """
    logger = setup_logger("critical_errors")
    logger.critical(f"CRITICAL FAILURE in {component}: {error}")

    # For now, we'll log the error. In production, we might want to actually crash.
    # Uncomment the next line to enable actual crashing on critical errors:
    # raise SystemExit(f"Critical error in {component}: {error}")


def log_system_event(event_type: str, component: str, details: str = ""):
    """Log system events for monitoring purposes."""
    logger = setup_logger("system_events")
    message = f"{event_type} - {component}"
    if details:
        message += f" - {details}"
    logger.info(message)
