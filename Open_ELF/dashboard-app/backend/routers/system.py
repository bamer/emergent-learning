"""
System Services Router - Dashboard API Integration

This router provides endpoints for:
- Checking system service health (Sentinel, Sentinel, EventBridge, Learning Capture)
- Service status monitoring (running/stopped, PID, uptime)
- Control of system services (start/stop/restart)
- System-wide metrics

Replaces agent registry monitoring with direct service health checks.
Refactoring alignment (2026-02-09)
"""

import json
import re
import subprocess
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error, log_warning

    logger = get_logger("system_services")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("system_services")


router = APIRouter(prefix="/api/v1/system", tags=["system"])

# Paths
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
OPEN_ELF_DIR = ELF_DIR / "Open_ELF"
ORCHESTRATOR_DIR = OPEN_ELF_DIR / "orchestrator"
COORDINATION_DIR = ELF_DIR / ".coordination"


# ============================================================================
# Data Models
# ============================================================================


class ServiceStatus(BaseModel):
    """Individual service status."""

    name: str
    type: str  # agent, service, system
    running: bool
    pid: Optional[int]
    uptime_seconds: Optional[float] = None
    last_heartbeat: Optional[str] = None
    health: str  # healthy, degraded, unhealthy
    metadata: Dict[str, Any] = {}


class SystemServicesResponse(BaseModel):
    """Full system services response."""

    services: Dict[str, ServiceStatus]
    health_overall: str  # healthy, degraded, unhealthy
    last_check: str


class ServiceControlRequest(BaseModel):
    """Service control request."""

    action: str  # start, stop, restart


# ============================================================================
# Service Detection Functions
# ============================================================================


def check_process_by_name(name: str) -> Dict[str, Any]:
    """Check if a process is running by name."""
    try:
        result = subprocess.run(["pgrep", "-f", name], capture_output=True, text=True)
        pids = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if pids and pids[0]:
            pid = int(pids[0])
            return {"running": True, "pid": pid}
        else:
            return {"running": False, "pid": None}
    except Exception as e:
        logger.error(f"Error checking process {name}: {e}")
        return {"running": False, "pid": None}


def check_port_listening(port: int) -> bool:
    """Check if a port is being listened on."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    except:
        return False


def get_service_heartbeat(service_name: str) -> Optional[str]:
    """Get last heartbeat timestamp from coordination database."""
    try:
        db_path = ELF_DIR / "memory" / "index.db"
        if not db_path.exists():
            return None

        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check coord_agents table first
        cursor.execute(
            """
            SELECT last_heartbeat
            FROM coord_agents
            WHERE name = ?
            ORDER BY last_heartbeat DESC
            LIMIT 1
        """,
            (service_name,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return row["last_heartbeat"]

    except Exception as e:
        logger.debug(f"Error getting heartbeat for {service_name}: {e}")

    return None


def get_orchestrator_services() -> Dict[str, Any]:
    """Get services status from Unified Orchestrator."""
    try:
        orchestrator_status_file = COORDINATION_DIR / "orchestrator_status.json"
        if not orchestrator_status_file.exists():
            return {}

        return json.loads(orchestrator_status_file.read_text())
    except Exception as e:
        logger.debug(f"Error reading orchestrator status: {e}")
        return {}


def calculate_health(running: bool, last_heartbeat: Optional[str]) -> str:
    """Calculate service health based on status and heartbeat."""
    if not running:
        return "unhealthy"

    if last_heartbeat:
        try:
            last_hb = datetime.fromisoformat(last_heartbeat)
            age_seconds = (datetime.now() - last_hb).total_seconds()

            if age_seconds < 60:  # Fresh heartbeat
                return "healthy"
            elif age_seconds < 300:  # Heartbeat up to 5 minutes old
                return "degraded"
            else:  # Stale heartbeat
                return "unhealthy"
        except:
            return "healthy"  # Assume healthy if we can't parse the timestamp

    return "healthy"  # Running without heartbeat tracking


# ============================================================================
# Service Status Functions
# ============================================================================


def get_sentinel_status() -> ServiceStatus:
    """Get Sentinel monitoring status."""
    proc_info = check_process_by_name("sentinel")

    # Try to get heartbeat from sentinel-log
    heartbeat = None
    sentinel_log = COORDINATION_DIR / "sentinel-log.md"
    if sentinel_log.exists():
        # Extract last timestamp from log
        try:
            content = sentinel_log.read_text()
            matches = list(re.finditer(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", content))
            if matches:
                heartbeat = matches[-1].group()
        except:
            pass

    health = calculate_health(proc_info["running"], heartbeat)

    return ServiceStatus(
        name="sentinel",
        type="agent",
        running=proc_info["running"],
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=heartbeat,
        health=health,
        metadata={"log_file": str(sentinel_log)},
    )


def get_sentinel_status() -> ServiceStatus:
    """Get Sentinel monitoring status."""
    proc_info = check_process_by_name("sentinel")

    # Get heartbeat from coordination database
    heartbeat = get_service_heartbeat("sentinel")

    health = calculate_health(proc_info["running"], heartbeat)

    return ServiceStatus(
        name="sentinel",
        type="agent",
        running=proc_info["running"],
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=heartbeat,
        health=health,
        metadata={},
    )


def get_event_bridge_status() -> ServiceStatus:
    """Get EventBridge status."""
    # EventBridge is on port 9998
    port_listening = check_port_listening(9998)
    proc_info = check_process_by_name("event_bridge")

    # Read heartbeat file
    heartbeat = None
    heartbeat_file = COORDINATION_DIR / "event-bridge-heartbeat.json"
    if heartbeat_file.exists():
        try:
            data = json.loads(heartbeat_file.read_text())
            heartbeat = data.get("last_heartbeat") or data.get("timestamp")
        except:
            pass

    health = calculate_health(port_listening, heartbeat)

    return ServiceStatus(
        name="event_bridge",
        type="service",
        running=port_listening,
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=heartbeat,
        health=health,
        metadata={
            "heartbeat_file": str(heartbeat_file),
            "api_port": 9998,
            "port": 9998 if port_listening else None,
        },
    )


def get_orchestrator_status() -> ServiceStatus:
    """Get Unified Orchestrator status."""
    # Orchestrator runs on port 9998 (via EventBridge API)
    port_listening = check_port_listening(9998)
    proc_info = check_process_by_name("orchestrator.py")

    # Get services from orchestrator
    orchestrator_data = get_orchestrator_services()

    health = calculate_health(port_listening, orchestrator_data.get("last_check"))

    return ServiceStatus(
        name="orchestrator",
        type="system",
        running=port_listening,
        pid=proc_info["pid"],
        uptime_seconds=orchestrator_data.get("uptime_seconds"),
        last_heartbeat=orchestrator_data.get("last_check"),
        health=health,
        metadata={
            "services": orchestrator_data.get("services", {}),
            "missions_count": orchestrator_data.get("missions_count", 0),
        },
    )


def get_learning_capture_status() -> ServiceStatus:
    """Get Learning Capture service status."""
    proc_info = check_process_by_name("learning-capture.py")

    # Get heartbeat from coord_agents
    heartbeat = get_service_heartbeat("learning_capture")

    health = calculate_health(proc_info["running"], heartbeat)

    return ServiceStatus(
        name="learning_capture",
        type="service",
        running=proc_info["running"],
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=heartbeat,
        health=health,
        metadata={"log_file": str(OPEN_ELF_DIR / "logs" / "learning-capture.log")},
    )


def get_ceo_monitor_status() -> ServiceStatus:
    """Get CEO Inbox Monitor status."""
    proc_info = check_process_by_name("ceo_inbox_monitor")

    # Check for monitor log
    heartbeat = None
    monitor_log = COORDINATION_DIR / "ceo-monitor.log"
    if monitor_log.exists():
        try:
            content = monitor_log.read_text()
            matches = list(
                re.finditer(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", content)
            )
            if matches:
                heartbeat = matches[-1].group() + "Z"
        except:
            pass

    health = calculate_health(proc_info["running"], heartbeat)

    return ServiceStatus(
        name="ceo_monitor",
        type="agent",
        running=proc_info["running"],
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=heartbeat,
        health=health,
        metadata={"log_file": str(monitor_log)},
    )


def get_dashboard_backend_status() -> ServiceStatus:
    """Get Dashboard Backend status."""
    # Dashboard backend is on port 8888 (or configured port)
    port_listening = check_port_listening(8888)
    proc_info = check_process_by_name("uvicorn.*main:app")

    health = "healthy" if port_listening else "unhealthy"

    return ServiceStatus(
        name="dashboard_backend",
        type="service",
        running=port_listening,
        pid=proc_info["pid"],
        uptime_seconds=None,
        last_heartbeat=None,
        health=health,
        metadata={"port": 8888},
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/services", response_model=SystemServicesResponse)
async def get_system_services():
    """Get status of all ELF system services."""
    try:
        # Collect all service statuses as actual objects
        services = {
            "orchestrator": get_orchestrator_status(),
            "event_bridge": get_event_bridge_status(),
            "sentinel": get_sentinel_status(),
            "sentinel": get_sentinel_status(),
            "learning_capture": get_learning_capture_status(),
            "ceo_monitor": get_ceo_monitor_status(),
            "dashboard_backend": get_dashboard_backend_status(),
        }

        # Calculate overall health
        healthy_count = sum(1 for s in services.values() if s.health == "healthy")
        total_count = len(services)

        if healthy_count == total_count:
            overall_health = "healthy"
        elif healthy_count >= total_count * 0.7:
            overall_health = "degraded"
        else:
            overall_health = "unhealthy"

        return SystemServicesResponse(
            services=services,
            health_overall=overall_health,
            last_check=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting system services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}", response_model=ServiceStatus)
async def get_service_status(service_name: str):
    """Get status of a specific service."""
    service_getters = {
        "orchestrator": get_orchestrator_status,
        "event_bridge": get_event_bridge_status,
        "sentinel": get_sentinel_status,
        "sentinel": get_sentinel_status,
        "learning_capture": get_learning_capture_status,
        "ceo_monitor": get_ceo_monitor_status,
        "dashboard_backend": get_dashboard_backend_status,
    }

    getter = service_getters.get(service_name.lower())
    if not getter:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    try:
        return getter()
    except Exception as e:
        logger.error(f"Error getting service status for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health():
    """Get overall system health summary."""
    try:
        services_response = await get_system_services()
        services = services_response.services

        # Count critical components
        critical_services = ["orchestrator", "event_bridge", "sentinel", "sentinel"]
        critical_running = sum(
            1 for name in critical_services if services[name].running
        )

        # Get database health
        db_healthy = False
        db_path = ELF_DIR / "memory" / "index.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path), timeout=5.0)
                conn.execute("PRAGMA integrity_check").fetchone()
                conn.close()
                db_healthy = True
            except:
                pass

        # Get disk space
        disk_usage = subprocess.run(["df", "-h"], capture_output=True, text=True).stdout

        return {
            "overall": services_response.health_overall,
            "critical_running": critical_running,
            "critical_total": len(critical_services),
            "database_healthy": db_healthy,
            "last_check": services_response.last_check,
            "disk_usage": disk_usage,
        }

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/services/{service_name}/control")
async def control_service(service_name: str, request: ServiceControlRequest):
    """Control a system service (start/stop/restart).

    Note: This is a placeholder. Actual service control should be handled
    by the Unified Orchestrator or dedicated service management scripts.
    """
    allowed_services = ["sentinel", "sentinel", "learning_capture", "ceo_monitor"]
    action = request.action.lower()

    if service_name.lower() not in allowed_services:
        raise HTTPException(
            status_code=400,
            detail=f"Service {service_name} cannot be controlled via API",
        )

    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    # Log the request - actual implementation would execute the control
    logger.info(f"Service control requested: {service_name} {action}")

    # Placeholder response
    return {
        "status": "pending",
        "message": f"Service control request queued: {service_name} {action}",
        "action": action,
        "service": service_name,
    }
