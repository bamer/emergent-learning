"""
Event Chronicle Adapter for Dashboard

Converts Event Chronicle format to dashboard-compatible timeline events.
"""

import json
import sys
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from timeline_events import get_event_config, format_event_description
except ImportError:
    try:
        from .timeline_events import get_event_config, format_event_description
    except ImportError:

        def get_event_config(event_type: str):
            from dataclasses import dataclass

            @dataclass
            class TimelineEventConfig:
                icon: str = "FileText"
                color: str = "bg-slate-500"
                label: str = event_type.replace("_", " ").title()
                description_template: str = "{event_data}"

            return TimelineEventConfig()

        def format_event_description(event_type: str, data: Dict[str, Any]) -> str:
            return str(data)


# Event type mapping: operational types → timeline-friendly types
EVENT_TYPE_MAPPING: Dict[str, str] = {
    "agent_started": "task_start",
    "agent_stopped": "task_end",
    "heuristic_created": "heuristic_consulted",
    "heuristic_validated": "heuristic_validated",
    "heuristic_violated": "heuristic_violated",
    "tool_poll": "task_start",
    "message.updated": "task_start",
    "message.part.updated": "task_start",
    "message.created": "task_start",
    "session.updated": "task_start",
    "session.status": "task_end",
    "session.idle": "task_end",
    "session.ended": "task_end",
    "session.started": "task_start",
    "server.heartbeat": "task_start",
    "sentinel_check": "task_start",
    "sentinel_cycle": "task_start",
    "checkin": "task_start",
    "checkout": "task_end",
    "swarm_execution": "task_start",
    "workflow_started": "task_start",
    "workflow_completed": "task_end",
    "error_logged": "failure_recorded",
    "golden_promoted": "golden_promoted",
    "unknown": "task_start",
}


def convert_chronicle_event_to_timeline_event(
    chronicle_event: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert an Event Chronicle event to a dashboard timeline event.

    Args:
        chronicle_event: Event from Event Chronicle in its native format

    Returns:
        Timeline event compatible with dashboard TimelineView component
    """
    # Extract basic fields
    event_id = chronicle_event.get("event_id", "")
    timestamp = chronicle_event.get("timestamp", "")
    original_event_type = chronicle_event.get("event_type", "unknown")
    source = chronicle_event.get("source", "")
    data = chronicle_event.get("data", {})
    metadata = chronicle_event.get("metadata", {})
    summary = chronicle_event.get("summary", "")

    # Map operational event type to timeline-friendly type
    event_type = EVENT_TYPE_MAPPING.get(original_event_type, "task_start")

    # Use summary field if available, otherwise format description
    if summary:
        description = summary
    else:
        description = format_event_description(event_type, data)

    # Extract file path and line number if available
    file_path = data.get("file_path") or metadata.get("file_path")
    line_number = data.get("line_number") or metadata.get("line_number")

    # Extract domain if available
    domain = data.get("domain") or metadata.get("domain")

    # Create timeline event
    timeline_event = {
        "id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "original_event_type": original_event_type,  # Preserve for reference
        "description": description,
        "metadata": metadata,
        "source": source,
    }

    # Add optional fields if present
    if file_path:
        timeline_event["file_path"] = file_path
    if line_number:
        timeline_event["line_number"] = line_number
    if domain:
        timeline_event["domain"] = domain

    return timeline_event


def get_chronicle_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    chronicle_dir: Optional[Path] = None,
    days_back: int = 7,
) -> List[Dict[str, Any]]:
    """
    Retrieve events from Event Chronicle database, converted to timeline format.

    Args:
        event_type: Filter by event type
        source: Filter by source component
        limit: Maximum number of events to return
        chronicle_dir: Deprecated parameter (kept for compatibility)
        days_back: Number of days to look back (default 7)

    Returns:
        List of timeline events
    """
    # Get ELF base directory
    elf_base = Path(__file__).parent.parent.parent
    db_path = elf_base / "memory" / "index.db"

    events = []

    # Query the database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT id, timestamp, event_type, source, source_id, status, summary, data
            FROM event_chronicle
            WHERE 1=1
        """
        params = []

        # Add time filter
        if days_back > 0:
            query += " AND timestamp > datetime('now', '-{} days')".format(days_back)

        # Add source filter
        if source:
            query += " AND source = ?"
            params.append(source)

        # Add event type filter
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        # Order and limit
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        for row in rows:
            # Parse JSON data
            data = {}
            if row["data"]:
                try:
                    data = json.loads(row["data"])
                except:
                    data = {}

            # Create chronicle event format
            chronicle_event = {
                "event_id": str(row["id"]),
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "source": row["source"],
                "source_id": row["source_id"],
                "status": row["status"],
                "summary": row["summary"],
                "data": data,
                "metadata": {},  # Column doesn't exist in database
            }

            # Convert to timeline format
            timeline_event = convert_chronicle_event_to_timeline_event(chronicle_event)
            events.append(timeline_event)

        conn.close()

    except Exception as e:
        print(f"Error querying database: {e}")

    return events


def get_chronicle_stats(
    chronicle_dir: Optional[Path] = None, days_back: int = 7
) -> Dict[str, Any]:
    """
    Get Event Chronicle statistics from database.

    Args:
        chronicle_dir: Deprecated parameter (kept for compatibility)
        days_back: Number of days to look back (default 7)

    Returns:
        Statistics about the chronicle
    """
    # Get ELF base directory
    elf_base = Path(__file__).parent.parent.parent
    db_path = elf_base / "memory" / "index.db"

    stats = {
        "total_events": 0,
        "event_types": {},
        "sources": {},
        "date_range": {"earliest": None, "latest": None},
    }

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT id, timestamp, event_type, source
            FROM event_chronicle
            WHERE 1=1
        """
        params = []

        # Add time filter
        if days_back > 0:
            query += " AND timestamp > datetime('now', '-{} days')".format(days_back)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        for row in rows:
            stats["total_events"] += 1

            # Count event types
            event_type = row["event_type"] or "unknown"
            stats["event_types"][event_type] = (
                stats["event_types"].get(event_type, 0) + 1
            )

            # Count sources
            source = row["source"] or "unknown"
            stats["sources"][source] = stats["sources"].get(source, 0) + 1

            # Track date range
            event_time = row["timestamp"]
            if event_time:
                if (
                    not stats["date_range"]["earliest"]
                    or event_time < stats["date_range"]["earliest"]
                ):
                    stats["date_range"]["earliest"] = event_time
                if (
                    not stats["date_range"]["latest"]
                    or event_time > stats["date_range"]["latest"]
                ):
                    stats["date_range"]["latest"] = event_time

        conn.close()

    except Exception as e:
        print(f"Error querying database stats: {e}")

    return stats
