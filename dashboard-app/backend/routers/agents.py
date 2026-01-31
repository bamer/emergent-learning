"""
Agents Router - Dashboard API for Open_ELF Orchestrator

Nouvelle version utilisant l'orchestrateur Open_ELF unifié.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add Open_ELF orchestrator to path
OPEN_ELF_DIR = Path("/home/bamer/.opencode/emergent-learning/Open_ELF")
ORCHESTRATOR_DIR = OPEN_ELF_DIR / "orchestrator"
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

# Import the new orchestrator
try:
    from orchestrator import (
        UnifiedOrchestrator,
        AgentSelector,
        MissionAnalyzer,
        AgentStatus,
        LOGS_DIR,
    )

    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Open_ELF orchestrator: {e}")
    ORCHESTRATOR_AVAILABLE = False

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Global orchestrator instance
_orchestrator: Optional[UnifiedOrchestrator] = None


def get_orchestrator() -> Optional[UnifiedOrchestrator]:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None and ORCHESTRATOR_AVAILABLE:
        _orchestrator = UnifiedOrchestrator()
    return _orchestrator


class MissionRequest(BaseModel):
    """Request to execute a mission."""

    mission: str
    mode: str = "smart"  # smart, auto, swarm, or specific agent
    agent_type: Optional[str] = None  # For manual mode


class AgentResponse(BaseModel):
    """Response from agent execution."""

    status: str
    agent_type: Optional[str]
    mission: str
    response_preview: Optional[str]
    heuristics_count: int
    execution_time_ms: int


@router.get("/status")
async def get_agents_status():
    """
    Get status of all agents and the orchestrator.
    """
    orch = get_orchestrator()

    if not orch:
        return {
            "orchestrator_available": False,
            "message": "Open_ELF orchestrator not available",
            "agents": [],
        }

    try:
        status = orch.get_status()
        return {
            "orchestrator_available": True,
            "orchestrator_running": status.get("running", False),
            "opencode_connected": status.get("opencode_connected", False),
            "agents": list(status.get("agents", {}).values()),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/run")
async def run_mission(request: MissionRequest):
    """
    Execute a mission with the orchestrator.

    Modes:
    - smart: Auto-detect if swarm needed, auto-select agent
    - auto: Auto-select best agent
    - swarm: Force multi-agent parallel execution
    - manual: Use specific agent_type
    """
    orch = get_orchestrator()

    if not orch:
        raise HTTPException(
            status_code=503, detail="Open_ELF orchestrator not available"
        )

    try:
        # Start orchestrator if not running
        if not orch.running:
            orch.start()

        start_time = datetime.now()

        # Execute based on mode
        if request.mode == "smart":
            result = orch.run_smart(request.mission)

            # Check if swarm result or single session
            if isinstance(result, dict) and result.get("mode") == "swarm":
                execution_time = int(
                    (datetime.now() - start_time).total_seconds() * 1000
                )
                return {
                    "status": "completed",
                    "mode": "swarm",
                    "mission": request.mission,
                    "subtasks_completed": result.get("subtasks_completed", 0),
                    "subtasks_total": result.get("plan", {}).get("subtasks_count", 0),
                    "synthesis_preview": result.get("synthesis", {}).get(
                        "response", ""
                    )[:200]
                    if result.get("synthesis")
                    else None,
                    "heuristics_count": result.get("total_heuristics", 0),
                    "execution_time_ms": execution_time,
                }
            else:
                # Single agent result
                session = result
                execution_time = int(
                    (datetime.now() - start_time).total_seconds() * 1000
                )
                return {
                    "status": session.status.value if session else "error",
                    "mode": "single",
                    "agent_type": session.agent_type if session else None,
                    "mission": request.mission,
                    "response_preview": session.response[:300]
                    if session and session.response
                    else None,
                    "heuristics_count": len(session.heuristics) if session else 0,
                    "execution_time_ms": execution_time,
                }

        elif request.mode == "auto":
            session = orch.run_with_auto_select(request.mission)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                "status": session.status.value if session else "error",
                "mode": "auto",
                "agent_type": session.agent_type if session else None,
                "mission": request.mission,
                "response_preview": session.response[:300]
                if session and session.response
                else None,
                "heuristics_count": len(session.heuristics) if session else 0,
                "execution_time_ms": execution_time,
            }

        elif request.mode == "swarm":
            result = orch.execute_swarm_mission(request.mission)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                "status": "completed",
                "mode": "swarm",
                "mission": request.mission,
                "subtasks_completed": result.get("subtasks_completed", 0),
                "subtasks_total": result.get("plan", {}).get("subtasks_count", 0),
                "synthesis_preview": result.get("synthesis", {}).get("response", "")[
                    :200
                ]
                if result.get("synthesis")
                else None,
                "heuristics_count": result.get("total_heuristics", 0),
                "execution_time_ms": execution_time,
            }

        elif request.mode == "manual" and request.agent_type:
            session = orch.run_mission(request.agent_type, request.mission)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                "status": session.status.value if session else "error",
                "mode": "manual",
                "agent_type": request.agent_type,
                "mission": request.mission,
                "response_preview": session.response[:300]
                if session and session.response
                else None,
                "heuristics_count": len(session.heuristics) if session else 0,
                "execution_time_ms": execution_time,
            }

        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/analyze")
async def analyze_mission(request: MissionRequest):
    """
    Analyze a mission without executing it.
    Returns the execution plan (agent selection or swarm decomposition).
    """
    try:
        # Analyze for swarm
        is_swarm = MissionAnalyzer.is_swarm_mission(request.mission)

        if is_swarm:
            plan = MissionAnalyzer.create_swarm_plan(request.mission)
            return {
                "mode": "swarm",
                "detected": True,
                "subtasks_count": plan["subtasks_count"],
                "subtasks": plan["subtasks"],
                "estimated_duration_minutes": plan["estimated_duration"],
            }
        else:
            # Single agent analysis
            selected_agent = AgentSelector.select_agent(request.mission)
            confidence = AgentSelector.get_agent_confidence(
                request.mission, selected_agent
            )

            return {
                "mode": "single",
                "detected": False,
                "selected_agent": selected_agent,
                "confidence": confidence,
                "message": f"Agent '{selected_agent}' selected with {confidence:.0%} confidence",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/logs/{agent_type}")
async def get_agent_logs(agent_type: str, lines: int = 50):
    """
    Get recent logs for an agent.
    """
    try:
        log_file = LOGS_DIR / f"{agent_type}.log"

        if not log_file.exists():
            return {"agent_type": agent_type, "logs": [], "message": "No logs found"}

        with open(log_file, "r") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "agent_type": agent_type,
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")


@router.get("/heuristics")
async def get_heuristics(limit: int = 50):
    """
    Get recently extracted heuristics.
    """
    try:
        heuristics_file = LOGS_DIR / "heuristics.log"

        if not heuristics_file.exists():
            return {"heuristics": [], "count": 0}

        with open(heuristics_file, "r") as f:
            lines = f.readlines()
            recent = lines[-limit:] if len(lines) > limit else lines

        return {"heuristics": [line.strip() for line in recent], "count": len(lines)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read heuristics: {str(e)}"
        )


@router.get("/list")
async def list_agents():
    """
    List all available agents from OpenCode personas.
    """
    agents = []
    opencode_agents_dir = Path.home() / ".config" / "opencode" / "agents"

    if opencode_agents_dir.exists():
        for persona_file in sorted(opencode_agents_dir.glob("*.md")):
            agent_id = persona_file.stem
            # Skip backup/copy files
            if " (Copy)" in agent_id:
                continue

            # Read first line for description if available
            description = f"Agent persona: {agent_id}"
            try:
                content = persona_file.read_text()
                lines = content.strip().split("\n")
                for line in lines[:10]:  # Check first 10 lines
                    line = line.strip()
                    if line and not line.startswith("#") and len(line) > 10:
                        description = line[:100]
                        break
            except:
                pass

            agents.append(
                {
                    "id": agent_id,
                    "name": agent_id.replace("-", " ").replace("_", " ").title(),
                    "description": description,
                    "type": agent_id,
                }
            )

    # Fallback to hardcoded list if no personas found
    if not agents:
        agents = [
            {
                "id": "architect",
                "name": "Architect",
                "description": "System design and architecture",
                "type": "architect",
            },
            {
                "id": "researcher",
                "name": "Researcher",
                "description": "Investigation and analysis",
                "type": "researcher",
            },
            {
                "id": "skeptic",
                "name": "Skeptic",
                "description": "Review and validation",
                "type": "skeptic",
            },
            {
                "id": "creative",
                "name": "Creative",
                "description": "Innovation and ideas",
                "type": "creative",
            },
            {
                "id": "ceo",
                "name": "CEO",
                "description": "Decision making and strategy",
                "type": "ceo",
            },
        ]

    return {"agents": agents}


# OpenCode agents endpoint - returns persona agents from ~/.config/opencode/agents/
@router.get("/opencode/list")
async def list_opencode_agents():
    """List all OpenCode persona agents from ~/.config/opencode/agents/"""
    agents = []
    opencode_agents_dir = Path.home() / ".config" / "opencode" / "agents"

    if opencode_agents_dir.exists():
        for persona_file in sorted(opencode_agents_dir.glob("*.md")):
            agent_id = persona_file.stem
            # Skip backup/copy files
            if " (Copy)" in agent_id:
                continue

            # Read first line for description if available
            description = f"Agent persona: {agent_id}"
            try:
                content = persona_file.read_text()
                lines = content.strip().split("\n")
                for line in lines[:10]:  # Check first 10 lines
                    line = line.strip()
                    if line and not line.startswith("#") and len(line) > 10:
                        description = line[:100]
                        break
            except:
                pass

            agents.append(
                {
                    "id": agent_id,
                    "name": agent_id.replace("-", " ").replace("_", " ").title(),
                    "description": description,
                    "type": agent_id,
                }
            )

    return {"agents": agents}


@router.post("/spawn")
async def spawn_agent_legacy(request: Dict[str, Any]):
    """Legacy: Start an agent. If mission provided, run it. Otherwise just return success."""
    if "agent_type" not in request:
        raise HTTPException(status_code=400, detail="Missing agent_type")

    agent_type = request["agent_type"]

    # If mission is provided, run it
    if "mission" in request.get("params", {}):
        mission_req = MissionRequest(
            mission=request["params"]["mission"],
            mode="manual",
            agent_type=agent_type,
        )
        return await run_mission(mission_req)

    # Otherwise, just return success (agent is ready to receive missions)
    return {
        "status": "ok",
        "agent_type": agent_type,
        "message": f"Agent {agent_type} is ready",
        "note": "Use /run endpoint to execute missions",
    }


@router.post("/kill")
async def kill_agent_legacy(request: Dict[str, Any]):
    """Legacy: Sessions are managed automatically now."""
    return {
        "status": "ok",
        "message": "Session management is now automatic. Agents run on-demand.",
        "note": "This endpoint is kept for backward compatibility",
    }


@router.post("/test")
async def test_agent_legacy(request: Dict[str, Any]):
    """Legacy: Test is now done via analyze endpoint."""
    if "agent_type" in request:
        # Just return a dry-run analysis
        return {
            "status": "ready",
            "dry_run": True,
            "message": f"Agent {request['agent_type']} is ready to execute missions",
            "note": "Use /analyze endpoint for detailed analysis",
        }

    raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/models")
async def list_available_models():
    """
    Fetch available models from OpenCode server.
    Returns models from all configured providers.
    """
    import requests

    try:
        # Fetch from OpenCode server
        response = requests.get("http://localhost:4096/config/providers", timeout=5)
        if response.status_code != 200:
            return {
                "models": [],
                "error": f"Failed to fetch from OpenCode: {response.status_code}",
            }

        data = response.json()
        providers = data.get("providers", [])
        default_models = data.get("default", {})

        # Extract all models from all providers
        all_models = []
        for provider in providers:
            provider_id = provider.get("id", "unknown")
            provider_name = provider.get("name", provider_id)
            models = provider.get("models", {})

            for model_id, model_info in models.items():
                if isinstance(model_info, dict):
                    all_models.append(
                        {
                            "id": model_id,
                            "name": model_info.get("name", model_id),
                            "provider": provider_name,
                            "provider_id": provider_id,
                            "is_default": default_models.get(provider_id) == model_id,
                            "status": model_info.get("status", "unknown"),
                            "capabilities": model_info.get("capabilities", {}),
                        }
                    )

        # Sort: default first, then by provider, then by name
        all_models.sort(key=lambda m: (not m["is_default"], m["provider"], m["name"]))

        return {
            "models": all_models,
            "count": len(all_models),
            "default_provider": list(default_models.keys())[0]
            if default_models
            else None,
        }

    except Exception as e:
        return {"models": [], "error": str(e)}
