"""
Monitoring Router - Dashboard API

Provides endpoints for:
- Sentinel monitoring status and cycles
- Event chronicle querying
- System health metrics
- Watcher status and control
"""

import json
import sqlite3
import subprocess
import os
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["monitoring"])

# Database path
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
EVENT_CHRONICLE_DIR = (
    Path.home() / ".opencode" / "emergent-learning" / "event_chronicle"
)


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with proper settings."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ==============================================================================
# Sentinel Endpoints
# ==============================================================================


@router.get("/sentinel/status")
async def get_sentinel_status():
    """Get current sentinel monitoring status and recent cycles."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent sentinel cycles from event_chronicle
        cursor.execute(
            """
            SELECT timestamp, data, summary, status
            FROM event_chronicle
            WHERE event_type = 'sentinel_cycle'
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )

        cycles = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row["data"]) if row["data"] else {}
                cycles.append(
                    {
                        "timestamp": row["timestamp"],
                        "metrics": data.get("metrics", {}),
                        "analysis": data.get("analysis", {}),
                        "actions_taken": data.get("actions", []),
                        "agent_executions": data.get("agent_executions", []),
                    }
                )
            except json.JSONDecodeError:
                continue

        conn.close()

        # Get current cycle (most recent)
        current_cycle = cycles[0] if cycles else None

        # Detect patterns from cycles
        patterns = detect_patterns_from_cycles(cycles[:20])

        return {
            "status": "ok",
            "current_cycle": current_cycle,
            "recent_cycles": cycles[:20],
            "patterns": patterns,
            "total_cycles": len(cycles),
        }

    except Exception as e:
        logger.error(f"Error fetching sentinel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def detect_patterns_from_cycles(cycles: List[Dict]) -> List[Dict]:
    """Detect patterns from sentinel cycle history."""
    patterns = []

    if len(cycles) < 3:
        return patterns

    # Check for declining activity
    activity_scores = [
        c.get("metrics", {}).get("activity", {}).get("activity_score", 0)
        for c in cycles[:5]
    ]
    if (
        len(activity_scores) >= 3
        and all(
            activity_scores[i] <= activity_scores[i - 1]
            for i in range(1, len(activity_scores))
        )
        and activity_scores[0] > 0
    ):
        patterns.append(
            {
                "pattern_name": "Declining Activity",
                "description": "System activity has been declining over recent cycles",
                "severity": "warning",
                "detected_at": cycles[0]["timestamp"],
            }
        )

    # Check for service instability
    service_issues = sum(
        1
        for c in cycles[:10]
        if not c.get("metrics", {}).get("services", {}).get("overall", True)
    )
    if service_issues >= 3:
        patterns.append(
            {
                "pattern_name": "Service Instability",
                "description": f"Service health issues detected in {service_issues} of last 10 cycles",
                "severity": "critical",
                "detected_at": cycles[0]["timestamp"],
            }
        )

    # Check for high error rate
    critical_cycles = sum(
        1 for c in cycles[:10] if c.get("analysis", {}).get("status") == "critical"
    )
    if critical_cycles >= 2:
        patterns.append(
            {
                "pattern_name": "Frequent Critical Status",
                "description": f"System reported critical status {critical_cycles} times recently",
                "severity": "warning",
                "detected_at": cycles[0]["timestamp"],
            }
        )

    return patterns


# ==============================================================================
# Event Chronicle Endpoints
# ==============================================================================


@router.get("/chronicle/events")
async def get_chronicle_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=50, le=1000),
):
    """Query events from the event chronicle."""
    try:
        events = []

        # Get chronicle files (most recent first)
        chronicle_files = sorted(EVENT_CHRONICLE_DIR.rglob("*.jsonl"), reverse=True)

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

                            events.append(event)

                        except json.JSONDecodeError:
                            continue

            except FileNotFoundError:
                continue

        return {"status": "ok", "events": events, "count": len(events)}

    except Exception as e:
        logger.error(f"Error fetching chronicle events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chronicle/stats")
async def get_chronicle_stats():
    """Get event chronicle statistics."""
    try:
        stats = {
            "total_events": 0,
            "event_types": {},
            "sources": {},
            "date_range": {"earliest": None, "latest": None},
        }

        chronicle_files = list(EVENT_CHRONICLE_DIR.rglob("*.jsonl"))

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

    except Exception as e:
        logger.error(f"Error fetching chronicle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# System Health Endpoints
# ==============================================================================


@router.get("/health/status")
async def get_system_health():
    """Get current system health status and history."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current health
        cursor.execute(
            """
            SELECT * FROM system_health
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )

        current_row = cursor.fetchone()
        current = None
        if current_row:
            current = dict(current_row)

        # Get recent history
        cursor.execute(
            """
            SELECT * FROM system_health
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )

        history = [dict(row) for row in cursor.fetchall()]

        # Calculate metrics
        metrics = calculate_health_metrics(history)

        conn.close()

        return {
            "status": "ok",
            "current": current,
            "history": history,
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        # Return default response if table doesn't exist
        return {"status": "ok", "current": None, "history": [], "metrics": None}


def calculate_health_metrics(history: List[Dict]) -> Dict:
    """Calculate health metrics from history."""
    if not history:
        return {
            "avg_response_time_ms": 0,
            "error_rate": 0,
            "uptime_percentage": 100,
            "total_requests": 0,
            "failed_requests": 0,
        }

    total = len(history)
    healthy_count = sum(1 for h in history if h.get("status") == "healthy")

    return {
        "avg_response_time_ms": 50,  # Placeholder
        "error_rate": (total - healthy_count) / total if total > 0 else 0,
        "uptime_percentage": (healthy_count / total * 100) if total > 0 else 100,
        "total_requests": total * 10,  # Estimated
        "failed_requests": (total - healthy_count) * 10,
    }


# ==============================================================================
# Watcher Endpoints
# ==============================================================================


class WatcherControlRequest(BaseModel):
    action: str  # 'start', 'stop', 'restart'


@router.get("/watcher/status")
async def get_watcher_status():
    """Get watcher status and recent logs."""
    try:
        # Check if watcher is running by looking for recent activity
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent watcher activity from event_chronicle
        cursor.execute(
            """
            SELECT timestamp, event_type, source, data, summary
            FROM event_chronicle
            WHERE source LIKE '%watcher%' OR event_type LIKE '%watcher%'
            ORDER BY timestamp DESC
            LIMIT 20
            """
        )

        logs = []
        for row in cursor.fetchall():
            logs.append(
                {
                    "timestamp": row["timestamp"],
                    "level": "info",
                    "message": row["summary"]
                    or f"{row['event_type']} from {row['source']}",
                    "tier": "tier1",
                }
            )

        # Check if watcher process is actually running
        result = subprocess.run(
            ["pgrep", "-f", "watcher/launcher.py"], capture_output=True, text=True
        )
        is_running = result.returncode == 0

        # Get sentinel cycles for additional context
        cursor.execute(
            """
            SELECT COUNT(*) as count,
                   MAX(timestamp) as last_check,
                   COUNT(CASE WHEN status = 'critical' THEN 1 END) as escalations
            FROM event_chronicle
            WHERE event_type = 'sentinel_cycle'
            AND timestamp > datetime('now', '-1 hour')
            """
        )

        row = cursor.fetchone()
        last_check = row["last_check"] if row else None
        escalations = row["escalations"] if row else 0

        conn.close()

        # Determine current tier based on recent activity
        tier = "idle"
        if is_running:
            tier = "tier1" if escalations == 0 else "tier2"

        status = {
            "is_running": is_running,
            "tier": tier,
            "last_check": last_check or datetime.now().isoformat(),
            "next_check": (datetime.now() + timedelta(seconds=30)).isoformat(),
            "check_interval_seconds": 30,
            "total_checks": row["count"] if row else 0,
            "escalations_count": escalations,
            "current_status": "healthy"
            if escalations == 0
            else "warning"
            if escalations < 3
            else "critical",
            "analysis_summary": f"Watcher {'active' if is_running else 'inactive'}. {escalations} escalations in last hour.",
        }

        config = {
            "tier1_interval_seconds": 30,
            "tier2_interval_seconds": 60,
            "escalation_threshold": 3,
            "auto_resolve": True,
            "enabled": True,
        }

        return {
            "status": "ok",
            "status_data": status,
            "recent_logs": logs,
            "config": config,
        }

    except Exception as e:
        logger.error(f"Error fetching watcher status: {e}")
        # Return default response
        return {
            "status": "ok",
            "status_data": {
                "is_running": False,
                "tier": "idle",
                "last_check": datetime.now().isoformat(),
                "next_check": (datetime.now() + timedelta(seconds=30)).isoformat(),
                "check_interval_seconds": 30,
                "total_checks": 0,
                "escalations_count": 0,
                "current_status": "healthy",
                "analysis_summary": "Watcher status unavailable",
            },
            "recent_logs": [],
            "config": {
                "tier1_interval_seconds": 30,
                "tier2_interval_seconds": 60,
                "escalation_threshold": 3,
                "auto_resolve": True,
                "enabled": False,
            },
        }


@router.post("/watcher/control")
async def control_watcher(request: WatcherControlRequest):
    """Control watcher (start/stop/restart)."""
    try:
        # Log the control action
        logger.info(f"Watcher control action: {request.action}")

        ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
        WATCHER_DIR = ELF_DIR / "watcher"
        START_SCRIPT = WATCHER_DIR / "start-watcher.sh"
        STOP_FILE = ELF_DIR / ".coordination" / "watcher-stop"
        PID_FILE = Path("/tmp") / "elf-watcher.pid"

        if request.action == "start":
            # Remove stop file if it exists
            if STOP_FILE.exists():
                STOP_FILE.unlink()
                logger.info("Removed watcher stop file")

            # Check if already running
            result = subprocess.run(
                ["pgrep", "-f", "watcher/launcher.py"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Watcher is already running",
                    "pid": result.stdout.strip(),
                }

            # Start the watcher
            if START_SCRIPT.exists():
                subprocess.Popen(
                    [str(START_SCRIPT), "--daemon"],
                    cwd=str(ELF_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Watcher started successfully",
                }
            else:
                raise HTTPException(
                    status_code=500, detail="Watcher start script not found"
                )

        elif request.action == "stop":
            # Create stop file to signal watcher to stop
            STOP_FILE.touch()
            logger.info("Created watcher stop file")

            # Also try to kill the process directly
            result = subprocess.run(
                ["pkill", "-f", "watcher/launcher.py"], capture_output=True, text=True
            )

            return {
                "status": "ok",
                "action": "stop",
                "message": "Watcher stop signal sent",
            }

        elif request.action == "restart":
            # Stop first
            STOP_FILE.touch() if not STOP_FILE.exists() else None
            subprocess.run(["pkill", "-f", "watcher/launcher.py"], capture_output=True)

            # Wait a moment
            import time

            time.sleep(1)

            # Remove stop file
            if STOP_FILE.exists():
                STOP_FILE.unlink()

            # Start again
            if START_SCRIPT.exists():
                subprocess.Popen(
                    [str(START_SCRIPT), "--daemon"],
                    cwd=str(ELF_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return {
                    "status": "ok",
                    "action": "restart",
                    "message": "Watcher restarted successfully",
                }
            else:
                raise HTTPException(
                    status_code=500, detail="Watcher start script not found"
                )

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown action: {request.action}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))
