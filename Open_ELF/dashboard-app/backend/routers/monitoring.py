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

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import requests

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("monitoring")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("monitoring")

# Import database utilities
try:
    from utils.database import get_db_connection, dict_from_row
except ImportError:
    import sys
    from pathlib import Path

    # Add backend directory to path for imports
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

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

# Database path - Production database (restored with 6885 records)
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
    """Query events from the event chronicle (from SQL database)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        where_clause = "WHERE 1=1"
        params = []

        if event_type:
            where_clause += " AND event_type = ?"
            params.append(event_type)

        if source:
            where_clause += " AND source = ?"
            params.append(source)

        # Get recent events from database (use 'id' not 'event_id')
        query = f"""
        SELECT id, timestamp, event_type, source, data, summary
        FROM event_chronicle
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ?
        """

        cursor.execute(query, params + [limit])

        events = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[4]) if row[4] else {}
            except:
                data = {}

            events.append(
                {
                    "event_id": row[0],
                    "timestamp": row[1],
                    "event_type": row[2],
                    "source": row[3],
                    "data": data,
                    "summary": row[5],
                }
            )

        return {"events": events, "count": len(events)}

    except Exception as e:
        logger.error(f"Error fetching chronicle events from DB: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error querying chronicle: {str(e)}"
        )

@router.get("/chronicle/stats")
async def get_chronicle_stats():
    """Get event chronicle statistics (from SQL database)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total events count
        cursor.execute("SELECT COUNT(*) FROM event_chronicle")
        total_events = cursor.fetchone()[0]

        # Get event types distribution
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM event_chronicle
            GROUP BY event_type
        """)
        event_types = {row[0]: row[1] for row in cursor.fetchall()}

        # Get sources distribution
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM event_chronicle
            GROUP BY source
        """)
        sources = {row[0]: row[1] for row in cursor.fetchall()}

        # Get date range
        cursor.execute("""
            SELECT 
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM event_chronicle
        """)
        date_range_row = cursor.fetchone()

        date_range = {"earliest": date_range_row[0], "latest": date_range_row[1]}

        stats = {
            "total_events": total_events,
            "event_types": event_types,
            "sources": sources,
            "date_range": date_range,
        }

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
    """Return orchestrator status including services health."""
    # Check services health via Orchestrator
    import subprocess

    services_health = {
        "learning_capture": {"active": False, "running": False},
        "watcher": False,
        "event_bridge": False,
    }

    # Check EventBridge
    try:
        response = requests.get("http://localhost:9998/status", timeout=2)
        if response.status_code == 200:
            eb_status = response.json()
            services_health["event_bridge"] = eb_status.get("running", False)

            # Check if Learning Capture info is in EventBridge status
            if "services" in eb_status:
                services_health.update(eb_status["services"])
        else:
            _log_error(f"EventBridge health check failed: HTTP {response.status_code}")
    except Exception as e:
        _log_error(f"EventBridge health check failed: {e}")

    # Check Learning Capture directly
    try:
        result = subprocess.run(
            ["pgrep", "-f", "background-learning-capture.py"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            services_health["learning_capture"]["active"] = True
            services_health["learning_capture"]["running"] = True
            services_health["learning_capture"]["pid"] = result.stdout.strip()
    except:
        pass

    # Check Watcher
    try:
        result = subprocess.run(
            ["pgrep", "-f", "watcher/elf_watcher.py"], capture_output=True, text=True
        )
        services_health["watcher"] = result.returncode == 0
    except:
        services_health["watcher"] = False

    return {
        "status": "ok",
        "status_data": {
            "running": services_health["event_bridge"],
            "uptime_seconds": services_health.get("uptime_seconds", 0),
            "services": services_health,
            "last_check": datetime.now().isoformat(),
        },
    }

    # try:
    #     response = requests.get(status_url_forwards, timeout=3)
    #     if response.status_code == 200:
    #         status_payload = response.json()
    #     else:
    #         _log_error(f"Orchestrator status check failed: HTTP {response.status_code}")
    # except Exception as e:
    #     _log_error(f"Orchestrator status check failed: {e}")

    # return {
    #     "status": "ok",
    #     "status_data": {
    #         "running": bool(status_payload.get("running")),
    #         "missions_count": int(status_payload.get("missions_count", 0)),
    #         "last_check": datetime.now().isoformat(),
    #         "status_url": status_url,
    #     },
    #     "missions": status_payload.get("missions", []),
    # }

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

        # Check watchdog.log file for additional logs
        watchdog_log_path = ELF_DIR / "logs" / "watcher.log"
        if watchdog_log_path.exists():
            try:
                # Read last 50 lines from watcher.log
                with open(watchdog_log_path, "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines

                # Parse log lines
                import re

                # Log format: 2026-02-06 17:58:00 - elf.watcher - INFO - Message
                log_pattern = re.compile(
                    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (elf\.\w+) - (INFO|WARNING|ERROR) - (.+)"
                )

                for line in recent_lines:
                    match = log_pattern.match(line.strip())
                    if match:
                        timestamp_str, source, level, message = match.groups()
                        logs.append(
                            {
                                "timestamp": timestamp_str + ".000000",
                                "level": level.lower(),
                                "message": message,
                                "tier": "tier1",
                            }
                        )
            except Exception as log_err:
                _log_error(f"Error reading watcher.log: {log_err}")
        else:
            _log_debug(f"Watcher log file not found: {watchdog_log_path}")

        # Check if watcher process is actually running
        result = subprocess.run(
            ["pgrep", "-f", "watcher/elf_watcher.py"], capture_output=True, text=True
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
        last_check = row["last_check"] if row and row["last_check"] else None
        escalations = row["escalations"] if row and row["escalations"] else 0
        total_cycles = row["count"] if row and row["count"] else 0

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
            "total_checks": total_cycles,
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
        START_SCRIPT = Path.home() / ".opencode" / "scripts" / "start-watcher.sh"
        STOP_FILE = ELF_DIR / ".coordination" / "watcher-stop"
        PID_FILE = Path("/tmp") / "elf-watcher.pid"

        if request.action == "start":
            # Remove stop file if it exists
            if STOP_FILE.exists():
                STOP_FILE.unlink()
                logger.info("Removed watcher stop file")

            # Check if already running
            result = subprocess.run(
                ["pgrep", "-f", "watcher/elf_watcher.py"],
                capture_output=True,
                text=True,
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
                    ["pgrep", "-f", "watcher/elf_watcher.py"],
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
                ["pkill", "-f", "watcher/elf_watcher.py"],
                capture_output=True,
                text=True,
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
            subprocess.run(
                ["pkill", "-f", "watcher/elf_watcher.py"], capture_output=True
            )

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

@router.get("/monitoring/watcher/events")
async def get_watcher_events():
    """Get last 20 watcher events for monitoring card."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent watcher events (watcher_check, watcher_status, file changes)
        cursor.execute("""
            SELECT id, timestamp, event_type, source, summary, data
            FROM event_chronicle 
            WHERE event_type IN ('watcher_check', 'watcher_status', 'file_change', 'file_creation', 'file_deletion')
            ORDER BY timestamp DESC 
            LIMIT 20
        """)

        events = []
        for row in cursor.fetchall():
            event_data = dict_from_row(row)
            # Format for display
            event_data["display_type"] = event_data.get("event_type", "unknown")
            event_data["display_time"] = event_data.get("timestamp", "")
            event_data["display_message"] = (
                f"{event_data.get('source', 'watcher')}: {event_data.get('summary', 'No summary')}"
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

@router.get("/monitoring/orchestrator/events")
async def get_orchestrator_events():
    """Get last 20 orchestrator events (questions and responses) for monitoring card."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get recent orchestrator events - questions received and responses
        cursor.execute("""
            SELECT id, timestamp, event_type, source, summary, data
            FROM event_chronicle 
            WHERE event_type IN ('agent_question', 'agent_response', 'orchestrator_action', 'question_received', 'response_sent', 'orchestrator_decided')
            ORDER BY timestamp DESC 
            LIMIT 20
        """)

        events = []
        for row in cursor.fetchall():
            event_data = dict_from_row(row)

            # Categorize as question or response
            is_question = event_data.get("event_type") in [
                "agent_question",
                "question_received",
            ]
            event_data["event_category"] = "question" if is_question else "response"

            # Format display message
            if is_question:
                event_data["display_message"] = (
                    f"❓ Question: {event_data.get('summary', 'No question')}"
                )
            else:
                # Parse data to get response details if available
                data_obj = {}
                try:
                    if event_data.get("data"):
                        data_obj = json.loads(event_data["data"])
                except:
                    pass
                event_data["display_message"] = (
                    f"✅ Response: {event_data.get('summary', 'No response')}"
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

@router.get("/monitoring/ollama/status")
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

@router.post("/monitoring/system-health/update")
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

# ==============================================================================
# Escalations Endpoint - NEW
# ==============================================================================

@router.get("/escalations")
async def get_escalations(
    agent: Optional[str] = Query(default=None, description="Filter by agent: watcher, sentinel, ceo"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: info, warning, critical"),
    limit: int = Query(default=50, le=200, description="Number of escalations to return"),
    hours: int = Query(default=24, description="Look back period in hours")
):
    """
    Get escalations from all agents (watcher, sentinel, CEO).
    
    Escalations are events where agents have detected issues requiring attention.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query for escalation events
        where_conditions = ["timestamp > datetime('now', ?)"]
        params = [f'-{hours} hours']
        
        # Event types that represent escalations
        escalation_event_types = [
            'sentinel_cycle',      # Sentinel monitoring cycles with status
            'watcher_escalation',  # Watcher escalations
            'ceo_alert',          # CEO alerts
            'critical_event',     # General critical events
            'agent_escalation',   # Generic agent escalation
            'system_alert',       # System-level alerts
        ]
        
        # Build event type filter
        event_type_placeholders = ', '.join(['?' for _ in escalation_event_types])
        where_conditions.append(f"event_type IN ({event_type_placeholders})")
        params.extend(escalation_event_types)
        
        # Filter by agent if specified
        if agent:
            agent = agent.lower()
            if agent == 'watcher':
                where_conditions.append("(source LIKE '%watcher%' OR event_type LIKE '%watcher%')")
            elif agent == 'sentinel':
                where_conditions.append("(source LIKE '%sentinel%' OR event_type LIKE '%sentinel%')")
            elif agent == 'ceo':
                where_conditions.append("(source LIKE '%ceo%' OR event_type LIKE '%ceo%')")
        
        # Filter by severity if specified
        if severity:
            severity = severity.lower()
            where_conditions.append("(status = ? OR json_extract(data, '$.severity') = ? OR json_extract(data, '$.analysis.status') = ?)")
            params.extend([severity, severity, severity])
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT id, timestamp, event_type, source, summary, data, status
            FROM event_chronicle
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        
        escalations = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row["data"]) if row["data"] else {}
            except:
                data = {}
            
            # Determine severity from various possible locations
            severity = row["status"] or "info"
            if not severity or severity == "ok":
                severity = data.get("severity") or data.get("analysis", {}).get("status", "info")
            
            # Format escalation entry
            escalation = {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "agent": detect_agent_from_source(row["source"], row["event_type"]),
                "event_type": row["event_type"],
                "source": row["source"],
                "summary": row["summary"],
                "severity": severity,
                "data": data,
                "display_message": format_escalation_message(row, data),
                "requires_action": severity in ["warning", "critical"]
            }
            escalations.append(escalation)
        
        # Get summary statistics
        stats = {
            "total": len(escalations),
            "by_agent": {},
            "by_severity": {"info": 0, "warning": 0, "critical": 0},
            "requiring_action": sum(1 for e in escalations if e["requires_action"])
        }
        
        for esc in escalations:
            agent_name = esc["agent"]
            stats["by_agent"][agent_name] = stats["by_agent"].get(agent_name, 0) + 1
            sev = esc["severity"]
            if sev in stats["by_severity"]:
                stats["by_severity"][sev] += 1
        
        conn.close()
        
        return {
            "status": "ok",
            "escalations": escalations,
            "stats": stats,
            "filters": {
                "agent": agent,
                "severity": severity,
                "hours": hours,
                "limit": limit
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching escalations: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching escalations: {str(e)}")

def detect_agent_from_source(source: str, event_type: str) -> str:
    """Detect which agent generated this escalation."""
    source_lower = source.lower() if source else ""
    event_lower = event_type.lower() if event_type else ""
    
    if "watcher" in source_lower or "watcher" in event_lower:
        return "watcher"
    elif "sentinel" in source_lower or "sentinel" in event_lower:
        return "sentinel"
    elif "ceo" in source_lower or "ceo" in event_lower:
        return "ceo"
    elif "orchestrator" in source_lower or "orchestrator" in event_lower:
        return "orchestrator"
    elif "experiment" in source_lower or "analyzer" in source_lower:
        return "experiment-analyzer"
    else:
        return "unknown"

def format_escalation_message(row, data: Dict) -> str:
    """Format a human-readable message for the escalation."""
    summary = row["summary"] or "No summary"
    event_type = row["event_type"]
    
    # Add severity indicator
    severity = data.get("severity") or data.get("analysis", {}).get("status", "info")
    severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
    
    # Format based on event type
    if "sentinel" in event_type:
        return f"{severity_emoji} Sentinel: {summary}"
    elif "watcher" in event_type:
        return f"{severity_emoji} Watcher: {summary}"
    elif "ceo" in event_type:
        return f"{severity_emoji} CEO: {summary}"
    else:
        return f"{severity_emoji} {event_type}: {summary}"

@router.get("/escalations/summary")
async def get_escalations_summary(hours: int = Query(default=24, description="Look back period in hours")):
    """Get a summary of recent escalations by agent and severity."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts by agent
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN source LIKE '%watcher%' OR event_type LIKE '%watcher%' THEN 'watcher'
                    WHEN source LIKE '%sentinel%' OR event_type LIKE '%sentinel%' THEN 'sentinel'
                    WHEN source LIKE '%ceo%' OR event_type LIKE '%ceo%' THEN 'ceo'
                    WHEN source LIKE '%orchestrator%' OR event_type LIKE '%orchestrator%' THEN 'orchestrator'
                    ELSE 'other'
                END as agent,
                COUNT(*) as count,
                status
            FROM event_chronicle
            WHERE timestamp > datetime('now', ?)
            AND event_type IN ('sentinel_cycle', 'watcher_escalation', 'ceo_alert', 'critical_event', 'agent_escalation')
            GROUP BY agent, status
        """, (f'-{hours} hours',))
        
        agent_summary = {}
        for row in cursor.fetchall():
            agent = row["agent"]
            if agent not in agent_summary:
                agent_summary[agent] = {"total": 0, "critical": 0, "warning": 0, "info": 0, "ok": 0}
            
            status = row["status"] or "info"
            count = row["count"]
            
            agent_summary[agent]["total"] += count
            if status in agent_summary[agent]:
                agent_summary[agent][status] = count
        
        # Get recent critical escalations
        cursor.execute("""
            SELECT timestamp, source, summary, status
            FROM event_chronicle
            WHERE timestamp > datetime('now', ?)
            AND status IN ('critical', 'warning')
            ORDER BY timestamp DESC
            LIMIT 10
        """, (f'-{hours} hours',))
        
        recent_critical = [
            {
                "timestamp": row["timestamp"],
                "agent": detect_agent_from_source(row["source"], ""),
                "summary": row["summary"],
                "severity": row["status"]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            "status": "ok",
            "summary": {
                "by_agent": agent_summary,
                "recent_critical": recent_critical,
                "total_escalations": sum(a["total"] for a in agent_summary.values())
            },
            "period_hours": hours,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching escalations summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")
