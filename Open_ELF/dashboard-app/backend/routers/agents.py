"""
Agents Router - Dashboard API (Simplified Version)

Version simplifiée sans dépendance à l'orchestrateur Python.
Utilise directement l'API OpenCode.
"""

import json
import requests
import time
import threading
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import EventBridge and UnifiedOrchestrator (REQUIRED - will fail if not available)
openelf_dir = Path(__file__).parent.parent.parent.parent
if str(openelf_dir) not in sys.path:
    sys.path.insert(0, str(openelf_dir))

from orchestrator.unified_orchestrator import get_orchestrator
from agents.agent_manager import get_agent_manager

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import (
        get_logger,
        log_critical,
        log_error,
        log_warning,
        log_info,
    )

    logger = get_logger("agents")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("agents")

HAS_ORCHESTRATOR = True


def get_agent_manager_instance():
    """Get AgentManager singleton. Fails gracefully if not available."""
    try:
        return get_agent_manager()
    except Exception as e:
        logger.warning(f"AgentManager not available: {e}")
        return None


router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

OPENCODE_SERVER = "http://localhost:4096"
TASKS_DIR = Path.home() / ".opencode" / "tasks"

# Valid OpenCode agent types
VALID_AGENT_TYPES = {
    "architect",
    "atlas",
    "build",
    "ceo",
    "coder",
    "coder-agent",
    "compaction",
    "creative",
    "explore",
    "general",
    "janitor-agent",
    "learning-extractor",
    "librarian",
    "metis",
    "momus",
    "multi-agent-coordinator",
    "multimodal-looker",
    "oracle",
    "orchestrator",
    "plan",
    "prometheus",
    "researcher",
    "reviewer",
    "scribe",
    "sentinel",
    "sentinel-agent",
    "sisyphus",
    "sisyphus-junior",
    "skeptic",
    "summary",
    "swarm-orchestrator",
    "title",
    "unified-orchestrator",
    "watcher",
}


def is_valid_agent_type(agent_type: str) -> bool:
    """Check if the agent type is valid."""
    return agent_type in VALID_AGENT_TYPES


def extract_heuristics(text: str) -> List[Dict[str, str]]:
    """Extract learning patterns from agent response text.

    Detects both:
    1. Explicit [LEARNED:domain] markers
    2. Implicit patterns with heuristic keywords (always, never, should, must, etc.)
    """
    heuristics = []

    # First: Extract explicit [LEARNED:] markers
    pattern_explicit = (
        r"\[LEARNED:([^\]]+)\](.*?)(?=\[LEARNED:|\[LEARNING:|\[LEARN:|\Z)"
    )
    matches_explicit = re.findall(pattern_explicit, text, re.DOTALL | re.IGNORECASE)

    for domain, lesson in matches_explicit:
        lesson_clean = lesson.strip()
        if lesson_clean and len(lesson_clean) > 10:
            is_heuristic = any(
                word in lesson_clean.lower()
                for word in [
                    "always",
                    "never",
                    "should",
                    "must",
                    "avoid",
                    "prefer",
                    "don't",
                    "never",
                ]
            )

            heuristics.append(
                {
                    "domain": domain.strip().lower(),
                    "text": lesson_clean,
                    "type": "heuristic" if is_heuristic else "observation",
                    "confidence": 0.6 if is_heuristic else 0.4,
                    "extracted_at": datetime.now().isoformat(),
                    "source": "explicit_marker",
                }
            )

    # Second: Extract implicit patterns (sentences with heuristic keywords)
    # Look for sentences containing learning indicators
    sentences = re.split(r"[.!?\n]+", text)
    heuristic_keywords = [
        "always",
        "never",
        "should",
        "must",
        "avoid",
        "prefer",
        "don't",
        "need to",
        "important to",
    ]

    for sentence in sentences:
        sentence_clean = sentence.strip()
        # Skip if too short, already captured, or not a learning statement
        if len(sentence_clean) < 20 or len(sentence_clean) > 300:
            continue

        # Check if contains heuristic keywords
        has_keyword = any(
            keyword in sentence_clean.lower() for keyword in heuristic_keywords
        )

        # Check if it's a learning statement (advice, pattern, best practice)
        learning_indicators = [
            "use ",
            "should ",
            "must ",
            "avoid ",
            "prefer ",
            "recommend",
            "best practice",
            "pattern",
            "approach",
        ]
        is_learning = any(
            indicator in sentence_clean.lower() for indicator in learning_indicators
        )

        if has_keyword and is_learning:
            # Extract domain from context (first word or default to "general")
            words = sentence_clean.split()[:3]
            potential_domain = words[0].lower() if words else "general"

            # Skip if already captured by explicit marker
            already_captured = any(
                h["text"].startswith(sentence_clean[:50]) for h in heuristics
            )
            if not already_captured:
                is_heuristic = any(
                    word in sentence_clean.lower()
                    for word in ["always", "never", "should", "must", "avoid", "prefer"]
                )

                heuristics.append(
                    {
                        "domain": potential_domain,
                        "text": sentence_clean,
                        "type": "heuristic" if is_heuristic else "observation",
                        "confidence": 0.4 if is_heuristic else 0.3,
                        "extracted_at": datetime.now().isoformat(),
                        "source": "implicit_detection",
                    }
                )

    return heuristics


def record_heuristic_to_building(heuristic: Dict[str, str], task_id: str) -> bool:
    """Record a heuristic to the ELF building knowledge base."""
    try:
        # Use the record-heuristic.py script
        script_path = (
            Path.home()
            / ".opencode"
            / "emergent-learning"
            / "scripts"
            / "record-heuristic.py"
        )

        if script_path.exists():
            result = subprocess.run(
                [
                    "python",
                    str(script_path),
                    "--domain",
                    heuristic["domain"],
                    "--rule",
                    heuristic["text"],
                    "--confidence",
                    str(heuristic["confidence"]),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info(
                    f"✅ Heuristic recorded: [{heuristic['domain']}] {heuristic['text'][:50]}..."
                )
                return True
            else:
                logger.warning(f"Failed to record heuristic: {result.stderr}")
        else:
            logger.warning(f"record-heuristic.py not found at {script_path}")

    except Exception as e:
        logger.error(f"Error recording heuristic: {e}")

    return False


def create_task(
    mission_text: str,
    agent_type: str,
    session_id: str,
    agent_name: Optional[str] = None,
) -> tuple[str, Path]:
    """Create a task file for the dashboard to monitor."""
    # Create session directory
    session_name = f"elf_{datetime.now().strftime('%Y%m%d')}"
    session_dir = TASKS_DIR / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    # Normalize agent_type - "unknown" should be "auto"
    display_agent = agent_type if agent_type and agent_type != "unknown" else "auto"

    # Use agent_name for display if provided, otherwise the agent_type
    display_name = agent_name if agent_name else display_agent

    # Generate task ID (always use agent_type for filtering)
    timestamp = int(time.time())
    task_id = f"{display_agent}_m{timestamp}"
    task_file = session_dir / f"{task_id}.json"

    # Create task data
    task_data = {
        "id": task_id,
        "subject": f"[{display_name}] {mission_text[:80]}{'...' if len(mission_text) > 80 else ''}",
        "description": mission_text,
        "status": "in_progress",
        "session_id": session_name,
        "session_name": f"ELF Dashboard {datetime.now().strftime('%Y-%m-%d')}",
        "notes": [
            {
                "text": f"Mission started at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        ],
    }

    # Write task file
    with open(task_file, "w") as f:
        json.dump(task_data, f, indent=2)

    logger.info(f"📝 Task created: {task_file.name}")
    return task_id, task_file


def update_task_status(
    task_file: Path, status: str, response_text: Optional[str] = None
):
    """Update task status and add response if provided."""
    if not task_file.exists():
        return

    try:
        # Read existing task data
        with open(task_file, "r") as f:
            task_data = json.load(f)

        # Update status
        task_data["status"] = status

        # Add response note if provided
        if response_text:
            task_data["notes"].append(
                {
                    "text": f"Response: {response_text[:500]}{'...' if len(response_text) > 500 else ''}",
                    "timestamp": datetime.now().isoformat(),
                    "source": "agent",
                }
            )

        # Add completion note
        task_data["notes"].append(
            {
                "text": f"Mission completed at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat(),
                "source": "dashboard",
            }
        )

        # Write updated task data
        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)

        logger.info(f"📝 Task updated: {task_file.name} -> {status}")
    except Exception as e:
        logger.error(f"Failed to update task {task_file}: {e}")


def wait_for_response(session_id: str, timeout: int = 120) -> Optional[str]:
    """Wait for response from OpenCode session by polling."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{OPENCODE_SERVER}/session/{session_id}/message", timeout=10
            )

            if response.status_code == 200:
                messages = response.json()

                # Look for the last assistant message with content
                for msg in reversed(messages):
                    if msg.get("info", {}).get("role") == "assistant":
                        parts = msg.get("parts", [])
                        text_parts = [
                            p
                            for p in parts
                            if p.get("type") == "text" and p.get("text")
                        ]

                        if text_parts:
                            return "\n".join([p.get("text", "") for p in text_parts])

        except Exception as e:
            logger.warning(f"Error polling session {session_id}: {e}")

        time.sleep(2)

    return None


def call_learning_extractor(
    agent_response: str, task_context: str
) -> List[Dict[str, Any]]:
    """Call learning-extractor agent to analyze response and extract learnings."""
    try:
        manager = get_agent_manager_instance()
        if not manager:
            logger.warning("AgentManager not available for learning-extractor")
            return []

        # Build the extraction prompt
        extraction_prompt = f"""Analyze this agent response and extract any valuable learnings, patterns, or insights that should be saved to the knowledge base.

Task Context: {task_context}

Agent Response:
---
{agent_response[:2000]}
---

For each significant learning you identify:
1. Determine if it's truly valuable and reusable (not trivial or one-time specific)
2. Assign it to the most relevant domain (e.g., 'react', 'api', 'testing', 'architecture')
3. Decide if it's a HEURISTIC (contains advice like "always", "never", "should", "must") or an OBSERVATION (factual insight)
4. Format it as: [LEARNED:domain] Your insight here

Only include learnings that are:
- Actionable and reusable
- Not obvious or trivial
- Worth remembering for future similar tasks

Return your extractions in [LEARNED:] format. If no valuable learnings found, return empty."""

        # Use AgentManager to query learning-extractor agent
        result = manager.ask_agent("learning-extractor", extraction_prompt)

        if not result.get("success"):
            logger.warning(
                f"Failed to get learning-extractor response: {result.get('error')}"
            )
            return []

        extraction_response = result.get("response", "")

        # Extract heuristics from learning-extractor response
        heuristics = extract_heuristics(extraction_response)

        logger.info(f"🧠 Learning-extractor found {len(heuristics)} learnings")
        return heuristics

    except Exception as e:
        logger.error(f"Error calling learning-extractor: {e}")
        return []


def monitor_mission(
    session_id: str, task_file: Path, agent_type: str, mission_text: str
):
    """Background function to monitor mission execution and update task status."""
    try:
        response_text = wait_for_response(session_id, timeout=120)

        if response_text:
            update_task_status(task_file, "completed", response_text)

            # Call learning-extractor to analyze and extract learnings
            heuristics = call_learning_extractor(
                agent_response=response_text, task_context=mission_text[:200]
            )

            if heuristics:
                logger.info(
                    f"🧠 Recording {len(heuristics)} learnings from learning-extractor"
                )

                for heuristic in heuristics:
                    record_heuristic_to_building(heuristic, task_file.stem)

                try:
                    with open(task_file, "r") as f:
                        task_data = json.load(f)

                    task_data["heuristics"] = heuristics
                    task_data["heuristics_count"] = len(heuristics)

                    with open(task_file, "w") as f:
                        json.dump(task_data, f, indent=2)

                    logger.info(f"✅ Task updated with {len(heuristics)} learnings")
                except Exception as e:
                    logger.error(f"Failed to update task with learnings: {e}")
            else:
                logger.info("📝 No valuable learnings extracted by learning-extractor")

            logger.info(f"✅ Mission completed for session {session_id}")
        else:
            update_task_status(task_file, "error", "No response received from agent")
            logger.error(f"❌ No response from agent for session {session_id}")

    except Exception as e:
        update_task_status(task_file, "error", f"Error monitoring mission: {str(e)}")
        logger.error(f"❌ Error monitoring mission for session {session_id}: {e}")


class MissionRequest(BaseModel):
    """Request to execute a mission."""

    mission: str
    mode: str = "smart"
    agent_type: Optional[str] = None


class SwarmRequest(BaseModel):
    """Request to run a swarm mission."""

    task: str
    mode: str = "all"  # analysis, design, implementation, learning, all
    context: str = ""
    custom_agents: Optional[List[str]] = None


@router.get("/status")
async def get_agents_status():
    """Get status of all agents."""
    try:
        # Get available agents from OpenCode
        response = requests.get(f"{OPENCODE_SERVER}/agent", timeout=5)
        if response.status_code == 200:
            agents_data = response.json()
            agents = []
            for agent in agents_data:
                agents.append(
                    {
                        "agent_type": agent.get("id", "unknown"),
                        "name": agent.get("name", "Unknown"),
                        "status": "ready",
                        "display_name": agent.get("name", "Unknown"),
                        "description": agent.get("description", ""),
                    }
                )
            return {
                "timestamp": datetime.now().isoformat(),
                "orchestrator": {"running": True, "uptime_seconds": 0},
                "agents": agents,
            }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": {"running": False, "uptime_seconds": 0},
            "agents": [],
            "error": str(e),
        }


@router.get("/list")
async def list_agents():
    """List all available agents."""
    try:
        response = requests.get(f"{OPENCODE_SERVER}/agent", timeout=5)
        if response.status_code == 200:
            agents_data = response.json()
            agents = []
            for agent in agents_data:
                agents.append(
                    {
                        "id": agent.get("id"),
                        "name": agent.get("name"),
                        "display_name": agent.get("name"),
                        "description": agent.get("description", ""),
                        "type": agent.get("id"),
                    }
                )
            return {"agents": agents}
    except Exception as e:
        return {"agents": [], "error": str(e)}


@router.get("/opencode/list")
async def list_opencode_agents():
    """List OpenCode agents."""
    return await list_agents()


@router.get("/models")
async def list_available_models():
    """Fetch available models from OpenCode server."""
    try:
        response = requests.get(f"{OPENCODE_SERVER}/config/providers", timeout=5)
        if response.status_code != 200:
            return {"models": [], "error": f"Failed to fetch: {response.status_code}"}

        data = response.json()
        providers = data.get("providers", [])
        default_models = data.get("default", {})

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
                        }
                    )

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


@router.post("/run")
async def run_mission(request: MissionRequest):
    """Execute a mission."""
    try:
        manager = get_agent_manager_instance()
        if not manager:
            return {
                "status": "error",
                "message": "AgentManager not available. Start OpenCode server.",
                "mode": request.mode,
                "mission": request.mission,
            }

        agent_type = request.agent_type or "auto"
        agent = (
            agent_type
            if agent_type != "auto" and is_valid_agent_type(agent_type)
            else None
        )

        logger.info(f"🤖 Executing mission via AgentManager: {request.mission[:50]}...")

        # Use AgentManager to query the agent
        if agent:
            result = manager.ask_agent(agent, request.mission)
        else:
            # Use auto agent or a general-purpose agent
            result = manager.ask_agent("general", request.mission)

        if not result.get("success"):
            logger.error(f"Failed to execute mission: {result.get('error')}")
            return {
                "status": "error",
                "message": result.get("error", "Unknown error"),
                "mode": request.mode,
                "agent_type": agent_type,
                "mission": request.mission,
            }

        session_id = result.get("session_id", "unknown")
        logger.info(f"✅ Mission started with session {session_id[:8]}...")

        # Create task file
        task_id, task_file = create_task(request.mission, agent_type, session_id)

        # Start background monitoring
        monitor_thread = threading.Thread(
            target=monitor_mission,
            args=(session_id, task_file, agent_type, request.mission),
            daemon=True,
        )
        monitor_thread.start()

        response_text = result.get("response", "")

        return {
            "status": "started",
            "mode": request.mode,
            "agent_type": agent_type,
            "mission": request.mission,
            "session_id": session_id,
            "task_id": task_id,
            "message_sent": True,
            "heuristics_count": 0,
            "execution_time_ms": 0,
            "response_preview": response_text[:200] if response_text else "",
        }
    except Exception as e:
        logger.error(f"Exception in run_mission: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "mode": request.mode,
            "mission": request.mission,
        }


# =============================================================================
# NEW ASYNC MISSION SYSTEM WITH SPAWN_AGENT
# =============================================================================

# Import mission store
sys.path.insert(0, str(Path(__file__).parent.parent))
from mission_store import get_mission_store, Mission


def auto_select_agent(mission_text: str, manager) -> str:
    """Automatically select the best agent based on mission content."""
    text_lower = mission_text.lower()

    # Code-related missions
    if any(
        kw in text_lower
        for kw in ["code", "refactor", "debug", "fix", "analyze code", "review"]
    ):
        return "architect"

    # Research and investigation
    if any(
        kw in text_lower
        for kw in ["research", "investigate", "find", "search", "explore"]
    ):
        return "researcher"

    # Design and creativity
    if any(kw in text_lower for kw in ["design", "create", "build", "implement"]):
        return "creative"

    # Analysis and validation
    if any(kw in text_lower for kw in ["analyze", "check", "validate", "verify"]):
        return "skeptic"

    # System and orchestration
    if any(
        kw in text_lower for kw in ["system", "orchestrate", "coordinate", "monitor"]
    ):
        return "unified-orchestrator"

    # Learning and extraction
    if any(kw in text_lower for kw in ["learn", "extract", "heuristic"]):
        return "learning-extractor"

    # Default to researcher for general tasks
    return "researcher"


class CreateMissionRequest(BaseModel):
    """Request to create a new mission."""

    agent_type: str
    mission_text: str
    model: Optional[str] = None


class ExecuteMissionRequest(BaseModel):
    """Request to execute a mission."""

    pass


@router.post("/missions")
async def create_mission(request: CreateMissionRequest):
    """Create a new pending mission."""
    try:
        store = get_mission_store()
        mission = store.create_mission(
            agent_type=request.agent_type, mission_text=request.mission_text
        )

        return {
            "status": "created",
            "mission_id": mission.id,
            "agent_type": mission.agent_type,
            "mission_text": mission.mission_text[:100] + "..."
            if len(mission.mission_text) > 100
            else mission.mission_text,
            "created_at": mission.created_at,
        }
    except Exception as e:
        logger.error(f"Failed to create mission: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create mission: {str(e)}"
        )


@router.get("/missions")
async def list_missions(status: Optional[str] = None):
    """List all missions, optionally filtered by status."""
    try:
        store = get_mission_store()
        missions = store.list_missions(status)

        return {
            "missions": [
                {
                    "id": m.id,
                    "status": m.status,
                    "agent_type": m.agent_type,
                    "mission_text": m.mission_text[:100] + "..."
                    if len(m.mission_text) > 100
                    else m.mission_text,
                    "created_at": m.created_at,
                    "started_at": m.started_at,
                    "completed_at": m.completed_at,
                    "duration_seconds": m.duration_seconds,
                }
                for m in missions
            ],
            "count": len(missions),
        }
    except Exception as e:
        logger.error(f"Failed to list missions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list missions: {str(e)}"
        )


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str):
    """Get mission details."""
    try:
        store = get_mission_store()
        mission = store.get_mission(mission_id)

        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        return {
            "id": mission.id,
            "status": mission.status,
            "agent_type": mission.agent_type,
            "mission_text": mission.mission_text,
            "result": mission.result,
            "error": mission.error,
            "session_id": mission.session_id,
            "created_at": mission.created_at,
            "started_at": mission.started_at,
            "completed_at": mission.completed_at,
            "duration_seconds": mission.duration_seconds,
            "heuristics": mission.heuristics,
            "logs": mission.logs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get mission: {str(e)}")


@router.post("/missions/{mission_id}/execute")
async def execute_mission(mission_id: str):
    """Execute a mission using spawn_agent (async, long-running)."""
    try:
        store = get_mission_store()
        mission = store.get_mission(mission_id)

        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Mission is not pending (status: {mission.status})",
            )

        manager = get_agent_manager_instance()
        if not manager:
            raise HTTPException(status_code=503, detail="AgentManager not available")

        # Use spawn_agent for async long-running missions
        logger.info(f"🚀 Spawning agent for mission {mission_id}...")

        try:
            # Determine agent to use
            agent_name = mission.agent_type
            if agent_name == "auto" or agent_name not in manager.agents:
                # Auto-select best agent based on mission content
                agent_name = auto_select_agent(mission.mission_text, manager)
                logger.info(f"🎯 Auto-selected agent: {agent_name}")

            # Spawn agent asynchronously
            result = manager.spawn_agent(
                agent_name=agent_name,
                mission=mission.mission_text,
            )

            if not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                store.fail_mission(mission_id, error_msg)
                raise HTTPException(
                    status_code=500, detail=f"Failed to spawn agent: {error_msg}"
                )

            session_id = result.get("session_id")
            if not session_id:
                store.fail_mission(mission_id, "No session ID returned")
                raise HTTPException(
                    status_code=500, detail="No session ID returned from spawn_agent"
                )

            # Update mission status to running
            store.start_mission(mission_id, session_id)

            # Start background monitoring thread
            monitor_thread = threading.Thread(
                target=monitor_mission_async,
                args=(mission_id, session_id, manager),
                daemon=True,
            )
            monitor_thread.start()

            return {
                "status": "started",
                "mission_id": mission_id,
                "session_id": session_id,
                "message": "Mission execution started. Use /missions/{mission_id}/status to poll.",
            }

        except Exception as spawn_error:
            logger.error(
                f"Failed to spawn agent for mission {mission_id}: {spawn_error}"
            )
            store.fail_mission(mission_id, str(spawn_error))
            raise HTTPException(
                status_code=500, detail=f"Failed to spawn agent: {str(spawn_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute mission: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to execute mission: {str(e)}"
        )


def monitor_mission_async(mission_id: str, session_id: str, manager):
    """Background thread to monitor async mission execution."""
    try:
        store = get_mission_store()
        logger.info(
            f"👁️  [Monitor] Started monitoring mission {mission_id} (session {session_id[:8]}...)"
        )

        # Poll for mission completion
        max_wait = 3600 * 24  # Max 24 hours
        poll_interval = 10  # Poll every 10 seconds
        waited = 0

        while waited < max_wait:
            try:
                # Check if session is still active
                session_result = manager.get_session_status(session_id)

                logger.debug(
                    f"[Monitor] Mission {mission_id[:8]}... Poll result: {session_result.get('status')} (waited {waited}s)"
                )

                if not session_result.get("success"):
                    # Session not found or error
                    logger.warning(
                        f"[Monitor] Session {session_id[:8]} error for mission {mission_id}: {session_result.get('error')}"
                    )
                    store.fail_mission(
                        mission_id,
                        f"Session lost: {session_result.get('error', 'Unknown')}",
                    )
                    return

                status = session_result.get("status", "unknown")

                if status == "completed":
                    # Mission completed - get the result
                    response = session_result.get("last_response", "")
                    logger.info(
                        f"[Monitor] Mission {mission_id} completed! Response length: {len(response)} chars"
                    )

                    # Get mission for task context
                    mission = store.get_mission(mission_id)
                    if not mission:
                        logger.error(
                            f"[Monitor] Mission {mission_id} not found in store"
                        )
                        store.fail_mission(
                            mission_id, "Mission not found after completion"
                        )
                        return

                    # Extract learnings
                    heuristics = call_learning_extractor(
                        agent_response=response,
                        task_context=mission.mission_text[:200],
                    )
                    logger.info(
                        f"[Monitor] Extracted {len(heuristics)} heuristics from mission {mission_id}"
                    )

                    # Complete the mission
                    store.complete_mission(mission_id, response, heuristics)

                    # Record heuristics to building
                    for h in heuristics:
                        record_heuristic_to_building(h, mission_id)

                    logger.info(
                        f"✅ [Monitor] Mission {mission_id} completed successfully after {waited}s"
                    )
                    return

                elif status == "error":
                    # Mission failed
                    error_msg = session_result.get("error", "Unknown error")
                    logger.error(
                        f"[Monitor] Mission {mission_id} failed with error: {error_msg}"
                    )
                    store.fail_mission(mission_id, error_msg)
                    return

                elif status == "running":
                    # Still running, continue polling
                    logger.debug(
                        f"[Monitor] Mission {mission_id} still running after {waited}s"
                    )
                    time.sleep(poll_interval)
                    waited += poll_interval
                    continue

                else:
                    # Unknown status
                    logger.warning(
                        f"[Monitor] Unknown session status for mission {mission_id}: {status}"
                    )
                    time.sleep(poll_interval)
                    waited += poll_interval

            except Exception as poll_error:
                logger.error(
                    f"[Monitor] Error polling mission {mission_id}: {poll_error}",
                    exc_info=True,
                )
                time.sleep(poll_interval)
                waited += poll_interval

        # Timeout reached
        logger.error(f"[Monitor] Mission {mission_id} timed out after {max_wait}s")
        store.fail_mission(mission_id, f"Mission timeout after {max_wait} seconds")

    except Exception as e:
        logger.error(
            f"[Monitor] Critical error monitoring mission {mission_id}: {e}",
            exc_info=True,
        )
        try:
            store.fail_mission(mission_id, f"Monitoring error: {str(e)}")
        except:
            pass


@router.get("/missions/{mission_id}/status")
async def get_mission_status(mission_id: str):
    """Get mission execution status."""
    try:
        store = get_mission_store()
        mission = store.get_mission(mission_id)

        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        return {
            "mission_id": mission.id,
            "status": mission.status,
            "session_id": mission.session_id,
            "created_at": mission.created_at,
            "started_at": mission.started_at,
            "completed_at": mission.completed_at,
            "duration_seconds": mission.duration_seconds,
            "progress": "running" if mission.status == "running" else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get mission status: {str(e)}"
        )


@router.post("/missions/{mission_id}/cancel")
async def cancel_mission(mission_id: str):
    """Cancel a running mission."""
    try:
        store = get_mission_store()
        mission = store.get_mission(mission_id)

        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel mission with status: {mission.status}",
            )

        # Try to kill the session if running
        if mission.status == "running" and mission.session_id:
            try:
                manager = get_agent_manager_instance()
                if manager:
                    manager.kill_session(mission.session_id)
            except Exception as kill_error:
                logger.warning(
                    f"Failed to kill session {mission.session_id}: {kill_error}"
                )

        # Mark as cancelled
        store.cancel_mission(mission_id)

        return {
            "status": "cancelled",
            "mission_id": mission_id,
            "message": "Mission cancelled successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel mission: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel mission: {str(e)}"
        )


@router.get("/missions/{mission_id}/result")
async def get_mission_result(mission_id: str):
    """Get full mission result."""
    try:
        store = get_mission_store()
        mission = store.get_mission(mission_id)

        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        if mission.status not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Mission not finished (status: {mission.status})",
            )

        return {
            "mission_id": mission.id,
            "status": mission.status,
            "result": mission.result,
            "error": mission.error,
            "heuristics": mission.heuristics,
            "duration_seconds": mission.duration_seconds,
            "completed_at": mission.completed_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission result: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get mission result: {str(e)}"
        )


# =============================================================================
# END NEW ASYNC MISSION SYSTEM
# =============================================================================


@router.post("/spawn_direct")
async def spawn_agent_direct(request: Dict[str, Any]):
    """Spawn an agent directly in main session + sub-session."""
    try:
        agent_type = request.get("agent_type")
        agent_name = request.get("agent_name") or agent_type or "Unknown Agent"
        model = request.get("model")
        mission = (
            request.get("mission")
            or f"You are {agent_name}. Identify yourself and your capabilities."
        )

        if not agent_type:
            raise HTTPException(status_code=400, detail="Missing agent_type")

        if not is_valid_agent_type(agent_type):
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type: {agent_type}"
            )

        manager = get_agent_manager_instance()
        if not manager:
            raise HTTPException(status_code=503, detail="AgentManager not available")

        logger.info(f"🤖 Spawning agent {agent_name} via AgentManager...")

        # Use AgentManager to initialize the agent
        result = manager.ask_agent(agent_type, mission)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize agent: {result.get('error')}",
            )

        session_id = result.get("session_id", "unknown")
        logger.info(f"✅ Agent {agent_name} spawned with session {session_id[:8]}...")

        # Create task file
        task_id, task_file = create_task(mission, agent_type, session_id, agent_name)

        # Start background monitoring
        monitor_thread = threading.Thread(
            target=monitor_mission,
            args=(session_id, task_file, agent_type, mission),
            daemon=True,
        )
        monitor_thread.start()

        return {
            "status": "spawned",
            "agent_id": session_id,
            "agent_type": agent_type,
            "agent_name": agent_name,
            "model": model,
            "session_id": session_id,
            "task_id": task_id,
            "message": f"Agent {agent_name} spawned successfully with ID {session_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error spawning agent directly: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spawn")
async def spawn_agent_legacy(request: Dict[str, Any]):
    """Legacy: Start an agent."""
    if "agent_type" not in request:
        raise HTTPException(status_code=400, detail="Missing agent_type")

    return {
        "status": "ok",
        "agent_type": request["agent_type"],
        "message": f"Agent {request['agent_type']} is ready",
    }


@router.post("/kill")
async def kill_agent_legacy(request: Dict[str, Any]):
    """Legacy: Kill an agent."""
    return {
        "status": "ok",
        "message": "Session management is automatic",
    }


@router.post("/test")
async def test_agent_legacy(request: Dict[str, Any]):
    """Legacy: Test an agent."""
    if "agent_type" in request:
        return {
            "status": "ready",
            "dry_run": True,
            "message": f"Agent {request['agent_type']} is ready",
        }
    raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/logs/{agent_type}")
async def get_agent_logs(agent_type: str, lines: int = 50):
    """Get agent logs."""
    return {"logs": f"Logs for {agent_type} not available in simplified mode"}


@router.get("/heuristics")
async def get_heuristics():
    """Get extracted heuristics from all tasks."""
    try:
        all_heuristics = []

        for session_dir in TASKS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            for task_file in session_dir.glob("*.json"):
                try:
                    with open(task_file, "r") as f:
                        task_data = json.load(f)

                    if "heuristics" in task_data and task_data["heuristics"]:
                        for heuristic in task_data["heuristics"]:
                            all_heuristics.append(
                                {
                                    "task_id": task_data.get("id"),
                                    "session_id": task_data.get("session_id"),
                                    "domain": heuristic.get("domain"),
                                    "text": heuristic.get("text"),
                                    "type": heuristic.get("type"),
                                    "confidence": heuristic.get("confidence"),
                                    "extracted_at": heuristic.get("extracted_at"),
                                }
                            )
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read task file {task_file}: {e}")

        # Sort by extraction time (newest first)
        all_heuristics.sort(key=lambda h: h.get("extracted_at", ""), reverse=True)

        return {
            "status": "ok",
            "heuristics": all_heuristics,
            "count": len(all_heuristics),
        }

    except Exception as e:
        logger.error(f"Error retrieving heuristics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_mission(request: MissionRequest):
    """Analyze a mission without executing."""
    return {
        "mode": request.mode,
        "mission": request.mission,
        "analysis": "Analysis not available in simplified mode",
    }


@router.post("/swarm")
async def run_swarm(request: SwarmRequest):
    """Execute a swarm mission with multiple agents."""
    try:
        # Use orchestrator if available
        if HAS_ORCHESTRATOR:
            try:
                orchestrator = get_orchestrator()

                if not orchestrator.running:
                    orchestrator.start()

                result = orchestrator.run_swarm(
                    task=request.task, mode=request.mode, context=request.context
                )

                return result

            except Exception as e:
                logger.error(f"Error running swarm with orchestrator: {e}")

        # Use AgentManager for swarm
        manager = get_agent_manager_instance()
        if not manager:
            return {
                "status": "error",
                "error": "AgentManager not available",
                "task": request.task,
                "mode": request.mode,
            }

        logger.info(f"🤖 Running swarm via AgentManager: {request.task[:50]}...")

        # Use multi-agent-coordinator agent
        swarm_prompt = f"""[SWARM] Execute task with multiple agents in {request.mode} mode.

Task: {request.task}

Context: {request.context}

Coordinate multiple agents to work together on this task and provide a comprehensive response."""

        result = manager.ask_agent("multi-agent-coordinator", swarm_prompt)

        if result.get("success"):
            session_id = result.get("session_id", "unknown")
            return {
                "status": "started",
                "task": request.task,
                "mode": request.mode,
                "session_id": session_id,
            }
        else:
            return {
                "status": "error",
                "error": f"AgentManager swarm failed: {result.get('error')}",
                "task": request.task,
                "mode": request.mode,
            }

    except Exception as e:
        logger.error(f"Error running swarm: {e}")
        return {
            "status": "error",
            "error": str(e),
            "task": request.task,
            "mode": request.mode,
        }


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get details of a specific task by ID."""
    try:
        # Search for task file in tasks directory
        for session_dir in TASKS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            task_file = session_dir / f"{task_id}.json"
            if task_file.exists():
                with open(task_file, "r") as f:
                    task_data = json.load(f)
                    return {"status": "ok", "task": task_data}

        # Task not found
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(session_id: Optional[str] = None, status: Optional[str] = None):
    """List all tasks, optionally filtered by session or status."""
    try:
        tasks = []

        for session_dir in TASKS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            current_session_id = session_dir.name

            # Filter by session_id if provided
            if session_id and current_session_id != session_id:
                continue

            for task_file in session_dir.glob("*.json"):
                try:
                    with open(task_file, "r") as f:
                        task_data = json.load(f)

                        # Filter by status if provided
                        if status and task_data.get("status") != status:
                            continue

                        tasks.append(task_data)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load task file {task_file}: {e}")

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.get("id", ""), reverse=True)

        return {"status": "ok", "tasks": tasks, "count": len(tasks)}

    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_mission_logs(limit: int = 50):
    """Get recent mission execution logs from task notes."""
    try:
        logs = []

        for session_dir in TASKS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            for task_file in session_dir.glob("*.json"):
                try:
                    with open(task_file, "r") as f:
                        task_data = json.load(f)

                    # Extract notes as logs
                    for note in task_data.get("notes", []):
                        logs.append(
                            {
                                "timestamp": note.get("timestamp"),
                                "level": "info"
                                if note.get("source") == "dashboard"
                                else "agent",
                                "source": note.get("source"),
                                "message": note.get("text"),
                                "task_id": task_data.get("id"),
                                "session_id": task_data.get("session_id"),
                            }
                        )

                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read task file {task_file}: {e}")

        # Sort by timestamp (newest first)
        logs.sort(key=lambda l: l.get("timestamp", ""), reverse=True)

        # Apply limit
        logs = logs[:limit]

        return {"status": "ok", "logs": logs, "count": len(logs)}

    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
