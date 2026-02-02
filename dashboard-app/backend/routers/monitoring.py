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
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import requests

# Import database utilities
try:
    from utils.database import get_db_connection, dict_from_row
except ImportError:

    def get_db_connection():
        import sqlite3

        db_path = (
            Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
        )
        return sqlite3.connect(str(db_path))

    def dict_from_row(row):
        """Convert sqlite3.Row to dict"""
        return dict(row) if hasattr(row, "keys") else row


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unified logging (best-effort)
try:
    sys.path.insert(0, str(Path.home() / ".opencode" / "emergent-learning" / "agents"))
    import logging

    logger = logging.getLogger(__name__)

    unified_logger = logger

    def _log_info(message: str) -> None:
        logger.info(message)

    def _log_error(message: str) -> None:
        logger.error(message)

except Exception:
    unified_logger = logger

    def _log_info(message: str) -> None:
        logger.info(message)

    def _log_error(message: str) -> None:
        logger.error(message)


router = APIRouter(prefix="/api/v1", tags=["monitoring"])

# Database path
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
EVENT_CHRONICLE_DIR = (
    Path.home() / ".opencode" / "emergent-learning" / "event_chronicle"
)
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
HOOKS_DIR = Path.home() / ".opencode" / "hooks"
COORDINATION_DIR = ELF_DIR / ".coordination"
EVENT_BRIDGE_HEARTBEAT = COORDINATION_DIR / "event-bridge-heartbeat.json"
OPENCODE_SERVER = "http://localhost:4096"


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
# Event Bridge Control Request Model
# ==============================================================================


class EventBridgeControlRequest(BaseModel):
    action: str  # 'start', 'stop', 'restart'


class OrchestratorControlRequest(BaseModel):
    action: str  # 'start', 'stop', 'restart'


# ==============================================================================
# Event Bridge Endpoints
# ==============================================================================


@router.get("/event-bridge/status")
async def get_event_bridge_status():
    """Return Event Bridge status based on hook heartbeat + OpenCode reachability."""
    now = datetime.now()
    hooks_dir = HOOKS_DIR
    opencode_status = "unknown"
    last_event_time = None
    events_processed = 0
    uptime_seconds = None

    if EVENT_BRIDGE_HEARTBEAT.exists():
        try:
            payload = json.loads(EVENT_BRIDGE_HEARTBEAT.read_text(encoding="utf-8"))
            last_event_time = payload.get("last_event_time")
            events_processed = int(payload.get("events_processed", 0))
            started_at = payload.get("started_at") or payload.get("created_at")
            if started_at:
                try:
                    uptime_seconds = int(
                        (now - datetime.fromisoformat(started_at)).total_seconds()
                    )
                except ValueError:
                    uptime_seconds = None
        except json.JSONDecodeError:
            last_event_time = None

    # Check OpenCode server reachability
    try:
        response = requests.get(f"{OPENCODE_SERVER}/health", timeout=3)
        opencode_status = "ok" if response.status_code < 400 else "error"
    except Exception:
        opencode_status = "error"

    # Determine running status based on heartbeat freshness
    running = False
    if last_event_time:
        try:
            last_time = datetime.fromisoformat(last_event_time)
            running = (now - last_time).total_seconds() < 120
        except ValueError:
            running = False

    return {
        "running": running,
        "events_processed": events_processed,
        "hooks_dir": str(hooks_dir),
        "opencode_server": OPENCODE_SERVER,
        "opencode_status": opencode_status,
        "uptime_seconds": uptime_seconds,
        "last_event_time": last_event_time,
    }


# ==============================================================================
# Orchestrator Endpoints
# ==============================================================================


@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """Return orchestrator status from the Open_ELF status server."""
    status_url = "http://localhost:9999/status"
    status_payload = {
        "running": False,
        "missions_count": 0,
        "missions": [],
    }

    try:
        response = requests.get(status_url, timeout=3)
        if response.status_code == 200:
            status_payload = response.json()
        else:
            _log_error(f"Orchestrator status check failed: HTTP {response.status_code}")
    except Exception as e:
        _log_error(f"Orchestrator status check failed: {e}")

    return {
        "status": "ok",
        "status_data": {
            "running": bool(status_payload.get("running")),
            "missions_count": int(status_payload.get("missions_count", 0)),
            "last_check": datetime.now().isoformat(),
            "status_url": status_url,
        },
        "missions": status_payload.get("missions", []),
    }


@router.post("/orchestrator/control")
async def control_orchestrator(request: OrchestratorControlRequest):
    """Control Open_ELF orchestrator (start/stop/restart)."""
    try:
        _log_info(f"Orchestrator control action: {request.action}")

        orchestrator_script = ELF_DIR / "Open_ELF" / "orchestrator" / "orchestrator.py"

        if request.action == "start":
            result = subprocess.run(
                ["pgrep", "-f", "orchestrator.py"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                _log_info("Orchestrator already running")
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Orchestrator is already running",
                    "pid": result.stdout.strip(),
                }

            if orchestrator_script.exists():
                _log_info(f"Launching orchestrator: {orchestrator_script}")
                subprocess.Popen(
                    ["python3", str(orchestrator_script), "start"],
                    cwd=str(orchestrator_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1)
                check = subprocess.run(
                    ["pgrep", "-f", "orchestrator.py"],
                    capture_output=True,
                    text=True,
                )
                _log_info(
                    "Orchestrator start check: running"
                    if check.returncode == 0
                    else "Orchestrator start check: not running"
                )
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Orchestrator started successfully"
                    if check.returncode == 0
                    else "Orchestrator start requested (not yet running)",
                }
            _log_error("Orchestrator script not found")
            raise HTTPException(status_code=500, detail="Orchestrator script not found")

        if request.action == "stop":
            subprocess.run(
                ["pkill", "-f", "orchestrator.py"],
                capture_output=True,
                text=True,
            )
            _log_info("Orchestrator stop signal sent")
            return {
                "status": "ok",
                "action": "stop",
                "message": "Orchestrator stop signal sent",
            }

        if request.action == "restart":
            subprocess.run(
                ["pkill", "-f", "orchestrator.py"],
                capture_output=True,
                text=True,
            )
            time.sleep(1)
            if orchestrator_script.exists():
                _log_info("Restarting orchestrator")
                subprocess.Popen(
                    ["python3", str(orchestrator_script), "start"],
                    cwd=str(orchestrator_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return {
                    "status": "ok",
                    "action": "restart",
                    "message": "Orchestrator restarted successfully",
                }
            _log_error("Orchestrator script not found")
            raise HTTPException(status_code=500, detail="Orchestrator script not found")

        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    except HTTPException:
        raise
    except Exception as e:
        _log_error(f"Error controlling orchestrator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event-bridge/control")
async def control_event_bridge(request: EventBridgeControlRequest):
    """Control Event Bridge (start/stop/restart)."""
    try:
        _log_info(f"Event Bridge control action: {request.action}")

        bridge_script = ELF_DIR / "Open_ELF" / "orchestrator" / "event_bridge.py"

        if request.action == "start":
            result = subprocess.run(
                ["pgrep", "-f", "event_bridge.py"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                _log_info("Event Bridge already running")
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Event Bridge is already running",
                    "pid": result.stdout.strip(),
                }

            if bridge_script.exists():
                _log_info(f"Launching Event Bridge: {bridge_script}")
                subprocess.Popen(
                    ["python3", str(bridge_script), "start"],
                    cwd=str(bridge_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1)
                check = subprocess.run(
                    ["pgrep", "-f", "event_bridge.py"],
                    capture_output=True,
                    text=True,
                )
                _log_info(
                    "Event Bridge start check: running"
                    if check.returncode == 0
                    else "Event Bridge start check: not running"
                )
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Event Bridge started successfully"
                    if check.returncode == 0
                    else "Event Bridge start requested (not yet running)",
                }
            _log_error("Event Bridge script not found")
            raise HTTPException(status_code=500, detail="Event Bridge script not found")

        if request.action == "stop":
            subprocess.run(
                ["pkill", "-f", "event_bridge.py"],
                capture_output=True,
                text=True,
            )
            _log_info("Event Bridge stop signal sent")
            return {
                "status": "ok",
                "action": "stop",
                "message": "Event Bridge stop signal sent",
            }

        if request.action == "restart":
            subprocess.run(
                ["pkill", "-f", "event_bridge.py"],
                capture_output=True,
                text=True,
            )
            time.sleep(1)
            if bridge_script.exists():
                _log_info("Restarting Event Bridge")
                subprocess.Popen(
                    ["python3", str(bridge_script), "start"],
                    cwd=str(bridge_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return {
                    "status": "ok",
                    "action": "restart",
                    "message": "Event Bridge restarted successfully",
                }
            _log_error("Event Bridge script not found")
            raise HTTPException(status_code=500, detail="Event Bridge script not found")

        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    except HTTPException:
        raise
    except Exception as e:
        _log_error(f"Error controlling Event Bridge: {e}")
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

        # Get current health - Use actual columns in system_health table
        cursor.execute(
            """
            SELECT id, timestamp, status, db_integrity, db_size_mb, disk_free_mb,
                   git_status, stale_locks, details
            FROM system_health
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )

        current_row = cursor.fetchone()
        current = None
        if current_row:
            current = dict(current_row)

        # Get recent history - Use actual columns in system_health table
        cursor.execute(
            """
            SELECT id, timestamp, status, db_integrity, db_size_mb, disk_free_mb,
                   git_status, stale_locks, details
            FROM system_health
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
        _log_info(f"Watcher control action: {request.action}")

        ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
        WATCHER_DIR = ELF_DIR / "watcher"
        START_SCRIPT = (
            Path.home() / ".opencode" / "scripts" / "start-watcher-corrected.sh"
        )
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
                _log_info("Watcher already running")
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Watcher is already running",
                    "pid": result.stdout.strip(),
                }

            # Start the watcher
            if START_SCRIPT.exists():
                _log_info(f"Launching watcher via {START_SCRIPT}")
                subprocess.Popen(
                    [str(START_SCRIPT), "--daemon"],
                    cwd=str(ELF_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1)
                check = subprocess.run(
                    ["pgrep", "-f", "watcher/launcher.py"],
                    capture_output=True,
                    text=True,
                )
                _log_info(
                    "Watcher start check: running"
                    if check.returncode == 0
                    else "Watcher start check: not running"
                )
                return {
                    "status": "ok",
                    "action": "start",
                    "message": "Watcher started successfully"
                    if check.returncode == 0
                    else "Watcher start requested (not yet running)",
                }
            else:
                _log_error("Watcher start script not found")
                raise HTTPException(
                    status_code=500, detail="Watcher start script not found"
                )

        elif request.action == "stop":
            # Create stop file to signal watcher to stop
            STOP_FILE.touch()
            _log_info("Created watcher stop file")

            # Also try to kill the process directly
            result = subprocess.run(
                ["pkill", "-f", "watcher/launcher.py"], capture_output=True, text=True
            )
            _log_info("Watcher stop signal sent")

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
            time.sleep(1)

            # Remove stop file
            if STOP_FILE.exists():
                STOP_FILE.unlink()

            # Start again
            if START_SCRIPT.exists():
                _log_info("Restarting watcher")
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
                _log_error("Watcher start script not found")
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
        _log_error(f"Error controlling watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/monitoring/watcher/events")
async def get_watcher_events():
    """Get last 20 watcher events for monitoring card."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent file monitoring events
        cursor.execute("""
            SELECT id, timestamp, type, tool, input_summary, output_summary, outcome,
                   session_id, agent_id, file_path
            FROM event_chronicle 
            WHERE type IN ('file_change', 'file_creation', 'file_deletion', 'watcher_status')
            ORDER BY timestamp DESC 
            LIMIT 20
        """)

        events = []
        for row in cursor.fetchall():
            event_data = dict_from_row(row)
            # Format for display
            event_data["display_type"] = event_data.get("type", "unknown")
            event_data["display_time"] = event_data.get("timestamp", "")
            event_data["display_message"] = (
                f"{event_data.get('tool', 'watcher')}: {event_data.get('input_summary', 'No summary')}"
            )
            events.append(event_data)

        conn.close()

        return {
            "status": "ok",
            "events": events,
            "total_count": len(events),
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching watcher events: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/api/v1/monitoring/orchestrator/events")
async def get_orchestrator_events():
    """Get last 20 orchestrator events (questions and responses) for monitoring card."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent orchestrator events - questions received and responses
        cursor.execute("""
            SELECT id, timestamp, type, tool, input_summary, output_summary, outcome,
                   session_id, agent_id
            FROM event_chronicle 
            WHERE type IN ('agent_question', 'agent_response', 'orchestrator_action', 'question_received', 'response_sent')
            ORDER BY timestamp DESC 
            LIMIT 20
        """)

        events = []
        for row in cursor.fetchall():
            event_data = dict_from_row(row)

            # Categorize as question or response
            is_question = event_data.get("type") in [
                "agent_question",
                "question_received",
            ]
            event_data["event_category"] = "question" if is_question else "response"

            # Format display message
            if is_question:
                event_data["display_message"] = (
                    f"❓ Question: {event_data.get('input_summary', 'No question')}"
                )
            else:
                event_data["display_message"] = (
                    f"✅ Response: {event_data.get('output_summary', 'No response')}"
                )

            event_data["display_type"] = "Question" if is_question else "Response"
            event_data["display_time"] = event_data.get("timestamp", "")

            events.append(event_data)

        conn.close()

        return {
            "status": "ok",
            "events": events,
            "total_count": len(events),
            "question_count": len(
                [e for e in events if e.get("event_category") == "question"]
            ),
            "response_count": len(
                [e for e in events if e.get("event_category") == "response"]
            ),
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching orchestrator events: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/api/v1/monitoring/ollama/status")
async def get_ollama_status():
    """Get Ollama embeddings service status for monitoring."""
    try:
        import requests

        # Check if Ollama service is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            ollama_running = response.status_code == 200
        except:
            ollama_running = False

        # Test embedding generation
        embedding_status = "not_tested"
        if ollama_running:
            try:
                test_response = requests.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": "test embedding"},
                    timeout=10,
                )
                if test_response.status_code == 200:
                    embedding_status = "working"
                else:
                    embedding_status = "error"
            except:
                embedding_status = "failed"

        # Get models available
        models = []
        if ollama_running:
            try:
                tags_response = requests.get(
                    "http://localhost:11434/api/tags", timeout=5
                )
                if tags_response.status_code == 200:
                    models_data = tags_response.json()
                    models = [
                        model.get("name", "") for model in models_data.get("models", [])
                    ]
            except:
                models = []

        return {
            "status": "ok",
            "service_running": ollama_running,
            "embedding_status": embedding_status,
            "models_available": models,
            "embedding_model": "nomic-embed-text"
            if "nomic-embed-text" in models
            else None,
            "service_url": "http://localhost:11434",
            "last_checked": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return {
            "status": "error",
            "service_running": False,
            "embedding_status": "unknown",
            "error": str(e),
            "last_checked": datetime.now().isoformat(),
        }


@router.post("/api/v1/monitoring/system-health/update")
async def update_system_health():
    """Update system health record with current status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check database integrity (fix typo)
        db_integrity = "ok"
        try:
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            if integrity_result and integrity_result[0] == "ok":
                db_integrity = "Integrity Check ✅ Passed"
            else:
                db_integrity = "Integrity Check ❌ Failed"
        except Exception:
            db_integrity = "Integrity Check ❌ Failed"

        # Get database size
        cursor.execute("PRAGMA page_count")
        page_count_result = cursor.fetchone()
        page_count = page_count_result[0] if page_count_result else 0
        cursor.execute("PRAGMA page_size")
        page_size_result = cursor.fetchone()
        page_size = page_size_result[0] if page_size_result else 4096
        db_size_mb = (page_count * page_size) / (1024 * 1024)

        # Get disk space
        import shutil

        disk_free_mb = shutil.disk_usage("/").free / (1024 * 1024)

        # Get git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            git_status = "Clean" if not result.stdout else "Modified files"
        except:
            git_status = "Unknown"

        # Insert new health record
        cursor.execute(
            """
            INSERT INTO system_health (timestamp, status, db_integrity, db_size_mb, 
                                     disk_free_mb, git_status, stale_locks, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.now().isoformat(),
                "ok",
                db_integrity,
                db_size_mb,
                disk_free_mb,
                git_status,
                0,  # stale_locks - would need implementation
                json.dumps(
                    {
                        "embedding_service": "ollama",
                        "dashboard_version": "1.0",
                        "monitoring_active": True,
                    }
                ),
            ),
        )

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "db_integrity": db_integrity,
            "db_size_mb": round(db_size_mb, 2),
            "disk_free_mb": round(disk_free_mb, 2),
            "git_status": git_status,
            "updated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error updating system health: {e}")
        return {"status": "error", "error": str(e)}
