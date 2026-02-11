#!/usr/bin/env python3
"""
Open_ELF Unified Logging System
Provides standardized logging across all Open_ELF components

=====================================================================
DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
THIS IS MANDATORY: ALL LOGS MUST GO TO 
/home/bamer/.opencode/emergent-learning/Open_ELF/logs/
ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
=====================================================================
"""

import logging as std_logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ColorFormatter(logging.Formatter):
    """Adds ANSI color codes to log records based on severity."""

    COLORS = {
        logging.DEBUG: "\033[94m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[93m",  # Bright Yellow
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        formatted = super().format(record)
        return f"{color}{formatted}{self.RESET}"


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record):
        import json

        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "component": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_entry.update(record.extra)

        return json.dumps(log_entry)


class OpenELFLogger:
    """
    Unified logging wrapper for Open_ELF components.
    
    =====================================================================
    DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
    THIS IS MANDATORY: ALL LOGS MUST GO TO 
    /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
    ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
    =====================================================================
    """

    # MANDATORY LOGS DIRECTORY - DO NOT CHANGE
    LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF/logs")

    def __init__(self, component: str, level: int = logging.INFO):
        self.component = component
        self.logger = logging.getLogger(f"openelf.{component}")
        self.logger.setLevel(level)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup file and console handlers with standardized formatting."""

        # Ensure logs directory exists
        self.LOGS_DIR.mkdir(exist_ok=True)

        # File handler with rotation
        log_file = self.LOGS_DIR / f"{self.component}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Console handler with colors
        console_handler = logging.StreamHandler()
        color_formatter = ColorFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(color_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @classmethod
    def setup_logging(cls, component: str, level: int = logging.INFO) -> logging.Logger:
        """Set up or retrieve a logger for the specified component."""
        logger_instance = cls(component, level)
        return logger_instance.logger

    @classmethod
    def get_logger(cls, component: str) -> logging.Logger:
        """Retrieve the configured logger for the component."""
        return logging.getLogger(f"openelf.{component}")

    @classmethod
    def structured_log(cls, level: str, component: str, message: str, **kwargs):
        """Log a structured message with optional components."""
        logger = cls.setup_logging(component)
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Create log record with extra fields
        extra_fields = {k: v for k, v in kwargs.items() if not k.startswith("_")}

        if log_level == logging.DEBUG:
            logger.debug(message, extra=extra_fields)
        elif log_level == logging.INFO:
            logger.info(message, extra=extra_fields)
        elif log_level == logging.WARNING:
            logger.warning(message, extra=extra_fields)
        elif log_level == logging.ERROR:
            logger.error(message, extra=extra_fields)
        elif log_level == logging.CRITICAL:
            logger.critical(message, extra=extra_fields)


# Public API functions
def setup_logging(component: str, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for a component."""
    return OpenELFLogger.setup_logging(component, level)


def get_logger(component: str) -> logging.Logger:
    """Get logger for a component."""
    return OpenELFLogger.get_logger(component)


def structured_log(level: str, component: str, message: str, **kwargs):
    """Log structured message."""
    return OpenELFLogger.structured_log(level, component, message, **kwargs)


# Example usage
if __name__ == "__main__":
    # Setup logger
    logger = setup_logging("test_component", logging.DEBUG)
    logger.debug("Test debug message")
    logger.info("Test info message")

    # Structured logging
    structured_log(
        "INFO", "payment_processor", "Payment succeeded", amount=99.99, currency="USD"
    )
