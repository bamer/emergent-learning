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
    event_type = chronicle_event.get("event_type", "unknown")
    source = chronicle_event.get("source", "")
    data = chronicle_event.get("data", {})
    metadata = chronicle_event.get("metadata", {})

    # Format description
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
) -> List[Dict[str, Any]]:
    """
    Retrieve events from Event Chronicle, converted to timeline format.

    Args:
        event_type: Filter by event type
        source: Filter by source component
        limit: Maximum number of events to return
        chronicle_dir: Path to chronicle directory (defaults to standard location)

    Returns:
        List of timeline events
    """
    if chronicle_dir is None:
        # Standard ELF event chronicle location
        elf_base = Path(__file__).parent.parent.parent
        chronicle_dir = elf_base / "event_chronicle"

    events = []

    # Get chronicle files (most recent first)
    if chronicle_dir.exists():
        chronicle_files = sorted(chronicle_dir.rglob("*.jsonl"), reverse=True)

        for chronicle_file in chronicle_files:
            if len(events) >= limit:
                break

            try:
                with open(chronicle_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(events) >= limit:
                            break

                        try:
                            event = json.loads(line.strip())

                            # Apply filters
                            if event_type and event.get("event_type") != event_type:
                                continue
                            if source and event.get("source") != source:
                                continue

                            # Convert to timeline format
                            timeline_event = convert_chronicle_event_to_timeline_event(
                                event
                            )
                            events.append(timeline_event)

                        except json.JSONDecodeError:
                            continue

            except FileNotFoundError:
                continue

    return events


def get_chronicle_stats(chronicle_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get Event Chronicle statistics.

    Args:
        chronicle_dir: Path to chronicle directory (defaults to standard location)

    Returns:
        Statistics about the chronicle
    """
    if chronicle_dir is None:
        # Standard ELF event chronicle location
        elf_base = Path(__file__).parent.parent.parent
        chronicle_dir = elf_base / "event_chronicle"

    stats = {
        "total_events": 0,
        "event_types": {},
        "sources": {},
        "date_range": {"earliest": None, "latest": None},
    }

    if chronicle_dir.exists():
        chronicle_files = list(chronicle_dir.rglob("*.jsonl"))

        for chronicle_file in chronicle_files:
            try:
                with open(chronicle_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            stats["total_events"] += 1

                            # Count event types
                            event_type = event.get("event_type", "unknown")
                            stats["event_types"][event_type] = (
                                stats["event_types"].get(event_type, 0) + 1
                            )

                            # Count sources
                            source = event.get("source", "unknown")
                            stats["sources"][source] = (
                                stats["sources"].get(source, 0) + 1
                            )

                            # Track date range
                            event_time = event.get("timestamp")
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

                        except json.JSONDecodeError:
                            continue

            except FileNotFoundError:
                continue

    return stats
