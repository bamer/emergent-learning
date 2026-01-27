"""
Chronicle Router - Event chronicle endpoints for tracking all system events.

Provides endpoints to record and retrieve system events like:
- Dashboard Sentinel monitoring cycles
- Learning loop completions
- Heuristic discoveries
- Task outcomes
- System health alerts
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from utils.database import get_db, dict_from_row

router = APIRouter(prefix="/api/chronicle", tags=["chronicle"])
logger = logging.getLogger(__name__)


class EventCreateRequest(BaseModel):
    """Request to create a new chronicle event."""
    event_type: str  # 'sentinel_cycle', 'learning_loop', 'heuristic_discovery', etc.
    source: str  # 'dashboard_sentinel', 'learning_hook', etc.
    source_id: Optional[str] = None
    status: str  # 'healthy', 'warning', 'critical', 'success', 'failure'
    summary: str
    data: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Response with event data."""
    id: int
    timestamp: str
    event_type: str
    source: str
    source_id: Optional[str]
    status: str
    summary: str
    data: Optional[Dict[str, Any]]
    created_at: str


@router.post("/events", response_model=EventResponse)
async def create_event(event: EventCreateRequest):
    """
    Record a new event to the chronicle.
    
    Used by Dashboard Sentinel, learning hooks, and other agents to log system events.
    
    Example:
    ```json
    {
        "event_type": "sentinel_cycle",
        "source": "dashboard_sentinel",
        "source_id": "sentinel-main",
        "status": "healthy",
        "summary": "System health check completed",
        "data": {"metrics": {...}}
    }
    ```
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        data_json = json.dumps(event.data) if event.data else None
        
        cursor.execute("""
            INSERT INTO event_chronicle (
                timestamp, event_type, source, source_id, status, summary, data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            event.event_type,
            event.source,
            event.source_id,
            event.status,
            event.summary,
            data_json,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"Event recorded: {event_id} - {event.event_type} ({event.source})")
        
        return EventResponse(
            id=event_id,
            timestamp=timestamp,
            event_type=event.event_type,
            source=event.source,
            source_id=event.source_id,
            status=event.status,
            summary=event.summary,
            data=event.data,
            created_at=timestamp
        )
    
    except Exception as e:
        logger.error(f"Failed to record event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    event_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hours: int = Query(24, description="How many hours back to query"),
    limit: int = Query(100, description="Max number of events to return")
):
    """
    Retrieve events from the chronicle.
    
    Query parameters:
    - `event_type`: Filter by event type (e.g., 'sentinel_cycle')
    - `source`: Filter by source (e.g., 'dashboard_sentinel')
    - `status`: Filter by status (e.g., 'healthy', 'critical')
    - `hours`: How many hours back to query (default: 24)
    - `limit`: Max results (default: 100)
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM event_chronicle WHERE created_at > datetime('now', ?)"
        params = [f"-{hours} hours"]
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event_dict = dict_from_row(row)
            # Parse JSON data if present
            if event_dict.get('data'):
                try:
                    event_dict['data'] = json.loads(event_dict['data'])
                except:
                    pass
            events.append(EventResponse(**event_dict))
        
        return events
    
    except Exception as e:
        logger.error(f"Failed to retrieve events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/stats")
async def get_event_stats(hours: int = Query(24)):
    """
    Get statistics about events in the chronicle.
    
    Returns counts by event_type and status.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Count by event_type
        cursor.execute("""
            SELECT event_type, COUNT(*) as count, status
            FROM event_chronicle
            WHERE created_at > datetime('now', ?)
            GROUP BY event_type, status
            ORDER BY event_type, status
        """, (f"-{hours} hours",))
        
        stats = {}
        for row in cursor.fetchall():
            event_type = row[0]
            count = row[1]
            status = row[2]
            
            if event_type not in stats:
                stats[event_type] = {}
            stats[event_type][status] = count
        
        conn.close()
        
        return {
            "query_hours": hours,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get event stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/latest")
async def get_latest_event(event_type: Optional[str] = None):
    """
    Get the latest event, optionally filtered by type.
    
    Useful for checking the most recent sentinel cycle or learning loop completion.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute("""
                SELECT * FROM event_chronicle
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (event_type,))
        else:
            cursor.execute("""
                SELECT * FROM event_chronicle
                ORDER BY created_at DESC
                LIMIT 1
            """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="No events found")
        
        event_dict = dict_from_row(row)
        # Parse JSON data if present
        if event_dict.get('data'):
            try:
                event_dict['data'] = json.loads(event_dict['data'])
            except:
                pass
        
        return EventResponse(**event_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
