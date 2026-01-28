#!/usr/bin/env python3
"""
ELF Event Chronicle System

Standard ELF immutable event logging system.
Provides audit trail for all ELF system events.

Event Format:
{
    "event_id": "uuid",
    "timestamp": "iso8601",
    "event_type": "heuristic_created|failure_recorded|agent_spawned|workflow_started",
    "source": "component_name",
    "data": {...},
    "metadata": {
        "user_id": "optional",
        "session_id": "optional",
        "correlation_id": "uuid"
    }
}

Usage:
    from event_chronicle import EventChronicle
    chronicle = EventChronicle()
    chronicle.log_event("heuristic_created", "record-heuristic", {...})
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import os


class EventChronicle:
    """ELF Standard Event Chronicle Implementation"""

    def __init__(self, chronicle_dir: Optional[Path] = None):
        """Initialize event chronicle with standard ELF directory structure"""
        if chronicle_dir is None:
            # Standard ELF event chronicle location
            elf_base = Path(__file__).parent.parent
            chronicle_dir = elf_base / "event_chronicle"

        self.chronicle_dir = Path(chronicle_dir)
        self.chronicle_dir.mkdir(parents=True, exist_ok=True)

        # Current day's event file
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.current_file = self.chronicle_dir / f"{today}.jsonl"

        # Thread safety
        self._lock = threading.Lock()

        # Ensure chronicle directory structure
        self._ensure_structure()

    def _ensure_structure(self):
        """Ensure ELF standard chronicle directory structure"""
        # Create yearly and monthly subdirectories for organization
        now = datetime.now(timezone.utc)
        year_dir = self.chronicle_dir / str(now.year)
        month_dir = year_dir / f"{now.month:02d}"

        year_dir.mkdir(exist_ok=True)
        month_dir.mkdir(exist_ok=True)

        # Also create current day file in month directory
        self.current_file = month_dir / f"{now.strftime('%Y-%m-%d')}.jsonl"

    def log_event(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an event to the chronicle

        Args:
            event_type: Type of event (heuristic_created, failure_recorded, etc.)
            source: Component that generated the event
            data: Event data payload
            metadata: Optional metadata (user_id, session_id, correlation_id)

        Returns:
            event_id: UUID of the logged event
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "source": source,
            "data": data,
            "metadata": metadata or {},
        }

        # Thread-safe file append
        with self._lock:
            with open(self.current_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

        return event_id

    def query_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        Query events from the chronicle

        Args:
            event_type: Filter by event type
            source: Filter by source component
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching events
        """
        events = []

        # Get relevant chronicle files
        chronicle_files = list(self.chronicle_dir.rglob("*.jsonl"))
        chronicle_files.sort(reverse=True)  # Most recent first

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

                            # Time filtering
                            event_time = datetime.fromisoformat(
                                event["timestamp"].replace("Z", "+00:00")
                            )
                            if start_time and event_time < start_time:
                                continue
                            if end_time and event_time > end_time:
                                continue

                            events.append(event)

                        except json.JSONDecodeError:
                            continue

            except FileNotFoundError:
                continue

        return events[:limit]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific event by ID"""
        chronicle_files = list(self.chronicle_dir.rglob("*.jsonl"))

        for chronicle_file in chronicle_files:
            try:
                with open(chronicle_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            if event.get("event_id") == event_id:
                                return event
                        except json.JSONDecodeError:
                            continue
            except FileNotFoundError:
                continue

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get chronicle statistics"""
        stats = {
            "total_events": 0,
            "event_types": {},
            "sources": {},
            "date_range": {"earliest": None, "latest": None},
        }

        chronicle_files = list(self.chronicle_dir.rglob("*.jsonl"))

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


# Global instance for ELF system
_chronicle_instance = None


def get_chronicle() -> EventChronicle:
    """Get the global ELF event chronicle instance"""
    global _chronicle_instance
    if _chronicle_instance is None:
        _chronicle_instance = EventChronicle()
    return _chronicle_instance


def log_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function to log an event to the global chronicle"""
    return get_chronicle().log_event(event_type, source, data, metadata)


if __name__ == "__main__":
    # Demo: Create test events
    chronicle = EventChronicle()

    # Log a test event
    event_id = chronicle.log_event(
        event_type="heuristic_created",
        source="record-heuristic.sh",
        data={
            "heuristic_id": 123,
            "domain": "test",
            "rule": "Test heuristic for event chronicle",
        },
        metadata={"user_id": "test-user", "session_id": "test-session"},
    )

    print(f"Logged event: {event_id}")

    # Query events
    events = chronicle.query_events(limit=5)
    print(f"Found {len(events)} events")

    # Get stats
    stats = chronicle.get_stats()
    print(f"Chronicle stats: {json.dumps(stats, indent=2)}")
