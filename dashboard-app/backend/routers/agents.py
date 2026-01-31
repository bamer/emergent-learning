"""
Agents Router - Dashboard API for ELF Agent Orchestration

Provides endpoints for:
- Getting agent status
- Spawning agents
- Killing/stopping agents
- Testing agents
- Live SSE updates for agent status

All agents are managed through the unified orchestrator.
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# Add agents directory to path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from elf_logging import get_logger, LOGS_DIR

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = get_logger("dashboard_agents")

# Path to unified orchestrator
UNIFIED_ORCHESTRATOR = AGENTS_DIR / "unified_orchestrator.py"
PYTHON_CMD = "python3"


class SpawnRequest(BaseModel):
    """Request to spawn an agent."""

    agent_type: str  # researcher, architect, skeptic, creative, ceo
    params: Optional[Dict[str, Any]] = None


class KillRequest(BaseModel):
    """Request to kill an agent."""

    agent_type: str
    force: bool = False


class TestRequest(BaseModel):
    """Request to test an agent."""

    agent_type: str


def _get_orchestrator_status() -> Dict[str, Any]:
    """Get current status from unified orchestrator."""
    try:
        result = subprocess.run(
            [PYTHON_CMD, str(UNIFIED_ORCHESTRATOR), "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Filter out log lines that start with timestamps (keep only JSON)
            lines = result.stdout.strip().split("\n")
            json_lines = []
            for line in lines:
                # Skip log lines (they start with dates like "2026-01-31")
                if line.strip() and not line[0:4].isdigit():
                    json_lines.append(line)
            json_str = "\n".join(json_lines)
            return json.loads(json_str)
        else:
            logger.error(f"Failed to get status: {result.stderr}")
            return {"error": "Failed to get status", "details": result.stderr}
    except Exception as e:
        logger.error(f"Exception getting status: {e}")
        return {"error": str(e)}


def _spawn_agent(agent_type: str) -> bool:
    """Spawn an agent using the unified orchestrator."""
    try:
        result = subprocess.run(
            [PYTHON_CMD, str(UNIFIED_ORCHESTRATOR), "spawn", "--agent", agent_type],
            capture_output=True,
            text=True,
            timeout=30,
        )
        success = result.returncode == 0
        if not success:
            logger.error(f"Failed to spawn {agent_type}: {result.stderr}")
        return success
    except Exception as e:
        logger.error(f"Exception spawning {agent_type}: {e}")
        return False


def _kill_agent(agent_type: str, force: bool = False) -> bool:
    """Kill an agent using the unified orchestrator."""
    try:
        cmd = [PYTHON_CMD, str(UNIFIED_ORCHESTRATOR), "kill", "--agent", agent_type]
        if force:
            cmd.append("--force")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        success = result.returncode == 0
        if not success:
            logger.error(f"Failed to kill {agent_type}: {result.stderr}")
        return success
    except Exception as e:
        logger.error(f"Exception killing {agent_type}: {e}")
        return False


def _test_agent(agent_type: str) -> Dict[str, Any]:
    """Test an agent by spawning and immediately killing it."""
    logger.info(f"Testing agent: {agent_type}")

    # Try to spawn
    spawn_success = _spawn_agent(agent_type)
    if not spawn_success:
        return {
            "agent_type": agent_type,
            "status": "failed",
            "spawn": False,
            "kill": None,
            "message": "Failed to spawn agent",
        }

    # Wait a moment
    import time

    time.sleep(2)

    # Try to kill
    kill_success = _kill_agent(agent_type)

    return {
        "agent_type": agent_type,
        "status": "passed" if kill_success else "partial",
        "spawn": True,
        "kill": kill_success,
        "message": "Agent test completed"
        if kill_success
        else "Spawned but failed to kill cleanly",
    }


@router.get("/status")
async def get_agents_status():
    """
    Get status of all agents in the ELF system.

    Returns:
        {
            "orchestrator": {"running": true, "uptime_seconds": 123},
            "agents": [
                {"name": "Sentinel", "status": "running", ...},
                ...
            ]
        }
    """
    status = _get_orchestrator_status()
    if "error" in status:
        raise HTTPException(status_code=500, detail=status["error"])

    # Convert agents object to array for frontend compatibility
    if "agents" in status and isinstance(status["agents"], dict):
        agents_array = []
        for agent_type, agent_data in status["agents"].items():
            agent_data["type"] = agent_type
            agents_array.append(agent_data)
        status["agents"] = agents_array

    return status


@router.post("/spawn")
async def spawn_agent(request: SpawnRequest):
    """
    Spawn a specific agent.

    Args:
        request: SpawnRequest with agent_type

    Returns:
        {"status": "ok", "agent": "researcher", "message": "Agent spawned successfully"}
    """
    valid_agents = ["researcher", "architect", "skeptic", "creative", "ceo"]

    if request.agent_type not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
        )

    success = _spawn_agent(request.agent_type)

    if success:
        logger.info(f"Agent {request.agent_type} spawned via dashboard")
        return {
            "status": "ok",
            "agent": request.agent_type,
            "message": f"Agent {request.agent_type} spawned successfully",
        }
    else:
        raise HTTPException(
            status_code=500, detail=f"Failed to spawn agent {request.agent_type}"
        )


@router.post("/kill")
async def kill_agent(request: KillRequest):
    """
    Kill/stop a specific agent.

    Args:
        request: KillRequest with agent_type and optional force flag

    Returns:
        {"status": "ok", "agent": "researcher", "message": "Agent stopped successfully"}
    """
    valid_agents = [
        "sentinel",
        "watcher",
        "researcher",
        "architect",
        "skeptic",
        "creative",
        "ceo",
    ]

    if request.agent_type not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
        )

    success = _kill_agent(request.agent_type, request.force)

    if success:
        logger.info(
            f"Agent {request.agent_type} killed via dashboard (force={request.force})"
        )
        return {
            "status": "ok",
            "agent": request.agent_type,
            "force": request.force,
            "message": f"Agent {request.agent_type} stopped successfully",
        }
    else:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop agent {request.agent_type}"
        )


@router.post("/test")
async def test_agent(request: TestRequest):
    """
    Test an agent by spawning and killing it.

    Args:
        request: TestRequest with agent_type

    Returns:
        Test results with spawn/kill status
    """
    valid_agents = ["researcher", "architect", "skeptic", "creative", "ceo"]

    if request.agent_type not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
        )

    result = _test_agent(request.agent_type)
    logger.info(f"Agent {request.agent_type} test completed: {result['status']}")
    return result


@router.get("/logs/{agent_name}")
async def get_agent_logs(agent_name: str, lines: int = 100):
    """
    Get recent log entries for an agent.

    Args:
        agent_name: Name of the agent (e.g., "unified_orchestrator", "sentinel")
        lines: Number of lines to return (default: 100)

    Returns:
        {"agent": "sentinel", "logs": ["line1", "line2", ...]}
    """
    log_file = LOGS_DIR / f"{agent_name}.log"

    if not log_file.exists():
        raise HTTPException(
            status_code=404, detail=f"No logs found for agent: {agent_name}"
        )

    try:
        # Read last N lines
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "agent": agent_name,
            "log_file": str(log_file),
            "lines_returned": len(recent_lines),
            "logs": [line.strip() for line in recent_lines],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")


@router.get("/list")
async def list_available_agents():
    """
    List all available agent types with their descriptions.

    Returns:
        List of agent definitions
    """
    agents = [
        {
            "type": "orchestrator",
            "name": "Orchestrateur Unifié",
            "description": "Coordination centrale de tous les agents",
            "icon": "🎯",
            "auto_start": True,
            "can_spawn": False,
        },
        {
            "type": "sentinel",
            "name": "Sentinel",
            "description": "Surveillance continue et détection de patterns",
            "icon": "🔍",
            "auto_start": True,
            "can_spawn": False,
        },
        {
            "type": "watcher",
            "name": "Watcher",
            "description": "Vérifications périodiques et interventions",
            "icon": "👁️",
            "auto_start": True,
            "can_spawn": False,
        },
        {
            "type": "researcher",
            "name": "Researcher",
            "description": "Investigation approfondie et collecte d'evidence",
            "icon": "🔬",
            "auto_start": False,
            "can_spawn": True,
        },
        {
            "type": "architect",
            "name": "Architect",
            "description": "Conception système et planification structure",
            "icon": "🏗️",
            "auto_start": False,
            "can_spawn": True,
        },
        {
            "type": "skeptic",
            "name": "Skeptic",
            "description": "Analyse critique et identification des risques",
            "icon": "❓",
            "auto_start": False,
            "can_spawn": True,
        },
        {
            "type": "creative",
            "name": "Creative",
            "description": "Innovation et génération de solutions",
            "icon": "💡",
            "auto_start": False,
            "can_spawn": True,
        },
        {
            "type": "ceo",
            "name": "CEO",
            "description": "Décisions exécutives et direction stratégique",
            "icon": "👑",
            "auto_start": False,
            "can_spawn": True,
        },
    ]

    return {"agents": agents}


async def _generate_agent_events(request: Request):
    """Generator for SSE agent status updates."""
    last_status = None

    while True:
        # Check if client disconnected
        if await request.is_disconnected():
            break

        try:
            # Get current status
            current_status = _get_orchestrator_status()

            # Only send if changed
            if current_status != last_status:
                yield f"data: {json.dumps({'type': 'update', 'status': current_status})}\n\n"
                last_status = current_status

        except Exception as e:
            logger.error(f"Error in agent SSE generator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        await asyncio.sleep(5)  # Poll every 5 seconds


@router.get("/stream")
async def stream_agents(request: Request):
    """
    SSE endpoint for real-time agent status updates.

    Streams agent status changes every 5 seconds.
    """
    return StreamingResponse(
        _generate_agent_events(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# OpenCode Swarm Endpoints
# =============================================================================


class SwarmRequest(BaseModel):
    """Request to run an OpenCode swarm."""

    task: str
    mode: str = "all"  # analysis, design, implementation, learning, all
    context: str = ""
    custom_agents: Optional[List[str]] = None


@router.get("/opencode/list")
async def list_opencode_agents():
    """
    List all available OpenCode agents (prompt-based personas).

    Returns:
        List of OpenCode agents with their descriptions
    """
    try:
        import sys

        sys.path.insert(0, str(AGENTS_DIR))
        from opencode_swarm import OpenCodeSwarmManager, OPENCODE_AGENTS_DIR

        manager = OpenCodeSwarmManager()
        agents = manager.get_available_agents()

        return {
            "agents": agents,
            "count": len(agents),
            "source": str(OPENCODE_AGENTS_DIR),
        }
    except Exception as e:
        logger.error(f"Error listing OpenCode agents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list OpenCode agents: {str(e)}"
        )


@router.post("/opencode/swarm")
async def run_opencode_swarm(request: SwarmRequest):
    """
    Run an OpenCode agent swarm for a task.

    Args:
        request: SwarmRequest with task, mode, and optional context

    Returns:
        Swarm execution results
    """
    try:
        import sys

        sys.path.insert(0, str(AGENTS_DIR))
        from opencode_swarm import OpenCodeSwarmManager, SwarmMode

        manager = OpenCodeSwarmManager()

        # Convert mode string to enum
        try:
            mode = SwarmMode(request.mode)
        except ValueError:
            mode = SwarmMode.ALL

        result = manager.run_swarm(
            task=request.task,
            context=request.context,
            mode=mode,
            custom_agents=request.custom_agents,
        )

        logger.info(
            f"OpenCode swarm executed: {result['status']} with {result.get('agent_count', 0)} agents"
        )
        return result
    except Exception as e:
        logger.error(f"Error running OpenCode swarm: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run swarm: {str(e)}")


@router.get("/opencode/modes")
async def list_swarm_modes():
    """
    List available swarm modes and their agent sequences.

    Returns:
        Dictionary of modes with their agent sequences
    """
    try:
        import sys

        sys.path.insert(0, str(AGENTS_DIR))
        from opencode_swarm import SWARM_SEQUENCES, SwarmMode

        modes = {}
        for mode in SwarmMode:
            if mode != SwarmMode.ALL:
                modes[mode.value] = {
                    "agents": SWARM_SEQUENCES[mode],
                    "description": _get_mode_description(mode),
                }

        modes["all"] = {
            "agents": SWARM_SEQUENCES[SwarmMode.ALL],
            "description": "Use all available agents",
        }

        return {"modes": modes}
    except Exception as e:
        logger.error(f"Error listing swarm modes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list modes: {str(e)}")


def _get_mode_description(mode: "SwarmMode") -> str:
    """Get human-readable description for a swarm mode."""
    descriptions = {
        "analysis": "Deep investigation and evidence gathering",
        "design": "System design with innovation and critical review",
        "implementation": "Build with research and risk analysis",
        "learning": "Extract insights and patterns from work",
    }
    return descriptions.get(mode.value, "Custom agent sequence")
