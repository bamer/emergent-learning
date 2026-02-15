# =====================================================================
# DO NOT REMOVE THIS COMMENT THE ELF LOGGUER IS FUCKING MANDATORY
# THIS IS MANDATORY: ALL LOGS MUST GO TO
# /home/bamer/.opencode/emergent-learning/Open_ELF/logs/
# ANYONE WHO CHANGES THIS WILL BE EXECUTED WITHOUT PRIOR NOTICE
# =====================================================================

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
import threading
import time
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

from Open_ELF.utils.elf_logging import get_logger, LOGS_DIR

# Import orchestrator components
from unified_orchestrator import UnifiedOrchestrator, AgentType
from orchestrator_state import get_state

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = get_logger("dashboard_agents")

# Global orchestrator instance (singleton)
_orchestrator_instance: Optional[UnifiedOrchestrator] = None
_orchestrator_lock = threading.Lock()
_orchestrator_thread: Optional[threading.Thread] = None


def get_orchestrator() -> UnifiedOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator_instance, _orchestrator_thread

    with _orchestrator_lock:
        if _orchestrator_instance is None:
            logger.info("Initializing global orchestrator instance")
            _orchestrator_instance = UnifiedOrchestrator()

            # Start orchestrator in background thread
            def run_orchestrator():
                try:
                    _orchestrator_instance.start()
                    while _orchestrator_instance.running:
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Orchestrator thread error: {e}")

            _orchestrator_thread = threading.Thread(
                target=run_orchestrator, daemon=True
            )
            _orchestrator_thread.start()

            # Wait for orchestrator to be ready
            timeout = 10
            start_time = time.time()
            while (
                not _orchestrator_instance.running
                and time.time() - start_time < timeout
            ):
                time.sleep(0.5)

            if not _orchestrator_instance.running:
                logger.error("Orchestrator failed to start within timeout")
            else:
                logger.info("Global orchestrator started successfully")

        return _orchestrator_instance


class SpawnRequest(BaseModel):
    """Request to spawn an agent."""

    agent_type: (
        str  # researcher, architect, skeptic, creative (CEO not available for spawning)
    )
    params: Optional[Dict[str, Any]] = None


class KillRequest(BaseModel):
    """Request to kill an agent."""

    agent_type: str
    force: bool = False


class TestRequest(BaseModel):
    """Request to test an agent."""

    agent_type: str
    prompt: Optional[str] = None
    dry_run: bool = False


def _get_orchestrator_status() -> Dict[str, Any]:
    """Get current status from unified orchestrator."""
    try:
        # Try to get from running orchestrator first
        orchestrator = get_orchestrator()
        if orchestrator.running:
            return orchestrator.get_agent_status()
    except Exception as e:
        logger.error(f"Failed to get status from running orchestrator: {e}")

    # Fallback to persisted state
    try:
        state_manager = get_state()
        persisted_state = state_manager.load_state()
        if persisted_state:
            return persisted_state
    except Exception as e:
        logger.error(f"Failed to load persisted state: {e}")

    # Ultimate fallback - return empty status
    return {
        "orchestrator": {"running": False, "start_time": None, "uptime_seconds": 0},
        "agents": [],
        "stats": {
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_crashed": 0,
            "errors_handled": 0,
            "escalations": 0,
            "uptime_seconds": 0,
        },
        "escalations": 0,
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
        request: SpawnRequest with agent_type and optional params (mission)

    Returns:
        {"status": "ok", "agent": "researcher", "message": "Agent spawned successfully", "mission": "..."}
    """
    # CEO is NOT available for spawning - CEO manages the system autonomously
    valid_agents = ["researcher", "architect", "skeptic", "creative"]

    if request.agent_type not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
        )

    try:
        orchestrator = get_orchestrator()
        agent_type = AgentType(request.agent_type)

        if not orchestrator.running:
            raise HTTPException(
                status_code=503,
                detail="Orchestrator is not running. Please start it first.",
            )

        # Log mission if provided
        mission = request.params.get("mission") if request.params else None
        if mission:
            logger.info(
                f"🎯 Agent {request.agent_type} starting with mission: {mission[:100]}..."
            )
            print(
                f"\n🚀 DASHBOARD: Starting agent '{request.agent_type}' with mission:"
            )
            print(f"   Mission: {mission}")
            print(f"   Time: {datetime.now().isoformat()}")
            print(f"   Orchestrator: Active\n")
        else:
            logger.info(
                f"🚀 Agent {request.agent_type} starting without specific mission"
            )
            print(
                f"\n🚀 DASHBOARD: Starting agent '{request.agent_type}' (no mission specified)"
            )
            print(f"   Time: {datetime.now().isoformat()}")
            print(f"   Orchestrator: Active\n")

        success = orchestrator.spawn_agent(agent_type)

        if success:
            logger.info(
                f"✅ Agent {request.agent_type} spawned successfully via dashboard"
            )
            print(
                f"✅ Agent '{request.agent_type}' is now RUNNING on OpenCode server (port 4096)"
            )
            print(f"   Session created and agent is active\n")

            return {
                "status": "ok",
                "agent": request.agent_type,
                "message": f"Agent {request.agent_type} spawned successfully",
                "mission": mission,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error(f"❌ Failed to spawn agent {request.agent_type}")
            print(f"❌ FAILED to start agent '{request.agent_type}'")
            raise HTTPException(
                status_code=500, detail=f"Failed to spawn agent {request.agent_type}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception spawning agent: {e}")
        print(f"❌ EXCEPTION while starting agent '{request.agent_type}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Exception while spawning agent: {str(e)}"
        )

    try:
        orchestrator = get_orchestrator()
        agent_type = AgentType(request.agent_type)

        if not orchestrator.running:
            raise HTTPException(
                status_code=503,
                detail="Orchestrator is not running. Please start it first.",
            )

        success = orchestrator.spawn_agent(agent_type)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception spawning agent: {e}")
        raise HTTPException(
            status_code=500, detail=f"Exception while spawning agent: {str(e)}"
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
        "sentinel",
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

    try:
        orchestrator = get_orchestrator()
        agent_type = AgentType(request.agent_type)

        if not orchestrator.running:
            raise HTTPException(status_code=503, detail="Orchestrator is not running.")

        success = orchestrator.kill_agent(agent_type, request.force)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception killing agent: {e}")
        raise HTTPException(
            status_code=500, detail=f"Exception while stopping agent: {str(e)}"
        )


def _test_agent(
    agent_type: str, prompt: Optional[str] = None, dry_run: bool = False
) -> Dict[str, Any]:
    """Test an agent by spawning and immediately killing it."""
    logger.info(f"Testing agent: {agent_type} (dry_run={dry_run})")

    if dry_run:
        # In dry-run mode, just check if the agent configuration is valid
        valid_agents = [
            "researcher",
            "architect",
            "skeptic",
            "creative",
            "ceo",
            "sentinel",
            "sentinel",
        ]
        if agent_type not in valid_agents:
            return {
                "agent_type": agent_type,
                "status": "failed",
                "dry_run": True,
                "message": f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
            }

        # Check if orchestrator is running
        try:
            orchestrator = get_orchestrator()
            if not orchestrator.running:
                return {
                    "agent_type": agent_type,
                    "status": "warning",
                    "dry_run": True,
                    "message": "Orchestrator is not running. Agent can be started but won't be monitored.",
                }
        except Exception:
            return {
                "agent_type": agent_type,
                "status": "warning",
                "dry_run": True,
                "message": "Orchestrator is not accessible. Agent may not start properly.",
            }

        return {
            "agent_type": agent_type,
            "status": "ready",
            "dry_run": True,
            "message": f"Agent {agent_type} is ready to start. Configuration valid.",
        }

    # Real test - try to spawn and kill
    try:
        orchestrator = get_orchestrator()
        agent_type_enum = AgentType(agent_type)

        # Try to spawn
        spawn_success = orchestrator.spawn_agent(agent_type_enum)
        if not spawn_success:
            return {
                "agent_type": agent_type,
                "status": "failed",
                "spawn": False,
                "kill": None,
                "message": "Failed to spawn agent",
            }

        # Wait a moment
        time.sleep(2)

        # Try to kill
        kill_success = orchestrator.kill_agent(agent_type_enum)

        return {
            "agent_type": agent_type,
            "status": "passed" if kill_success else "partial",
            "spawn": True,
            "kill": kill_success,
            "message": "Agent test completed"
            if kill_success
            else "Spawned but failed to kill cleanly",
        }
    except Exception as e:
        logger.error(f"Exception testing agent: {e}")
        return {
            "agent_type": agent_type,
            "status": "failed",
            "error": str(e),
            "message": f"Test failed with error: {str(e)}",
        }


@router.post("/test")
async def test_agent(request: TestRequest):
    """
    Test an agent by spawning and killing it (or dry-run check).

    Args:
        request: TestRequest with agent_type, optional prompt, and dry_run flag

    Returns:
        Test results with spawn/kill status or dry-run validation
    """
    valid_agents = [
        "researcher",
        "architect",
        "skeptic",
        "creative",
        "ceo",
        "sentinel",
        "sentinel",
    ]

    if request.agent_type not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {', '.join(valid_agents)}",
        )

    result = _test_agent(request.agent_type, request.prompt, request.dry_run)
    logger.info(
        f"Agent {request.agent_type} test completed: {result['status']} (dry_run={request.dry_run})"
    )
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
            "type": "sentinel",
            "name": "Sentinel",
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


# =============================================================================
# Mission/Activity Tracking
# =============================================================================

# Simple in-memory mission log (in production, use a database)
_mission_log: List[Dict[str, Any]] = []


def log_mission(agent_type: str, system: str, mission: Optional[str], status: str):
    """Log a mission/activity to the mission log."""
    global _mission_log
    entry = {
        "id": f"{agent_type}-{datetime.now().timestamp()}",
        "agent_type": agent_type,
        "system": system,
        "mission": mission,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    _mission_log.append(entry)
    # Keep only last 50 missions
    if len(_mission_log) > 50:
        _mission_log = _mission_log[-50:]


@router.get("/missions")
async def get_recent_missions(limit: int = 20):
    """
    Get recent missions/activities.

    Returns:
        List of recent missions with agent, mission text, status, and timestamp
    """
    global _mission_log
    return {
        "missions": _mission_log[-limit:],
        "total": len(_mission_log),
    }


@router.get("/console")
async def get_console_output(lines: int = 50):
    """
    Get recent console output from the backend.

    This is a simplified endpoint that returns status messages.
    In production, you'd use a proper logging aggregation system.

    Returns:
        Recent console messages
    """
    try:
        orchestrator = get_orchestrator()
        status = orchestrator.get_agent_status() if orchestrator.running else None

        messages = []
        if status:
            messages.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "info",
                    "message": f"Orchestrator is running. Uptime: {status.get('orchestrator', {}).get('uptime_seconds', 0)}s",
                }
            )

            for agent in status.get("agents", []):
                if isinstance(agent, dict) and agent.get("status") == "running":
                    messages.append(
                        {
                            "timestamp": agent.get(
                                "start_time", datetime.now().isoformat()
                            ),
                            "level": "success",
                            "message": f"Agent '{agent.get('name', agent.get('type'))}' is active",
                        }
                    )

        return {
            "messages": messages[-lines:],
            "orchestrator_running": orchestrator.running if orchestrator else False,
        }
    except Exception as e:
        return {
            "messages": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "error",
                    "message": str(e),
                }
            ],
            "orchestrator_running": False,
        }
