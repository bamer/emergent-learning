#!/usr/bin/env python3
"""
Agent Orchestrator - Main coordination agent

The Orchestrator is the central coordination point for all ELF agents:
- Manages agent lifecycle and state
- Coordinates agent communication
- Handles agent scheduling and prioritization
- Provides real-time agent status
- Integrates with OpenCode API for agent execution

This replaces the ad-hoc agent startup with proper orchestration.
"""

import json
import time
import logging
import sqlite3
import requests
import threading
import atexit
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum
import sys

# Add path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from opencode_client import OpenCodeClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/bamer/.opencode/emergent-learning/logs/orchestrator.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Import Agent Execution Engine and Pattern Response Handler
try:
    from agent_execution_engine import AgentExecutionEngine
    from pattern_response_handler import PatternResponseHandler

    agent_execution_available = True
except ImportError as e:
    logger.warning(f"⚠️ Agent execution components not available: {e}")
    agent_execution_available = False
    AgentExecutionEngine = None
    PatternResponseHandler = None
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/bamer/.opencode/emergent-learning/logs/orchestrator.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"


class AgentType(Enum):
    """Agent types with their roles."""

    ORCHESTRATOR = "orchestrator"
    SENTINEL = "sentinel"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    CREATIVE = "creative"
    CEO = "ceo"


class AgentDefinition:
    """Definition of an agent with its configuration."""

    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        icon: str,
        priority: int = 5,
        auto_start: bool = False,
        session_timeout: int = 3600,
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.icon = icon
        self.priority = priority  # 1=highest, 10=lowest
        self.auto_start = auto_start
        self.session_timeout = session_timeout  # seconds
        self.status = AgentStatus.STOPPED
        self.session_id = None
        self.last_activity = None
        self.start_time = None
        self.error_count = 0
        self.metadata = {}


class AgentOrchestrator:
    """Main agent orchestration system."""

    def __init__(self, server_url: str = "http://localhost:4096"):
        self.server_url = server_url
        self.client = OpenCodeClient(server_url=server_url)
        self.db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"

        # Agent registry
        self.agents = self._initialize_agents()

        # Initialize Agent Execution Engine and Pattern Response Handler
        if agent_execution_available:
            self.execution_engine = AgentExecutionEngine()
            self.pattern_handler = PatternResponseHandler()
        else:
            self.execution_engine = None
            self.pattern_handler = None
        self.pattern_handler = (
            PatternResponseHandler() if agent_execution_available else None
        )
        self.pattern_handler = (
            PatternResponseHandler() if PatternResponseHandler else None
        )

        # Orchestrator state
        self.running = False
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()

        # Statistics
        self.stats = {
            "total_sessions_created": 0,
            "total_messages_sent": 0,
            "agents_started": 0,
            "agents_stopped": 0,
            "errors_handled": 0,
            "uptime_seconds": 0,
        }

        # Register cleanup
        atexit.register(self.shutdown)

    def _initialize_agents(self) -> Dict[AgentType, AgentDefinition]:
        """Initialize all available agents with their definitions."""
        agents = {}

        # Orchestrator (self)
        agents[AgentType.ORCHESTRATOR] = AgentDefinition(
            agent_type=AgentType.ORCHESTRATOR,
            name="ELF Orchestrator",
            description="Central coordination and agent lifecycle management",
            icon="🎯",
            priority=1,
            auto_start=True,
        )

        # Sentinel - Monitoring agent
        agents[AgentType.SENTINEL] = AgentDefinition(
            agent_type=AgentType.SENTINEL,
            name="Sentinel",
            description="Continuous monitoring and pattern detection",
            icon="🔍",
            priority=2,
            auto_start=True,
        )

        # Researcher - Investigation agent
        agents[AgentType.RESEARCHER] = AgentDefinition(
            agent_type=AgentType.RESEARCHER,
            name="Researcher",
            description="Deep investigation and evidence gathering",
            icon="🔬",
            priority=4,
            auto_start=False,
        )

        # Architect - System design agent
        agents[AgentType.ARCHITECT] = AgentDefinition(
            agent_type=AgentType.ARCHITECT,
            name="Architect",
            description="System design and structure planning",
            icon="🏗️",
            priority=5,
            auto_start=False,
        )

        # Skeptic - Critical analysis agent
        agents[AgentType.SKEPTIC] = AgentDefinition(
            agent_type=AgentType.SKEPTIC,
            name="Skeptic",
            description="Critical analysis and risk identification",
            icon="❓",
            priority=6,
            auto_start=False,
        )

        # Creative - Innovation agent
        agents[AgentType.CREATIVE] = AgentDefinition(
            agent_type=AgentType.CREATIVE,
            name="Creative",
            description="Innovation and novel solution generation",
            icon="💡",
            priority=7,
            auto_start=False,
        )

        # CEO - Decision making agent
        agents[AgentType.CEO] = AgentDefinition(
            agent_type=AgentType.CEO,
            name="CEO",
            description="Executive decisions and strategic direction",
            icon="👑",
            priority=1,
            auto_start=False,  # Only started when needed
        )

        return agents

    def start_orchestrator(self):
        """Start the orchestrator and auto-start agents."""
        logger.info("🚀 Starting ELF Agent Orchestrator...")
        self.running = True
        self.start_time = datetime.now()

        # Set orchestrator status
        self.agents[AgentType.ORCHESTRATOR].status = AgentStatus.RUNNING
        self.agents[AgentType.ORCHESTRATOR].start_time = datetime.now()

        # Start auto-start agents
        for agent_type, agent_def in self.agents.items():
            if agent_def.auto_start and agent_type != AgentType.ORCHESTRATOR:
                self.start_agent(agent_type)

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        logger.info("✅ ELF Agent Orchestrator started successfully")
        self._record_orchestrator_event(
            "orchestrator_started", "Orchestrator system started"
        )

    def shutdown(self):
        """Gracefully shutdown all agents."""
        if not self.running:
            return

        logger.info("🛑 Shutting down ELF Agent Orchestrator...")
        self.running = False
        self.shutdown_event.set()

        # Stop all agents
        for agent_type in list(self.agents.keys()):
            self.stop_agent(agent_type)

        # Wait for monitoring thread
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)

        # Update final stats
        if hasattr(self, "start_time"):
            self.stats["uptime_seconds"] = (
                datetime.now() - self.start_time
            ).total_seconds()

        self._record_orchestrator_event(
            "orchestrator_stopped", "Orchestrator system shutdown"
        )
        logger.info("✅ ELF Agent Orchestrator shutdown complete")

    def start_agent(self, agent_type: AgentType) -> bool:
        """Start a specific agent."""
        if agent_type not in self.agents:
            logger.error(f"Unknown agent type: {agent_type}")
            return False

        agent = self.agents[agent_type]

        if agent.status != AgentStatus.STOPPED:
            logger.warning(f"Agent {agent.name} is already {agent.status.value}")
            return False

        try:
            logger.info(f"🚀 Starting agent: {agent.name}")
            agent.status = AgentStatus.STARTING

            # Create OpenCode session for the agent
            session_data = self._create_agent_session(agent)

            if session_data:
                agent.session_id = session_data["id"]
                agent.status = AgentStatus.RUNNING
                agent.last_activity = datetime.now()
                agent.start_time = datetime.now()
                agent.error_count = 0

                self.stats["agents_started"] += 1
                logger.info(
                    f"✅ Agent {agent.name} started (session: {agent.session_id})"
                )

                self._record_agent_event(
                    agent_type, "agent_started", f"Agent {agent.name} started"
                )
                return True
            else:
                agent.status = AgentStatus.ERROR
                agent.error_count += 1
                logger.error(f"❌ Failed to start agent {agent.name}")
                return False

        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            logger.error(f"❌ Exception starting agent {agent.name}: {e}")
            self.stats["errors_handled"] += 1
            return False

    def stop_agent(self, agent_type: AgentType) -> bool:
        """Stop a specific agent."""
        if agent_type not in self.agents:
            logger.error(f"Unknown agent type: {agent_type}")
            return False

        agent = self.agents[agent_type]

        if agent.status == AgentStatus.STOPPED:
            logger.warning(f"Agent {agent.name} is already stopped")
            return True

        try:
            logger.info(f"🛑 Stopping agent: {agent.name}")
            agent.status = AgentStatus.STOPPING

            # Close OpenCode session
            if agent.session_id:
                success = self._close_agent_session(agent)
                if success:
                    agent.session_id = None
                    agent.status = AgentStatus.STOPPED
                    self.stats["agents_stopped"] += 1
                    logger.info(f"✅ Agent {agent.name} stopped")
                    self._record_agent_event(
                        agent_type, "agent_stopped", f"Agent {agent.name} stopped"
                    )
                    return True
                else:
                    agent.status = AgentStatus.ERROR
                    logger.error(f"❌ Failed to stop agent {agent.name}")
                    return False

        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            logger.error(f"❌ Exception stopping agent {agent.name}: {e}")
            self.stats["errors_handled"] += 1
            return False

    def call_agent(
        self, agent_type: AgentType, prompt: str, timeout: int = 300
    ) -> Optional[str]:
        """Call a specific agent with a prompt."""
        if agent_type not in self.agents:
            logger.error(f"Unknown agent type: {agent_type}")
            return None

        agent = self.agents[agent_type]

        # Start agent if not running
        if agent.status == AgentStatus.STOPPED:
            if not self.start_agent(agent_type):
                return None

        try:
            agent.status = AgentStatus.BUSY
            agent.last_activity = datetime.now()

            # Send message to agent session
            response = self._send_agent_message(agent, prompt, timeout)

            if response:
                self.stats["total_messages_sent"] += 1
                logger.info(f"📞 Agent {agent.name} responded ({len(response)} chars)")
                self._record_agent_event(
                    agent_type, "agent_called", f"Agent {agent.name} handled request"
                )
            else:
                logger.warning(f"⚠️ Agent {agent.name} did not respond")

            agent.status = AgentStatus.RUNNING
            return response

        except Exception as e:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            logger.error(f"❌ Exception calling agent {agent.name}: {e}")
            self.stats["errors_handled"] += 1
            return None

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of all agents."""
        status = {
            "orchestrator": {
                "running": self.running,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                if hasattr(self, "start_time") and self.start_time
                else 0,
                "stats": self.stats.copy(),
            },
            "agents": {},
        }

        for agent_type, agent in self.agents.items():
            status["agents"][agent_type.value] = {
                "name": agent.name,
                "description": agent.description,
                "icon": agent.icon,
                "status": agent.status.value,
                "priority": agent.priority,
                "session_id": agent.session_id,
                "last_activity": agent.last_activity.isoformat()
                if agent.last_activity
                else None,
                "start_time": agent.start_time.isoformat()
                if agent.start_time
                else None,
                "error_count": agent.error_count,
                "auto_start": agent.auto_start,
            }

        return status

    def _create_agent_session(self, agent: AgentDefinition) -> Optional[Dict[str, Any]]:
        """Create OpenCode session for an agent."""
        try:
            response = requests.post(
                f"{self.server_url}/session",
                json={"title": f"ELF Agent: {agent.name}"},
                timeout=10,
            )

            if response.status_code == 200:
                session_data = response.json()
                self.stats["total_sessions_created"] += 1
                return session_data
            else:
                logger.error(
                    f"Failed to create session for {agent.name}: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception creating session for {agent.name}: {e}")
            return None

    def _close_agent_session(self, agent: AgentDefinition) -> bool:
        """Close OpenCode session for an agent."""
        if not agent.session_id:
            return True

        try:
            response = requests.delete(
                f"{self.server_url}/session/{agent.session_id}",
                timeout=5,
            )

            return response.status_code in [200, 404]  # 404 is OK (already gone)

        except Exception as e:
            logger.error(f"Exception closing session for {agent.name}: {e}")
            return False

    def _send_agent_message(
        self, agent: AgentDefinition, prompt: str, timeout: int
    ) -> Optional[str]:
        """Send message to agent session and get response."""
        if not agent.session_id:
            return None

        try:
            # Prepend agent-specific instruction
            if agent.agent_type == AgentType.SENTINEL:
                full_prompt = (
                    f"@sentinel\n\nYou are the Sentinel monitoring agent. {prompt}"
                )
            elif agent.agent_type == AgentType.RESEARCHER:
                full_prompt = f"@researcher\n\nYou are the Researcher investigation agent. {prompt}"
            elif agent.agent_type == AgentType.ARCHITECT:
                full_prompt = (
                    f"@architect\n\nYou are the Architect design agent. {prompt}"
                )
            elif agent.agent_type == AgentType.SKEPTIC:
                full_prompt = (
                    f"@skeptic\n\nYou are the Skeptic critical analysis agent. {prompt}"
                )
            elif agent.agent_type == AgentType.CREATIVE:
                full_prompt = (
                    f"@creative\n\nYou are the Creative innovation agent. {prompt}"
                )
            elif agent.agent_type == AgentType.CEO:
                full_prompt = (
                    f"@general\n\nYou are the CEO decision-making agent. {prompt}"
                )
            else:
                full_prompt = prompt

            message_data = {
                "model": {"providerID": "opencode", "modelID": "big-pickle"},
                "parts": [{"type": "text", "text": full_prompt}],
            }

            response = requests.post(
                f"{self.server_url}/session/{agent.session_id}/message",
                json=message_data,
                timeout=timeout,
            )

            if response.status_code == 200:
                parts = response.json().get("parts", [])
                result = ""
                for part in parts:
                    if part.get("type") == "text":
                        result += part.get("text", "")
                return result.strip() if result else None
            else:
                logger.error(
                    f"Failed to send message to {agent.name}: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception sending message to {agent.name}: {e}")
            return None

    def _monitoring_loop(self):
        """Background monitoring loop for agent health."""
        logger.info("🔍 Starting agent monitoring loop")

        while self.running and not self.shutdown_event.is_set():
            try:
                # Check agent health
                current_time = datetime.now()

                for agent_type, agent in self.agents.items():
                    if agent.status == AgentStatus.RUNNING:
                        # Check for session timeout
                        if agent.last_activity and agent.session_timeout:
                            idle_time = (
                                current_time - agent.last_activity
                            ).total_seconds()
                            if idle_time > agent.session_timeout:
                                logger.info(
                                    f"⏰ Agent {agent.name} session timeout, stopping..."
                                )
                                self.stop_agent(agent_type)

                    elif agent.status == AgentStatus.ERROR:
                        # Try to restart errored agents (with backoff)
                        if agent.error_count < 3:  # Max 3 restart attempts
                            wait_time = min(
                                60, 10 * agent.error_count
                            )  # Exponential backoff
                            if (
                                agent.last_activity
                                and (current_time - agent.last_activity).total_seconds()
                                > wait_time
                            ):
                                logger.info(
                                    f"🔄 Attempting to restart errored agent {agent.name}..."
                                )
                                agent.status = AgentStatus.STOPPED
                                self.start_agent(agent_type)

                # Sleep before next check
                self.shutdown_event.wait(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.stats["errors_handled"] += 1
                self.shutdown_event.wait(60)  # Wait longer on error

            # Check CEO inbox for pending decisions (every cycle)
            if self.running and not self.shutdown_event.is_set():
                inbox_items = self._check_ceo_inbox()
                if inbox_items:
                    logger.info(f"📬 CEO Inbox: {len(inbox_items)} pending items")
                    # If CEO agent is running, notify it
                    if self.agents[AgentType.CEO].status == AgentStatus.RUNNING:
                        self._notify_ceo_of_inbox(inbox_items)
                    else:
                        # Auto-start CEO agent when inbox items exist
                        logger.info("🚀 Auto-starting CEO agent for critical decisions")
                        self.start_agent(AgentType.CEO)
                        # Wait a moment for CEO to be fully started
                        import time

                        time.sleep(3)
                        # Now notify the CEO
                        self._notify_ceo_of_inbox(inbox_items)

    def _record_orchestrator_event(
        self, event_type: str, summary: str, data: Dict[str, Any] = None
    ):
        """Record orchestrator events to database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO event_chronicle (timestamp, event_type, source, source_id, status, summary, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    event_type,
                    "agent_orchestrator",
                    "orchestrator-main",
                    "completed",
                    summary,
                    json.dumps(data) if data else None,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record orchestrator event: {e}")

    def _record_agent_event(
        self,
        agent_type: AgentType,
        event_type: str,
        summary: str,
        data: Dict[str, Any] = None,
    ):
        """Record agent-specific events to database."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO event_chronicle (timestamp, event_type, source, source_id, status, summary, data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    event_type,
                    "agent_orchestrator",
                    agent_type.value,
                    "completed",
                    summary,
                    json.dumps(data) if data else None,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record agent event: {e}")

    def _check_ceo_inbox(self) -> List[str]:
        """Check CEO inbox for pending decisions."""
        inbox_path = Path("/home/bamer/.opencode/emergent-learning/ceo-inbox")
        if not inbox_path.exists():
            return []

        # Get all .md files in inbox (unprocessed)
        inbox_items = []
        for file_path in inbox_path.glob("*.md"):
            inbox_items.append(str(file_path))

        return inbox_items

    def _notify_ceo_of_inbox(self, inbox_items: List[str]):
        """Notify CEO agent about pending inbox items."""
        if not inbox_items:
            return

        # Build notification prompt
        items_summary = []
        for item_path in inbox_items:
            filename = Path(item_path).name
            items_summary.append(f"- {filename}")

        prompt = f"""
🚨 **CEO INBOX ALERT**

You have {len(inbox_items)} pending decision(s) requiring immediate attention:

{chr(10).join(items_summary)}

Please review and provide decisions on each item.
Items are located in: /home/bamer/.opencode/emergent-learning/ceo-inbox/

Priority: CRITICAL - System stability issues require executive decisions.
"""

        # Call CEO agent with notification
        try:
            response = self.call_agent(
                AgentType.CEO,
                prompt,
                timeout=600,  # 10 minutes for complex decisions
            )

            if response:
                logger.info(
                    f"✅ CEO notified and responded to {len(inbox_items)} inbox items"
                )
                # Record the CEO's decision processing
                self._record_agent_event(
                    AgentType.CEO,
                    "ceo_inbox_processed",
                    f"CEO processed {len(inbox_items)} inbox items",
                )
            else:
                logger.warning("⚠️ CEO notified but no response received")

        except Exception as e:
            logger.error(f"❌ Failed to notify CEO of inbox items: {e}")


def main():
    """Main entry point for the orchestrator."""
    orchestrator = AgentOrchestrator()

    try:
        # Start orchestrator
        orchestrator.start_orchestrator()

        print("\n" + "=" * 70)
        print("🤖 ELF Agent Orchestrator - Running")
        print("=" * 70)

        # Show initial status
        status = orchestrator.get_agent_status()
        print(
            f"Orchestrator: {'🟢 RUNNING' if status['orchestrator']['running'] else '🔴 STOPPED'}"
        )
        print(
            f"Active agents: {len([a for a in status['agents'].values() if a['status'] == 'running'])}"
        )
        print()

        for agent_info in status["agents"].values():
            status_emoji = {
                "running": "🟢",
                "starting": "🟡",
                "stopped": "⚪",
                "error": "🔴",
                "busy": "🟠",
                "stopping": "🟡",
            }.get(agent_info["status"], "⚪")

            print(
                f"{agent_info['icon']} {agent_info['name']}: {status_emoji} {agent_info['status'].upper()}"
            )

        print("\n" + "=" * 70)
        print("Press Ctrl+C to stop...")

        # Keep running
        while True:
            time.sleep(60)

            # Show status every 5 minutes
            if int(time.time()) % 300 == 0:
                status = orchestrator.get_agent_status()
                active_count = len(
                    [a for a in status["agents"].values() if a["status"] == "running"]
                )
                print(f"\n📊 Status Check - Active agents: {active_count}")

    except KeyboardInterrupt:
        print("\n⏹️  Shutdown requested...")
        orchestrator.shutdown()
        print("✅ Orchestrator stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        orchestrator.shutdown()
        raise


if __name__ == "__main__":
    main()
