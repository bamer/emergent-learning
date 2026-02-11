"""
ELF Unified Logging System
==========================

All agents and daemons MUST use this logging system.

Features:
- Centralized file logging to /home/bamer/.opencode/emergent-learning/logs/
- Database event logging to event_chronicle table
- Crash policy: Critical errors will crash the system
- Agent-specific loggers with consistent formatting

Usage:
    # File-based logging
    from elf_logging import get_logger, log_info, log_warning

    logger = get_logger("my_agent")
    logger.info("Message")

    # Database event logging
    from elf_logging import log_event, log_sentinel_check

    log_event(event_type="tool_execution", source="my_agent", summary="Task completed")

"""

import logging
import logging.handlers
import sys
import os
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# Central log directory - ALL logs go here
LOGS_DIR = Path("/home/bamer/.opencode/emergent-learning/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database path
ELF_BASE = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_BASE / "memory" / "index.db"

# Crash log file for critical errors
CRASH_LOG = LOGS_DIR / "CRASH.log"

# Log rotation settings
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_LOG_AGE_DAYS = 7
MAX_BACKUP_COUNT = 5  # Keep 5 backup files per logger

# Track if we've already crashed (to avoid infinite crash loops)
_has_crashed = False


def cleanup_old_logs():
    """
    Clean up log files older than MAX_LOG_AGE_DAYS.
    Called automatically when creating a logger.
    """
    try:
        cutoff_time = time.time() - (MAX_LOG_AGE_DAYS * 24 * 60 * 60)
        deleted_count = 0
        
        if LOGS_DIR.exists():
            for log_file in LOGS_DIR.glob("*.log*"):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        log_file.unlink()
                        deleted_count += 1
                except Exception:
                    pass  # Ignore permission errors, etc.
        
        if deleted_count > 0:
            print(f"[LOG_CLEANUP] Removed {deleted_count} log files older than {MAX_LOG_AGE_DAYS} days")
    except Exception as e:
        print(f"[LOG_CLEANUP_ERROR] {e}", file=sys.stderr)


# =============================================================================
# FILE-BASED LOGGING (Agent Logging)
# =============================================================================


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

    # Clean up old logs periodically (only for the first logger created)
    if not hasattr(cleanup_old_logs, '_last_cleanup'):
        cleanup_old_logs._last_cleanup = 0
    
    current_time = time.time()
    if current_time - cleanup_old_logs._last_cleanup > 3600:  # Cleanup once per hour
        cleanup_old_logs()
        cleanup_old_logs._last_cleanup = current_time
    
    # Rotating file handler - rotates when log exceeds 10MB, keeps 5 backups
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=MAX_BACKUP_COUNT
    )
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


# =============================================================================
# DATABASE EVENT LOGGING (Event Chronicle)
# =============================================================================

# Common event types
EVENT_TYPES = {
    # Sentinel events
    "file_change": "Sentinel detected a file change",
    "file_creation": "Sentinel detected a new file",
    "file_deletion": "Sentinel detected a deleted file",
    "sentinel_status": "Sentinel status update",
    "sentinel_check": "Sentinel performed check",
    # Orchestrator events
    "agent_question": "Agent received a question",
    "agent_response": "Agent generated a response",
    "orchestrator_action": "Orchestrator performed an action",
    "question_received": "Orchestrator received a question",
    "response_sent": "Orchestrator sent a response",
    "orchestrator_decided": "Orchestrator made a decision",
    # System events
    "system_check": "System health check",
    "service_status": "Service status update",
}


def log_event(
    event_type: str,
    source: str,
    summary: str,
    data: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None,
    status: str = "success",
) -> Optional[int]:
    """
    Log an event to the event_chronicle database table.

    Args:
        event_type: Type of event (use EVENT_TYPES values for consistency)
        source: Component that generated the event (e.g., 'sentinel', 'orchestrator')
        summary: Human-readable summary of the event
        data: Optional JSON-serializable data payload
        source_id: Optional identifier for the event source
        status: Event status (success, error, warning)

    Returns:
        ID of the inserted event record, or None on failure
    """
    try:
        # Ensure database exists
        if not DB_PATH.exists():
            log_warning("event_logger", f"Database not found at {DB_PATH}")
            return None

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Serialize data to JSON if provided
        data_json = json.dumps(data) if data else None

        # Use current timestamp if not provided in data
        timestamp = datetime.now(timezone.utc).isoformat()
        if data and "timestamp" in data:
            timestamp = data["timestamp"]

        cursor.execute(
            """
            INSERT INTO event_chronicle 
            (event_type, source, source_id, summary, status, data, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
            (event_type, source, source_id, summary, status, data_json, timestamp),
        )

        event_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return event_id

    except Exception as e:
        # Use fallback logging if database logging fails
        print(f"[EVENT_LOG_ERROR] {e}", file=sys.stderr)
        return None


def log_sentinel_check(
    tier: int, status: str, summary: str, details: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Log a sentinel check event.

    Args:
        tier: Sentinel tier (1 or 2)
        status: Check status (success, error, warning)
        summary: Human-readable summary
        details: Optional details about the check

    Returns:
        ID of the inserted event, or None on failure
    """
    data = {
        "tier": tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }

    return log_event(
        event_type="sentinel_check",
        source="sentinel",
        summary=f"Tier {tier} check: {summary}",
        data=data,
        status=status,
    )


def log_file_event(
    action: str,  # 'change', 'creation', 'deletion'
    file_path: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Log a file sentinel event.

    Args:
        action: Type of file action
        file_path: Path to the file
        details: Optional details about the file

    Returns:
        ID of the inserted event, or None on failure
    """
    event_type_map = {
        "change": "file_change",
        "creation": "file_creation",
        "deletion": "file_deletion",
    }

    event_type = event_type_map.get(action, "file_change")

    data = {
        "file_path": file_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }

    return log_event(
        event_type=event_type,
        source="sentinel",
        summary=f"File {action}: {file_path}",
        data=data,
        status="success",
    )


def log_orchestrator_event(
    event_type: str,  # 'question_received', 'response_sent', 'orchestrator_action', 'orchestrator_decided'
    event_category: str,  # 'question', 'response', 'action', 'decision'
    summary: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Log an orchestrator event.

    Args:
        event_type: Specific event type
        event_category: General category (question, response, action, decision)
        summary: Human-readable summary
        details: Optional event details

    Returns:
        ID of the inserted event, or None on failure
    """
    data = {
        "category": event_category,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": details or {},
    }

    return log_event(
        event_type=event_type,
        source="orchestrator",
        summary=f"[{event_category.upper()}] {summary}",
        data=data,
        status="success",
    )


def get_recent_events(
    event_type_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get recent events from the database.

    Args:
        event_type_filter: Optional filter by event type
        source_filter: Optional filter by source
        limit: Maximum number of events to return

    Returns:
        List of event dictionaries
    """
    try:
        if not DB_PATH.exists():
            return []

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with optional filters
        where_clauses = []
        params = []

        if event_type_filter:
            where_clauses.append("event_type = ?")
            params.append(event_type_filter)

        if source_filter:
            where_clauses.append("source = ?")
            params.append(source_filter)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
            SELECT id, timestamp, event_type, source, summary, status, data
            FROM event_chronicle
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
        """

        cursor.execute(query, params + [limit])

        events = []
        for row in cursor.fetchall():
            event_data = dict(row)
            # Parse JSON data if present
            if event_data.get("data"):
                try:
                    event_data["data"] = json.loads(event_data["data"])
                except json.JSONDecodeError:
                    pass
            events.append(event_data)

        conn.close()
        return events

    except Exception as e:
        # Use fallback logging if database logging fails
        print(f"[EVENT_QUERY_ERROR] {e}", file=sys.stderr)
        return []


# =============================================================================
# MAIN / TEST
# =============================================================================

if __name__ == "__main__":
    # Test the logging system
    print("Testing ELF Unified Logging System...")

    # Verify logging works
    verify_logging()
    print("✅ Logging verification passed")

    # Test different log levels
    log_info("test", "Info message")
    log_warning("test", "Warning message")
    log_error("test", "Error message (no escalate)")

    print(f"✅ All logs written to: {LOGS_DIR}")

    # Test event logging
    print("\nTesting Database Event Logging...")

    event_id = log_event(
        event_type="test_event",
        source="test_logger",
        summary="Testing unified logging",
        data={"test": True},
        status="success",
    )
    print(f"✅ Event logged with ID: {event_id}")

    # Test sentinel event logging
    sentinel_event_id = log_sentinel_check(
        tier=1,
        status="success",
        summary="Test sentinel check",
        details={"test": "sentinel"},
    )
    print(f"✅ Sentinel event logged with ID: {sentinel_event_id}")

    # Test orchestrator event logging
    orch_event_id = log_orchestrator_event(
        event_type="question_received",
        event_category="question",
        summary="Test orchestrator question",
        details={"question": "test"},
    )
    print(f"✅ Orchestrator event logged with ID: {orch_event_id}")

    # Test fetching events
    recent_events = get_recent_events(limit=5)
    print(f"✅ Found {len(recent_events)} recent events in database")

    print("\n✅ Unified logging system ready!")
