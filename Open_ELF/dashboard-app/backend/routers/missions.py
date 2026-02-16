# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Missions Router - Dashboard API Integration with Mission Engine

This router provides endpoints for:
- Listing missions by status (pending, running, completed, failed, archive)
- Mission details and metadata
- Mission control (start, stop, restart)
- Mission history and logs
- Mission metrics

Added in v0.5.3 - Refactoring alignment (2026-02-09)
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error, log_warning

    logger = get_logger("missions")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("missions")


router = APIRouter(prefix="/api/v1/missions", tags=["missions"])

# Paths
ELF_DIR = Path.home() / ".opencode" / "emergent-learning"
MISSIONS_DIR = ELF_DIR / ".coordination" / "missions"

# Mission status directories
MISSION_STATUS_DIRS = {
    "pending": MISSIONS_DIR / "pending",
    "running": MISSIONS_DIR / "running",
    "completed": MISSIONS_DIR / "completed",
    "failed": MISSIONS_DIR / "failed",
    "archive": MISSIONS_DIR / "archive",
}


# ============================================================================
# Data Models
# ============================================================================


class MissionStatus(BaseModel):
    """Mission status summary."""

    total: int
    pending: int
    running: int
    completed: int
    failed: int
    archived: int


class Mission(BaseModel):
    """Mission data."""

    id: str
    title: str
    mission: str
    agent_type: str
    status: str
    priority: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    metadata: Dict[str, Any]
    logs: List[str]
    file_path: str


class MissionControlRequest(BaseModel):
    """Mission control request."""

    action: str  # start, stop, restart, cancel, retry


class MissionCreateRequest(BaseModel):
    """Mission creation request."""

    task: str
    mode: str = "smart"  # smart, auto, swarm, manual
    model_id: Optional[str] = None
    agent_type: Optional[str] = None


class MissionResult(BaseModel):
    """Mission result data."""

    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    heuristics_count: int = 0
    execution_time_seconds: Optional[float] = None
    completed_at: Optional[str] = None


class MissionStats(BaseModel):
    """Mission statistics."""

    total_missions: int
    success_rate: float
    avg_duration: float
    agent_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]


# ============================================================================
# Parsing Functions
# ============================================================================


def parse_mission_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse a mission file (JSON or Markdown).

    Handles both JSON files and Markdown files with frontmatter.
    """
    try:
        if file_path.suffix == ".json":
            # JSON format
            content = json.loads(file_path.read_text())
            return content

        elif file_path.suffix == ".md":
            # Markdown format with frontmatter
            content = file_path.read_text()

            # Extract frontmatter
            frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            frontmatter = {}
            if frontmatter_match:
                frontmatter_text = frontmatter_match.group(1)
                for line in frontmatter_text.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip()

            # Extract body as mission description
            body_match = re.search(r"---\n(.*)", content, re.DOTALL)
            body = body_match.group(1).strip() if body_match else ""

            # Create mission object
            mission_id = file_path.stem.replace("mission_", "")

            mission = {
                "id": mission_id,
                "title": frontmatter.get("title", mission_id),
                "mission": body[:200] + "..." if len(body) > 200 else body,
                "agent_type": frontmatter.get("agent", "unknown"),
                "status": file_path.parent.name,
                "priority": frontmatter.get("priority", "medium").lower(),
                "created_at": frontmatter.get(
                    "created_at",
                    datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                ),
                "started_at": frontmatter.get("started_at"),
                "completed_at": frontmatter.get("completed_at"),
                "metadata": frontmatter,
                "logs": [],
                "file_path": str(file_path),
            }

            # Extract error details if failed
            if file_path.parent.name == "failed" and "error" in frontmatter:
                mission["error"] = frontmatter["error"]

            return mission

    except Exception as e:
        logger.error(f"Error parsing mission file {file_path}: {e}")
        return None


def get_mission_status_counts() -> Dict[str, int]:
    """Get count of missions by status."""
    counts = {
        "total": 0,
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "archived": 0,
    }

    for status, path in MISSION_STATUS_DIRS.items():
        if path.exists():
            files = list(path.glob("mission_*.*"))
            counts[status] = len(files)
            counts["total"] += len(files)

    return counts


def check_mission_process(mission_id: str) -> bool:
    """Check if a mission is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"mission.*{mission_id}"], capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    except:
        return False


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/status", response_model=MissionStatus)
async def get_mission_status():
    """Get overall mission status summary."""
    try:
        counts = get_mission_status_counts()
        return MissionStatus(**counts)

    except Exception as e:
        logger.error(f"Error getting mission status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
@router.post("")
async def create_mission(request: MissionCreateRequest):
    """
    Create and execute a new mission.

    This endpoint creates a mission and triggers execution via the agent system.
    Supports multiple execution modes:
    - smart: AI determines best approach
    - auto: Automatic agent selection
    - swarm: Multi-agent coordination
    - manual: Specific agent/model selection
    """
    import uuid
    from datetime import datetime

    try:
        # Generate mission ID
        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        # Determine agent type based on mode
        agent_type = request.agent_type or "general"

        # Create mission file in pending directory
        pending_dir = MISSION_STATUS_DIRS["pending"]
        pending_dir.mkdir(parents=True, exist_ok=True)

        mission_data = {
            "id": mission_id,
            "title": request.task[:100] + ("..." if len(request.task) > 100 else ""),
            "mission": request.task,
            "agent_type": agent_type,
            "status": "pending",
            "priority": "medium",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "mode": request.mode,
            "model_id": request.model_id,
            "metadata": {
                "mode": request.mode,
                "model_id": request.model_id,
            },
            "logs": [],
        }

        mission_file = pending_dir / f"{mission_id}.json"
        with open(mission_file, "w") as f:
            json.dump(mission_data, f, indent=2)

        logger.info(f"Created mission {mission_id} with mode={request.mode}")

        # Try to trigger execution via agent manager if available
        execution_status = "pending"
        session_id = None
        response_preview = None

        try:
            # Import agent manager if available
            import sys

            backend_path = Path(__file__).parent.parent
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))

            from routers.agents import get_agent_manager_instance

            manager = get_agent_manager_instance()
            if manager:
                # Execute the mission
                result = manager.ask_agent(agent_type, request.task)
                if result.get("success"):
                    session_id = result.get("session_id")
                    execution_status = "running"
                    response_preview = result.get("response", "")[:200]

                    # Move to running directory
                    running_dir = MISSION_STATUS_DIRS["running"]
                    running_dir.mkdir(parents=True, exist_ok=True)

                    mission_data["status"] = "running"
                    mission_data["started_at"] = datetime.now().isoformat()
                    mission_data["session_id"] = session_id

                    # Update file in running directory
                    running_file = running_dir / f"{mission_id}.json"
                    with open(running_file, "w") as f:
                        json.dump(mission_data, f, indent=2)

                    # Remove from pending
                    mission_file.unlink()

                    logger.info(
                        f"Mission {mission_id} started with session {session_id[:8] if session_id else 'unknown'}"
                    )
                else:
                    logger.warning(
                        f"Mission {mission_id} execution failed: {result.get('error')}"
                    )
                    execution_status = "failed"
        except Exception as e:
            logger.warning(f"Could not trigger execution: {e}")
            # Mission remains pending - can be started manually

        return {
            "status": execution_status,
            "mission_id": mission_id,
            "session_id": session_id,
            "created_at": mission_data["created_at"],
            "mode": request.mode,
            "agent_type": agent_type,
            "execution_time_ms": 0,
            "heuristics_count": 0,
            "response_preview": response_preview,
            "message": f"Mission created with status: {execution_status}",
        }

    except Exception as e:
        logger.error(f"Error creating mission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Mission])
async def list_missions(
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending, running, completed, failed, archive",
    ),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    priority: Optional[str] = Query(
        None, description="Filter by priority: critical, high, medium, low"
    ),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of missions to return"
    ),
    offset: int = Query(0, ge=0, description="Number of missions to skip"),
):
    """List missions with optional filtering."""
    try:
        missions = []

        # Determine which directories to search
        search_dirs = (
            [MISSIONS_DIR]
            if not status
            else [MISSION_STATUS_DIRS.get(status, MISSIONS_DIR)]
        )

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Search in immediate directory and status subdirectories
            for file in search_dir.glob("mission_*.*") + search_dir.glob(
                "*/mission_*.*"
            ):
                # Skip directories
                if file.is_dir():
                    continue

                # Skip archive when filtering other statuses
                if status and file.parent.name != status:
                    # If looking in a parent directory, check the actual parent
                    if file.parent == MISSIONS_DIR and file.parent.name != status:
                        continue

                mission = parse_mission_file(file)
                if not mission:
                    continue

                # Apply filters
                agent_actual = mission.get(
                    "agent_type", mission.get("metadata", {}).get("agent", "")
                ).lower()
                priority_actual = mission.get("priority", "").lower()

                if agent_type and agent_type.lower() not in agent_actual:
                    continue
                if priority and priority.lower() != priority_actual:
                    continue

                # Check if mission is actually running
                if mission.get("status") == "running":
                    mission["is_active"] = check_mission_process(mission["id"])

                missions.append(mission)

        # Sort by created_at (newest first)
        missions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Apply pagination
        total = len(missions)
        missions = missions[offset : offset + limit]

        return [Mission(**mission) for mission in missions]

    except Exception as e:
        logger.error(f"Error listing missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{mission_id}", response_model=Mission)
async def get_mission(mission_id: str):
    """Get a specific mission by ID."""
    try:
        # Search for mission file
        mission_file = None

        # Search in all status directories
        for status_dir in MISSION_STATUS_DIRS.values():
            if not status_dir.exists():
                continue

            # Try exact match
            for ext in [".json", ".md"]:
                candidate = status_dir / f"mission_{mission_id}{ext}"
                if candidate.exists():
                    mission_file = candidate
                    break

            if mission_file:
                break

        # Also search in missions root
        if not mission_file:
            for ext in [".json", ".md"]:
                candidate = MISSIONS_DIR / f"mission_{mission_id}{ext}"
                if candidate.exists():
                    mission_file = candidate
                    break

        if not mission_file:
            raise HTTPException(
                status_code=404, detail=f"Mission {mission_id} not found"
            )

        mission = parse_mission_file(mission_file)
        if not mission:
            raise HTTPException(status_code=500, detail="Failed to parse mission file")

        # Check if mission is actually running
        if mission.get("status") == "running":
            mission["is_active"] = check_mission_process(mission_id)

        return Mission(**mission)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{mission_id}/control")
async def control_mission(mission_id: str, request: MissionControlRequest):
    """Control a mission (start, stop, restart, cancel, retry)."""
    try:
        action = request.action.lower()

        if action == "start":
            logger.info(f"Starting mission: {mission_id}")
            # Note: Actual mission start should be handled by Mission Engine
            # This endpoint updates the status representation
            return {
                "status": "ok",
                "message": f"Mission {mission_id} start requested",
                "action": action,
            }

        elif action == "stop":
            logger.info(f"Stopping mission: {mission_id}")
            # Note: Actual mission stop should be handled by Mission Engine
            return {
                "status": "ok",
                "message": f"Mission {mission_id} stop requested",
                "action": action,
            }

        elif action == "restart":
            logger.info(f"Restarting mission: {mission_id}")
            return {
                "status": "ok",
                "message": f"Mission {mission_id} restart requested",
                "action": action,
            }

        elif action == "cancel":
            logger.info(f"Cancelling mission: {mission_id}")
            return {
                "status": "ok",
                "message": f"Mission {mission_id} cancel requested",
                "action": action,
            }

        elif action == "retry":
            logger.info(f"Retrying failed mission: {mission_id}")
            return {
                "status": "ok",
                "message": f"Mission {mission_id} retry requested",
                "action": action,
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=MissionStats)
async def get_mission_stats():
    """Get mission statistics and summary."""
    try:
        # Get all missions
        all_missions = await list_missions(status=None, limit=1000)

        total = len(all_missions)

        if total == 0:
            return MissionStats(
                total_missions=0,
                success_rate=0.0,
                avg_duration=0.0,
                agent_breakdown={},
                priority_breakdown={},
            )

        # Calculate metrics
        completed = [m for m in all_missions if m.status == "completed"]
        failed = [m for m in all_missions if m.status == "failed"]
        success_rate = len(completed) / total * 100 if total > 0 else 0.0

        # Calculate average duration
        durations = []
        for m in completed:
            if m.started_at and m.completed_at:
                try:
                    start = datetime.fromisoformat(m.started_at)
                    end = datetime.fromisoformat(m.completed_at)
                    duration = (end - start).total_seconds()
                    durations.append(duration)
                except:
                    pass

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Agent breakdown
        agent_breakdown = {}
        for m in all_missions:
            agent = m.agent_type
            agent_breakdown[agent] = agent_breakdown.get(agent, 0) + 1

        # Priority breakdown
        priority_breakdown = {}
        for m in all_missions:
            priority = m.priority
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1

        return MissionStats(
            total_missions=total,
            success_rate=round(success_rate, 2),
            avg_duration=round(avg_duration, 2),
            agent_breakdown=agent_breakdown,
            priority_breakdown=priority_breakdown,
        )

    except Exception as e:
        logger.error(f"Error getting mission stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_missions(limit: int = Query(10, ge=1, le=50)):
    """Get recently modified missions across all statuses."""
    try:
        # This is a simpler version that gets the most recently modified files
        recently_modified = []

        # Search all mission directories
        for status_dir in MISSION_STATUS_DIRS.values():
            if not status_dir.exists():
                continue

            # Get all mission files with modification time
            for file in status_dir.glob("mission_*.*"):
                if file.is_dir():
                    continue

                mission = parse_mission_file(file)
                if mission:
                    mission["modified_at"] = datetime.fromtimestamp(
                        file.stat().st_mtime
                    ).isoformat()
                    recently_modified.append(mission)

        # Sort by modified_at (newest first)
        recently_modified.sort(key=lambda x: x.get("modified_at", ""), reverse=True)

        # Limit results
        recently_modified = recently_modified[:limit]

        return {"missions": recently_modified, "count": len(recently_modified)}

    except Exception as e:
        logger.error(f"Error getting recent missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{mission_id}")
async def delete_mission(
    mission_id: str,
    archive: bool = Query(
        False, description="If True, move to archive instead of deleting"
    ),
):
    """Delete or archive a mission."""
    try:
        # Find mission file
        mission_file = None

        for status_dir in MISSION_STATUS_DIRS.values():
            if not status_dir.exists():
                continue

            for ext in [".json", ".md"]:
                candidate = status_dir / f"mission_{mission_id}{ext}"
                if candidate.exists():
                    mission_file = candidate
                    break

            if mission_file:
                break

        if not mission_file:
            raise HTTPException(
                status_code=404, detail=f"Mission {mission_id} not found"
            )

        if archive:
            # Move to archive directory
            MISSIONS_DIR.mkdir(exist_ok=True)
            archive_dir = MISSIONS_DIR / "archive"
            archive_dir.mkdir(exist_ok=True)

            destination = archive_dir / mission_file.name

            # Handle duplicate filenames
            counter = 1
            while destination.exists():
                stem = mission_file.stem
                ext = mission_file.suffix
                destination = archive_dir / f"{stem}_{counter}{ext}"
                counter += 1

            mission_file.rename(destination)
            logger.info(f"Archived mission {mission_id} to {destination}")
            return {
                "status": "ok",
                "message": f"Mission {mission_id} archived",
                "archived": True,
            }
        else:
            # Delete permanently
            mission_file.unlink()
            logger.info(f"Deleted mission {mission_id}")
            return {
                "status": "ok",
                "message": f"Mission {mission_id} deleted",
                "archived": False,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
