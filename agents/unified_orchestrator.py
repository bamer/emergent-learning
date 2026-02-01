"""
Unified Orchestrator for ELF Agent Management
============================================

Central coordinator for all ELF agents (Sentinel, Watcher, Researcher, etc.)
and OpenCode agents. Handles agent lifecycle, status tracking, and swarm coordination.

This replaces the missing orchestrator that was referenced in the old agents router.
"""

import json
import logging
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents that can be managed."""

    SENTINEL = "sentinel"
    WATCHER = "watcher"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    CREATIVE = "creative"
    CEO = "ceo"
    MULTI_AGENT_COORDINATOR = "multi-agent-coordinator"
    SWARM_ORCHESTRATOR = "swarm-orchestrator"


class AgentStatus(Enum):
    """Possible agent statuses."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class UnifiedOrchestrator:
    """
    Central orchestrator for managing all agents in the ELF system.

    Coordinates ELF Python agents and OpenCode prompt-based agents.
    """

    def __init__(self, opencode_server: str = "http://localhost:4096"):
        self.opencode_server = opencode_server
        self.running = False
        self.agents: Dict[AgentType, Dict[str, Any]] = {}
        self.stats = {
            "agents_started": 0,
            "agents_stopped": 0,
            "agents_crashed": 0,
            "errors_handled": 0,
            "escalations": 0,
            "start_time": None,
        }
        self._lock = threading.RLock()

        # Initialize agent registry
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the agent registry with default states."""
        for agent_type in AgentType:
            self.agents[agent_type] = {
                "type": agent_type.value,
                "status": AgentStatus.STOPPED.value,
                "start_time": None,
                "last_activity": None,
                "error_count": 0,
                "session_id": None,
                "description": self._get_agent_description(agent_type),
            }

    def _get_agent_description(self, agent_type: AgentType) -> str:
        """Get human-readable description for an agent type."""
        descriptions = {
            AgentType.SENTINEL: "Continuous surveillance and pattern detection",
            AgentType.WATCHER: "Periodic checks and interventions",
            AgentType.RESEARCHER: "Deep investigation and evidence gathering",
            AgentType.ARCHITECT: "System design and structural planning",
            AgentType.SKEPTIC: "Critical analysis and risk identification",
            AgentType.CREATIVE: "Innovation and novel solutions",
            AgentType.CEO: "Executive decisions and strategic direction",
            AgentType.MULTI_AGENT_COORDINATOR: "Complex workflow orchestration",
            AgentType.SWARM_ORCHESTRATOR: "Multi-agent parallel execution",
        }
        return descriptions.get(agent_type, f"{agent_type.value} agent")

    def start(self):
        """Start the orchestrator."""
        with self._lock:
            if self.running:
                logger.warning("Orchestrator is already running")
                return

            self.running = True
            self.stats["start_time"] = datetime.now().isoformat()
            logger.info("Unified Orchestrator started")

    def stop(self):
        """Stop the orchestrator and all agents."""
        with self._lock:
            if not self.running:
                return

            # Stop all running agents
            for agent_type in list(self.agents.keys()):
                if self.agents[agent_type]["status"] == AgentStatus.RUNNING.value:
                    self.kill_agent(agent_type)

            self.running = False
            logger.info("Unified Orchestrator stopped")

    def spawn_agent(self, agent_type: AgentType) -> bool:
        """
        Spawn/start an agent.

        Args:
            agent_type: Type of agent to spawn

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if not self.running:
                logger.error("Orchestrator not running")
                return False

            agent_info = self.agents.get(agent_type)
            if not agent_info:
                logger.error(f"Unknown agent type: {agent_type}")
                return False

            # Check if already running
            if agent_info["status"] == AgentStatus.RUNNING.value:
                logger.info(f"Agent {agent_type.value} already running")
                return True

            try:
                # Update status
                agent_info["status"] = AgentStatus.STARTING.value
                agent_info["start_time"] = datetime.now().isoformat()

                # For OpenCode agents, we don't actually spawn processes
                # We just mark them as available for use
                agent_info["status"] = AgentStatus.RUNNING.value
                agent_info["last_activity"] = datetime.now().isoformat()
                self.stats["agents_started"] += 1

                logger.info(f"Agent {agent_type.value} marked as running")
                return True

            except Exception as e:
                logger.error(f"Failed to spawn agent {agent_type.value}: {e}")
                agent_info["status"] = AgentStatus.ERROR.value
                agent_info["error_count"] += 1
                self.stats["errors_handled"] += 1
                return False

    def kill_agent(self, agent_type: AgentType, force: bool = False) -> bool:
        """
        Kill/stop an agent.

        Args:
            agent_type: Type of agent to kill
            force: Whether to force kill

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            agent_info = self.agents.get(agent_type)
            if not agent_info:
                return False

            try:
                # Update status
                agent_info["status"] = AgentStatus.STOPPING.value

                # For OpenCode agents, we just mark them as stopped
                agent_info["status"] = AgentStatus.STOPPED.value
                agent_info["session_id"] = None
                self.stats["agents_stopped"] += 1

                logger.info(f"Agent {agent_type.value} marked as stopped")
                return True

            except Exception as e:
                logger.error(f"Failed to kill agent {agent_type.value}: {e}")
                agent_info["status"] = AgentStatus.ERROR.value
                agent_info["error_count"] += 1
                self.stats["errors_handled"] += 1
                return False

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current status of all agents.

        Returns:
            Status dictionary with orchestrator and agent info
        """
        with self._lock:
            uptime = 0
            if self.stats["start_time"]:
                start_time = datetime.fromisoformat(self.stats["start_time"])
                uptime = (datetime.now() - start_time).total_seconds()

            return {
                "timestamp": datetime.now().isoformat(),
                "orchestrator": {
                    "running": self.running,
                    "start_time": self.stats["start_time"],
                    "uptime_seconds": int(uptime),
                },
                "agents": list(self.agents.values()),
                "stats": self.stats.copy(),
            }

    def run_swarm(
        self, task: str, mode: str = "all", context: str = ""
    ) -> Dict[str, Any]:
        """
        Run a swarm of agents on a task.

        Args:
            task: Main task description
            mode: Swarm mode (analysis, design, implementation, learning, all)
            context: Additional context for the task

        Returns:
            Swarm execution results
        """
        with self._lock:
            if not self.running:
                return {
                    "status": "error",
                    "error": "Orchestrator not running",
                    "task": task,
                    "mode": mode,
                }

            try:
                # Define agent sequences for different modes
                swarm_sequences = {
                    "analysis": ["researcher", "architect"],
                    "design": ["architect", "creative", "skeptic"],
                    "implementation": ["architect", "researcher", "skeptic"],
                    "learning": ["learning-extractor", "researcher", "architect"],
                    "all": [
                        "researcher",
                        "architect",
                        "skeptic",
                        "creative",
                        "learning-extractor",
                    ],
                }

                # Determine agent sequence
                agent_sequence = swarm_sequences.get(mode, swarm_sequences["all"])

                logger.info(
                    f"Creating swarm session with OpenCode server: {self.opencode_server}"
                )

                # Create a session for the swarm
                session_response = requests.post(
                    f"{self.opencode_server}/session",
                    json={"title": f"Swarm: {task[:50]}"},
                    timeout=30,
                )

                logger.info(
                    f"Session creation response status: {session_response.status_code}"
                )

                if session_response.status_code not in [200, 201]:
                    return {
                        "status": "error",
                        "error": f"Failed to create session: {session_response.status_code}",
                        "task": task,
                        "mode": mode,
                    }

                session_id = session_response.json().get("id")
                logger.info(f"Session created with ID: {session_id}")

                # Send swarm instruction to OpenCode
                swarm_prompt = f"""[SWARM] Execute task with multiple agents in {mode} mode.
                
Task: {task}

Context: {context}

Agent Sequence: {", ".join(agent_sequence)}

Coordinate the agents to work together on this task and provide a comprehensive response."""

                logger.info(f"Sending swarm message to session: {session_id}")

                # Send message in background thread - don't wait for response
                logger.info(f"Preparing to send message to session {session_id}")

                def send_message_async():
                    try:
                        message_response = requests.post(
                            f"{self.opencode_server}/session/{session_id}/message",
                            json={
                                "parts": [{"type": "text", "text": swarm_prompt}],
                                "agent": "multi-agent-coordinator",
                            },
                            timeout=30,  # Short timeout for initial send
                        )

                        logger.info(
                            f"Message send status: {message_response.status_code}"
                        )

                        if message_response.status_code not in [200, 201]:
                            logger.warning(
                                f"Message send failed with status: {message_response.status_code}"
                            )
                    except Exception as e:
                        logger.warning(f"Message send failed: {e}")

                # Start background thread and return immediately
                import threading

                thread = threading.Thread(target=send_message_async, daemon=True)
                thread.start()

                # Return immediately without waiting for response
                return {
                    "status": "started",
                    "task": task,
                    "mode": mode,
                    "session_id": session_id,
                    "agents": agent_sequence,
                    "agent_count": len(agent_sequence),
                }

            except Exception as e:
                logger.error(f"Error running swarm: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "task": task,
                    "mode": mode,
                }


# Singleton instance management
_orchestrator_instance: Optional[UnifiedOrchestrator] = None
_orchestrator_lock = threading.Lock()


def get_orchestrator() -> UnifiedOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator_instance

    with _orchestrator_lock:
        if _orchestrator_instance is None:
            _orchestrator_instance = UnifiedOrchestrator()

        return _orchestrator_instance
