"""
Timeline API for Dashboard Integration

Provides FastAPI endpoints for timeline data using Event Chronicle.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from .event_adapter import get_chronicle_events, get_chronicle_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["timeline"])

# Standard ELF event chronicle location
ELF_BASE_PATH = Path(__file__).parent.parent.parent
EVENT_CHRONICLE_DIR = ELF_BASE_PATH / "event_chronicle"


@router.get("/timeline/events")
async def get_timeline_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=50, le=1000),
):
    """
    Get individual events for timeline display.

    This endpoint provides events in the format expected by the dashboard's TimelineView component.

    Args:
        event_type: Filter by event type (e.g., 'heuristic_validated', 'task_start')
        source: Filter by source component (e.g., 'record-heuristic.sh', 'orchestrator')
        limit: Maximum number of events to return (max 1000)

    Returns:
        Dictionary with status, events list, and count
    """
    try:
        events = get_chronicle_events(
            event_type=event_type,
            source=source,
            limit=limit,
            chronicle_dir=EVENT_CHRONICLE_DIR,
        )

        return {"status": "ok", "events": events, "count": len(events)}

    except Exception as e:
        logger.error(f"Error fetching timeline events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/stats")
async def get_timeline_stats():
    """
    Get timeline statistics.

    Returns statistics about events in the chronicle.

    Returns:
        Dictionary with total events, event types, sources, and date range
    """
    try:
        stats = get_chronicle_stats(chronicle_dir=EVENT_CHRONICLE_DIR)
        return stats

    except Exception as e:
        logger.error(f"Error fetching timeline stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/recent")
async def get_recent_events(limit: int = Query(default=10, le=100)):
    """
    Get most recent events for quick overview.

    Args:
        limit: Number of recent events to return (max 100)

    Returns:
        List of recent timeline events
    """
    try:
        events = get_chronicle_events(limit=limit, chronicle_dir=EVENT_CHRONICLE_DIR)

        return events

    except Exception as e:
        logger.error(f"Error fetching recent events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Event type constants for frontend use
EVENT_TYPES = [
    "task_start",
    "task_end",
    "heuristic_consulted",
    "heuristic_validated",
    "heuristic_violated",
    "failure_recorded",
    "golden_promoted",
    "agent_spawned",
    "workflow_started",
    "session_started",
    "session_ended",
]


@router.get("/timeline/event-types")
async def get_event_types():
    """
    Get available event types.

    Returns list of event types that can be used for filtering.

    Returns:
        List of event type strings
    """
    return EVENT_TYPES
