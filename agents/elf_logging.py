"""
ELF Centralized Logging System
==============================

All agents and daemons MUST use this logging system.
Logs are written to: /home/bamer/.opencode/emergent-learning/logs/

Usage:
    from elf_logging import get_logger, log_critical, log_error, log_warning, log_info

    logger = get_logger("my_agent")
    logger.info("Message")

    # Or use direct functions:
    log_critical("my_agent", "Critical message", crash=True)  # Will crash the system
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Central log directory - ALL logs go here
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Crash log file for critical errors
CRASH_LOG = LOGS_DIR / "CRASH.log"

# Track if we've already crashed (to avoid infinite crash loops)
_has_crashed = False


class CrashPolicyHandler(logging.Handler):
    """
    Handler that enforces the 'ça marche ou ça crash' policy.
    Critical errors will crash the system rather than fail silently.
    """

    def emit(self, record):
        if record.levelno >= logging.CRITICAL:
            self._handle_crash(record)

    def _handle_crash(self, record):
        """Handle critical crash - log and exit."""
        global _has_crashed

        if _has_crashed:
            return  # Prevent infinite loops

        _has_crashed = True

        crash_info = f"""
{"=" * 70}
CRITICAL ERROR - SYSTEM CRASH
{"=" * 70}
Timestamp: {datetime.now().isoformat()}
Logger: {record.name}
Level: {record.levelname}
Message: {record.getMessage()}
{"=" * 70}
"""

        # Write to crash log
        try:
            with open(CRASH_LOG, "a") as f:
                f.write(crash_info + "\n")
        except:
            pass

        # Print to stderr
        print(crash_info, file=sys.stderr)

        # Exit with error code
        sys.exit(1)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a centralized logger for an agent or daemon.

    Args:
        name: Name of the agent/daemon (used for log file)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"elf.{name}")

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - all logs go to central directory
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Crash policy handler
    crash_handler = CrashPolicyHandler()
    crash_handler.setLevel(logging.CRITICAL)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(crash_handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


def log_critical(agent_name: str, message: str, crash: bool = True, exit_code: int = 1):
    """
    Log a critical error. By default, this will crash the system.

    Args:
        agent_name: Name of the agent logging the error
        message: Error message
        crash: If True, exit the system (default: True)
        exit_code: Exit code to use if crashing
    """
    global _has_crashed

    logger = get_logger(agent_name)
    logger.critical(message)

    if crash and not _has_crashed:
        _has_crashed = True

        crash_info = f"""
{"=" * 70}
CRITICAL ERROR - SYSTEM CRASH
{"=" * 70}
Timestamp: {datetime.now().isoformat()}
Agent: {agent_name}
Message: {message}
{"=" * 70}
"""

        # Write to crash log
        try:
            with open(CRASH_LOG, "a") as f:
                f.write(crash_info + "\n")
        except:
            pass

        # Print to stderr
        print(crash_info, file=sys.stderr)

        # Exit
        sys.exit(exit_code)


def log_error(agent_name: str, message: str, escalate: bool = False):
    """
    Log an error. Optionally escalate to the orchestrator.

    Args:
        agent_name: Name of the agent logging the error
        message: Error message
        escalate: If True, notify the orchestrator (default: False)
    """
    logger = get_logger(agent_name)
    logger.error(message)

    if escalate:
        # Write to escalation log
        escalation_file = LOGS_DIR / "escalation.log"
        timestamp = datetime.now().isoformat()
        with open(escalation_file, "a") as f:
            f.write(f"{timestamp} - {agent_name} - {message}\n")


def log_warning(agent_name: str, message: str):
    """Log a warning message."""
    logger = get_logger(agent_name)
    logger.warning(message)


def log_info(agent_name: str, message: str):
    """Log an info message."""
    logger = get_logger(agent_name)
    logger.info(message)


def log_debug(agent_name: str, message: str):
    """Log a debug message."""
    logger = get_logger(agent_name)
    logger.debug(message)


# Convenience function for agents to verify logging is working
def verify_logging() -> bool:
    """
    Verify that the logging system is properly configured.
    Returns True if logging is working, raises exception otherwise.
    """
    test_logger = get_logger("logging_verification")

    try:
        test_logger.info("Logging verification test")

        # Check if log file was created
        log_file = LOGS_DIR / "logging_verification.log"
        if not log_file.exists():
            raise RuntimeError(f"Log file not created: {log_file}")

        # Check if we can read it
        content = log_file.read_text()
        if "Logging verification test" not in content:
            raise RuntimeError("Log message not written to file")

        return True
    except Exception as e:
        print(f"LOGGING VERIFICATION FAILED: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    # Test the logging system
    print("Testing ELF Centralized Logging System...")

    # Verify logging works
    verify_logging()
    print("✅ Logging verification passed")

    # Test different log levels
    log_info("test", "Info message")
    log_warning("test", "Warning message")
    log_error("test", "Error message (no escalate)")

    print(f"✅ All logs written to: {LOGS_DIR}")
    print("✅ Logging system ready")
