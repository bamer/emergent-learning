#!/usr/bin/env python3
"""
ELF Database Event Logger
Utility for logging events to the event_chronicle table in the database.
Used by Watcher, Unified Orchestrator, and other ELF components.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Setup paths and database connection
ELF_BASE = Path.home() / ".opencode" / "emergent-learning"
DB_PATH = ELF_BASE / "memory" / "index.db"

logger = logging.getLogger(__name__)

# Common event types
EVENT_TYPES = {
    # Watcher events
    "file_change": "Watcher detected a file change",
    "file_creation": "Watcher detected a new file",
    "file_deletion": "Watcher detected a deleted file",
    "watcher_status": "Watcher status update",
    "watcher_check": "Watcher performed check",
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
        source: Component that generated the event (e.g., 'watcher', 'orchestrator')
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
            logger.warning(f"Database not found at {DB_PATH}")
            return None

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Serialize data to JSON if provided
        data_json = json.dumps(data) if data else None

        # Use current timestamp if not provided in data
        from datetime import timezone

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
        logger.error(f"Error logging event to database: {e}")
        return None


def log_watcher_check(
    tier: int, status: str, summary: str, details: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Log a watcher check event.

    Args:
        tier: Watcher tier (1 or 2)
        status: Check status (success, error, warning)
        summary: Human-readable summary
        details: Optional details about the check

    Returns:
        ID of the inserted event, or None on failure
    """
    from datetime import timezone

    data = {
        "tier": tier,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }

    return log_event(
        event_type="watcher_check",
        source="watcher",
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
    Log a file watcher event.

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

    from datetime import timezone

    data = {
        "file_path": file_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }

    return log_event(
        event_type=event_type,
        source="watcher",
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
) -> list[Dict[str, Any]]:
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
        logger.error(f"Error fetching events from database: {e}")
        return []


if __name__ == "__main__":
    # Test the event logger
    print("Testing ELF Event Logger...")

    # Test basic event logging
    event_id = log_event(
        event_type="test_event",
        source="test_logger",
        summary="Testing event logger",
        data={"test": True},
        status="success",
    )

    if event_id:
        print(f"✓ Test event logged with ID: {event_id}")
    else:
        print("✗ Failed to log test event")

    # Test watcher event logging
    watcher_event_id = log_watcher_check(
        tier=1,
        status="success",
        summary="Test watcher check",
        details={"test": "watcher"},
    )

    if watcher_event_id:
        print(f"✓ Watcher event logged with ID: {watcher_event_id}")
    else:
        print("✗ Failed to log watcher event")

    # Test orchestrator event logging
    orch_event_id = log_orchestrator_event(
        event_type="question_received",
        event_category="question",
        summary="Test orchestrator question",
        details={"question": "test"},
    )

    if orch_event_id:
        print(f"✓ Orchestrator event logged with ID: {orch_event_id}")
    else:
        print("✗ Failed to log orchestrator event")

    # Test fetching events
    recent_events = get_recent_events(limit=5)
    print(f"\n✓ Found {len(recent_events)} recent events in database")
