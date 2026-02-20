import logging
# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/OPC_ELF/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

"""
Live Router - Real-time SSE endpoints for task watching, trail streaming, and user signals.

Provides Server-Sent Events (SSE) for live dashboard updates.
"""

import asyncio
import json

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.database import get_db, dict_from_row

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("live")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("live")

router = APIRouter(prefix="/api/v1/live", tags=["live"])

# Path to Claude Code tasks directory
TASKS_DIR = Path.home() / ".opencode" / "tasks"
PROJECTS_DIR = Path.home() / ".opencode" / "projects"

# Path to Dashboard missions directory
DASHBOARD_MISSIONS_DIR = (
    Path.home() / ".opencode" / "emergent-learning" / ".coordination" / "missions"
)


def _load_session_names() -> Dict[str, str]:
    """Load session names from all sessions-index.json files."""
    session_names = {}

    if not PROJECTS_DIR.exists():
        return session_names

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        index_file = project_dir / "sessions-index.json"
        if not index_file.exists():
            continue

        try:
            with open(index_file, "r") as f:
                data = json.load(f)
                for entry in data.get("entries", []):
                    session_id = entry.get("sessionId", "")
                    # Prefer summary, fall back to truncated firstPrompt
                    name = entry.get("summary") or entry.get("firstPrompt", "")[:50]
                    if session_id and name:
                        session_names[session_id] = name
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load session index {index_file}: {e}")

    return session_names


class SignalRequest(BaseModel):
    """Request body for adding a note to a task."""

    task_id: str
    session_id: str
    note_text: str


class TaskStatusRequest(BaseModel):
    """Request body for changing task status."""

    status: (
        str  # 'blocked', 'cancelled', 'pending', 'in_progress', 'completed', 'error'
    )
    reason: Optional[str] = None


def _load_tasks_from_dir() -> Dict[str, List[Dict[str, Any]]]:
    """Load all tasks from multiple directories, grouped by session."""
    sessions = {}
    session_names = _load_session_names()

    # Helper function to load tasks from a directory
    def load_tasks_from_directory(task_dir: Path, root_dir: Path):
        local_sessions = {}

        for session_dir in task_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_id = session_dir.name
            # Determine session name
            if task_dir == DASHBOARD_MISSIONS_DIR:
                # Dashboard missions: use session_id as name
                session_name = f"Dashboard: {session_id}"
            else:
                session_name = session_names.get(session_id, session_id[:8] + "...")

            tasks = []

            # Special handling for elf_missions: look for mission_*.json instead of task_*.json
            if session_id == "elf_missions":
                pattern = "mission_*.json"
            else:
                pattern = "*.json"

            for task_file in session_dir.glob(pattern):
                try:
                    with open(task_file, "r") as f:
                        task_data = json.load(f)
                        # Use session_id and session_name from the file if present
                        task_data["session_id"] = task_data.get(
                            "session_id", session_id
                        )
                        task_data["session_name"] = task_data.get(
                            "session_name", session_name
                        )
                        task_data["file_path"] = str(task_file)
                        tasks.append(task_data)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load task file {task_file}: {e}")

            if tasks:
                # Sort by ID (extract numeric part if present)
                def extract_numeric_id(task_id):
                    # Try to extract numeric part from IDs like "architect_m1769888197" or "mission_20260216_011128_5417"
                    # Format: mission_YYYYMMDD_HHMMSS_timestamp or agent_mXXXXX...
                    match = re.search(r"m(\d+)", str(task_id))
                    if match:
                        return int(match.group(1))
                    # Also match timestamps in mission filenames
                    match = re.search(r"(\d{14})", str(task_id))
                    if match:
                        return int(match.group(1))
                    # Fallback to a very large number for non-matching IDs (put them at the end)
                    return 999999999999

                tasks.sort(key=lambda t: extract_numeric_id(t.get("id", "")))
                local_sessions[session_id] = tasks

        return local_sessions

    # Load from TASKS_DIR (elf_missions, sessions, etc.)
    if TASKS_DIR.exists():
        sessions.update(load_tasks_from_directory(TASKS_DIR, TASKS_DIR))

    # Load from DASHBOARD_MISSIONS_DIR (pending, running, completed, failed, archive)
    if DASHBOARD_MISSIONS_DIR.exists():
        # Load missions from all status subdirectories
        for status in ["pending", "running", "completed", "failed", "archive"]:
            status_dir = DASHBOARD_MISSIONS_DIR / status
            if not status_dir.exists():
                continue

            for mission_file in status_dir.glob("mission_*.json"):
                try:
                    with open(mission_file, "r") as f:
                        task_data = json.load(f)

                        # Mission becomes its own "session" with format dashboard_missions_YYYYMMDD_HHMMSS_XXXXXX
                        mission_id = task_data.get("id", mission_file.stem)
                        session_key = f"dashboard_missions_{mission_id}"

                        # Add session_id and session_name to the task
                        task_data["session_id"] = mission_id
                        task_data["session_name"] = (
                            f"Dashboard Mission: {status.title()}"
                        )
                        task_data["file_path"] = str(mission_file)

                        # Normalize field names for frontend compatibility
                        # Dashboard missions use "title", tasks use "subject"
                        if "title" in task_data and "subject" not in task_data:
                            task_data["subject"] = task_data["title"]

                        # Add creation_time and updated_time for consistency
                        if (
                            "created_at" in task_data
                            and "creation_time" not in task_data
                        ):
                            task_data["creation_time"] = task_data["created_at"]
                        if "started_at" in task_data and not task_data.get(
                            "updated_time"
                        ):
                            task_data["updated_time"] = task_data["started_at"]

                        # Add to sessions under this unique key
                        if session_key not in sessions:
                            sessions[session_key] = []
                        sessions[session_key].append(task_data)

                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load mission file {mission_file}: {e}")

    return sessions


def _get_task_file_mtimes() -> Dict[str, float]:
    """Get modification times for all task files across all directories."""
    mtimes = {}

    # Helper function to collect mtimes from a directory
    def collect_mtimes_from_directory(task_dir: Path):
        if not task_dir.exists():
            return

        for session_dir in task_dir.iterdir():
            if not session_dir.is_dir():
                continue

            for task_file in session_dir.glob("*.json"):
                try:
                    mtimes[str(task_file)] = task_file.stat().st_mtime
                except OSError:
                    pass

    # Collect from TASKS_DIR
    collect_mtimes_from_directory(TASKS_DIR)

    # Collect from DASHBOARD_MISSIONS_DIR (pending, running, completed, failed, archive)
    if DASHBOARD_MISSIONS_DIR.exists():
        for status in ["pending", "running", "completed", "failed", "archive"]:
            status_dir = DASHBOARD_MISSIONS_DIR / status
            if status_dir.exists():
                for mission_file in status_dir.glob("mission_*.json"):
                    try:
                        mtimes[str(mission_file)] = mission_file.stat().st_mtime
                    except OSError:
                        pass

    return mtimes


async def _generate_task_events(request: Request):
    """Generator for SSE task updates."""
    last_mtimes: Dict[str, float] = {}
    last_sessions: Dict[str, List[Dict[str, Any]]] = {}

    # Send initial state
    initial_sessions = _load_tasks_from_dir()
    last_sessions = initial_sessions
    last_mtimes = _get_task_file_mtimes()

    yield f"data: {json.dumps({'type': 'initial', 'sessions': initial_sessions})}\n\n"

    while True:
        # Check if client disconnected
        if await request.is_disconnected():
            break

        try:
            # Check for file changes
            current_mtimes = _get_task_file_mtimes()

            # Detect changes
            changed_files = set()
            new_files = set(current_mtimes.keys()) - set(last_mtimes.keys())
            deleted_files = set(last_mtimes.keys()) - set(current_mtimes.keys())

            for path, mtime in current_mtimes.items():
                if path in last_mtimes and mtime != last_mtimes[path]:
                    changed_files.add(path)

            if changed_files or new_files or deleted_files:
                # Reload all tasks and send update
                current_sessions = _load_tasks_from_dir()

                yield f"data: {json.dumps({'type': 'update', 'sessions': current_sessions})}\n\n"

                last_sessions = current_sessions
                last_mtimes = current_mtimes

        except Exception as e:
            logger.error(f"Error in task SSE generator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        await asyncio.sleep(1)  # Poll every 1 second


async def _generate_trail_events(request: Request):
    """Generator for SSE trail updates."""
    last_trail_id = 0

    # Get initial max trail ID
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM trails")
            result = cursor.fetchone()
            if result and result[0]:
                last_trail_id = result[0]
    except Exception as e:
        logger.warning(f"Could not get initial trail ID: {e}")

    # Send initial recent trails
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, location, scent, strength, agent_id, message, created_at
                FROM trails
                ORDER BY created_at DESC
                LIMIT 50
            """)
            initial_trails = [dict_from_row(r) for r in cursor.fetchall()]
            yield f"data: {json.dumps({'type': 'initial', 'trails': initial_trails})}\n\n"
    except Exception as e:
        logger.warning(f"Could not load initial trails: {e}")
        yield f"data: {json.dumps({'type': 'initial', 'trails': []})}\n\n"

    while True:
        if await request.is_disconnected():
            break

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, location, scent, strength, agent_id, message, created_at
                    FROM trails
                    WHERE id > ?
                    ORDER BY created_at ASC
                """,
                    (last_trail_id,),
                )

                new_trails = [dict_from_row(r) for r in cursor.fetchall()]

                if new_trails:
                    last_trail_id = max(t["id"] for t in new_trails)
                    yield f"data: {json.dumps({'type': 'new_trails', 'trails': new_trails})}\n\n"

        except Exception as e:
            logger.error(f"Error in trail SSE generator: {e}")

        await asyncio.sleep(1.5)  # Poll every 1.5 seconds


@router.get("/tasks")
async def stream_tasks(request: Request):
    """
    SSE endpoint for real-time task updates.

    Watches ~/.opencode/tasks/ directory for changes and streams updates.

    Events:
    - initial: Full task state on connection
    - update: Updated task state when files change
    - error: Error occurred during monitoring
    """
    return StreamingResponse(
        _generate_task_events(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/trails")
async def stream_trails(request: Request):
    """
    SSE endpoint for real-time trail updates.

    Polls the trails table for new entries and streams them.

    Events:
    - initial: Recent trails on connection (last 50)
    - new_trails: New trails since last check
    """
    return StreamingResponse(
        _generate_trail_events(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
async def get_active_sessions():
    """
    Get list of active task sessions.

    Returns:
        List of session IDs with task counts
    """
    sessions = _load_tasks_from_dir()

    result = []
    for session_id, tasks in sessions.items():
        # Get session directory mtime as last activity
        session_dir = TASKS_DIR / session_id
        try:
            mtime = session_dir.stat().st_mtime
            last_activity = datetime.fromtimestamp(mtime).isoformat()
        except OSError:
            last_activity = None

        # Count by status
        status_counts = {}
        for task in tasks:
            status = task.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1

        result.append(
            {
                "session_id": session_id,
                "task_count": len(tasks),
                "status_counts": status_counts,
                "last_activity": last_activity,
            }
        )

    # Sort by last activity, most recent first
    result.sort(key=lambda s: s.get("last_activity") or "", reverse=True)

    return result


@router.post("/signal")
async def add_task_signal(signal: SignalRequest):
    """
    Add a note/signal to a task.

    Args:
        signal: SignalRequest with task_id, session_id, and note_text

    Returns:
        {"status": "ok", "task_id": "...", "note_added": "..."}
    """
    task_file = TASKS_DIR / signal.session_id / f"{signal.task_id}.json"

    if not task_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Task {signal.task_id} not found in session {signal.session_id}",
        )

    try:
        # Load existing task
        with open(task_file, "r") as f:
            task_data = json.load(f)

        # Add note
        if "notes" not in task_data:
            task_data["notes"] = []

        note_entry = {
            "text": signal.note_text,
            "timestamp": datetime.now().isoformat(),
            "source": "dashboard",
        }
        task_data["notes"].append(note_entry)

        # Save back
        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(
            f"Added note to task {signal.task_id} in session {signal.session_id}"
        )

        return {
            "status": "ok",
            "task_id": signal.task_id,
            "note_added": signal.note_text,
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid task JSON: {e}")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task file: {e}")


@router.post("/task/{session_id}/{task_id}/start")
async def start_task(session_id: str, task_id: str):
    """Start a stopped/cancelled task."""
    try:
        task_file = TASKS_DIR / session_id / f"{task_id}.json"
        if not task_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Task file not found: {task_id}"
            )

        with open(task_file, "r") as f:
            task_data = json.load(f)

        task_data["status"] = "in_progress"
        task_data["notes"].append(
            {
                "text": f"Task started at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Started task {task_id}")

        # Trigger SSE update
        # Note: Live router will broadcast update automatically

        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        logger.error(f"Error starting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{session_id}/{task_id}/stop")
async def stop_task(session_id: str, task_id: str):
    """Stop a running task."""
    try:
        task_file = TASKS_DIR / session_id / f"{task_id}.json"
        if not task_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Task file not found: {task_id}"
            )

        with open(task_file, "r") as f:
            task_data = json.load(f)

        task_data["status"] = "stopped"
        task_data["notes"].append(
            {
                "text": f"Task stopped at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Stopped task {task_id}")

        # Trigger SSE update
        # Note: Live router will broadcast update automatically

        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        logger.error(f"Error stopping task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{session_id}/{task_id}/relaunch")
async def relaunch_task(session_id: str, task_id: str):
    """Relaunch a completed/cancelled task."""
    try:
        task_file = TASKS_DIR / session_id / f"{task_id}.json"
        if not task_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Task file not found: {task_id}"
            )

        with open(task_file, "r") as f:
            task_data = json.load(f)

        task_data["status"] = "in_progress"
        task_data["notes"].append(
            {
                "text": f"Task relaunched at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Relaunched task {task_id}")

        # Trigger SSE update
        # Note: Live router will broadcast update automatically

        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        logger.error(f"Error relaunching task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{session_id}/{task_id}/status")
async def update_task_status(session_id: str, task_id: str, request: TaskStatusRequest):
    """
    Update a task's status.

    This endpoint now also triggers SSE broadcast for live updates.

    Args:
        session_id: Session UUID
        task_id: Task ID within session
        request: TaskStatusRequest with new status and optional reason

    Returns:
        {"status": "ok", "task_id": "...", "new_status": "..."}
    """
    valid_statuses = {
        "pending",
        "in_progress",
        "completed",
        "blocked",
        "cancelled",
        "error",
    }
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    task_file = TASKS_DIR / session_id / f"{task_id}.json"

    if not task_file.exists():
        raise HTTPException(
            status_code=404, detail=f"Task {task_id} not found in session {session_id}"
        )

    try:
        # Load existing task
        with open(task_file, "r") as f:
            task_data = json.load(f)

        old_status = task_data.get("status", "pending")
        task_data["status"] = request.status

        # Add status change to notes if reason provided
        if request.reason:
            if "notes" not in task_data:
                task_data["notes"] = []
            task_data["notes"].append(
                {
                    "text": f"Status changed from {old_status} to {request.status}: {request.reason}",
                    "timestamp": datetime.now().isoformat(),
                    "source": "dashboard",
                }
            )

        # Save back
        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Updated task {task_id} status to {request.status}")

        return {
            "status": "ok",
            "task_id": task_id,
            "old_status": old_status,
            "new_status": request.status,
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid task JSON: {e}")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task file: {e}")


@router.post("/task/{session_id}/{task_id}/escalate")
async def escalate_task(session_id: str, task_id: str):
    """
    Escalate a blocked task to the orchestrator for analysis.

    This marks the task for orchestrator attention while keeping it in the blocked state.
    The orchestrator will analyze the blocking dependencies and determine next steps.

    Args:
        session_id: Session UUID
        task_id: Task ID within session (must be in 'blocked' state)

    Returns:
        {"status": "ok", "task_id": "...", "escalated": true}
    """
    try:
        task_file = TASKS_DIR / session_id / f"{task_id}.json"
        if not task_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Task file not found: {task_id}"
            )

        with open(task_file, "r") as f:
            task_data = json.load(f)

        # Only blocked tasks can be escalated
        current_status = task_data.get("status")
        if current_status != "blocked":
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} is not blocked (current status: {current_status})",
            )

        # Add escalation note
        if "notes" not in task_data:
            task_data["notes"] = []

        task_data["notes"].append(
            {
                "text": "Task escalated to orchestrator for analysis",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        # Set escalation flag (for future use by orchestrator)
        task_data["escalated"] = True
        task_data["escalated_at"] = datetime.now().isoformat()

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Escalated task {task_id} to orchestrator")

        return {
            "status": "ok",
            "task_id": task_id,
            "escalated": True,
            "escalated_at": task_data["escalated_at"],
        }
    except Exception as e:
        logger.error(f"Error escalating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{session_id}/{task_id}/archive")
async def archive_task(session_id: str, task_id: str):
    """
    Archive a completed/failed/error task from the kanban view.

    This marks the task as archived, hiding it from the main kanban while keeping
    it in storage. The task remains available in the task history.

    Args:
        session_id: Session UUID
        task_id: Task ID within session (must be completed, failed, or error)

    Returns:
        {"status": "ok", "task_id": "...", "archived": true}
    """
    try:
        task_file = TASKS_DIR / session_id / f"{task_id}.json"
        if not task_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Task file not found: {task_id}"
            )

        with open(task_file, "r") as f:
            task_data = json.load(f)

        # Only completed, failed, or error tasks can be archived
        current_status = task_data.get("status")
        valid_statuses = ["completed", "failed", "error", "cancelled"]
        if current_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} cannot be archived (current status: {current_status}. Valid: {valid_statuses})",
            )

        # Mark as archived with timestamp
        if "notes" not in task_data:
            task_data["notes"] = []

        task_data["notes"].append(
            {
                "text": f"Task archived from kanban - original status: {current_status}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        # Set archive flag
        task_data["archived"] = True
        task_data["archived_at"] = datetime.now().isoformat()

        # Store original status before archiving (for reference)
        task_data["archived_from_status"] = current_status

        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"Archived task {task_id} from kanban")

        return {
            "status": "ok",
            "task_id": task_id,
            "archived": True,
            "archived_at": task_data["archived_at"],
            "archived_from_status": task_data["archived_from_status"],
        }
    except Exception as e:
        logger.error(f"Error archiving task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
