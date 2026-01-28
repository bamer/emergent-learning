#!/usr/bin/env python3
"""
ELF Coordinator System - Agent and Mission Lifecycle Management

Implements ELF-compliant coordination with:
- Blackboard protocol for agent communication
- Heartbeat monitoring (30s standard)
- Mission lifecycle: launching → active → completing → completed/failed
- Automatic recovery mechanisms
- Event chronicle logging

Usage:
    python coordinator.py status               # Show system status
    python coordinator.py create-mission <json> # Create new mission
    python coordinator.py launch-mission <id>   # Launch mission agents
    python coordinator.py monitor              # Monitor and recover agents
    python coordinator.py stop-mission <id>     # Stop specific mission
    python coordinator.py health-check          # System health check
"""

import json
import sys
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

# Import ELF modules
try:
    from query.lifecycle_manager import LifecycleManager
    from elf_paths import get_base_path
except ImportError:
    # Fallback for direct execution
    def get_base_path():
        return Path(__file__).parent.parent

    class LifecycleManager:
        def __init__(self, *args, **kwargs):
            pass


class ELFCoordinator:
    """Main ELF Coordinator for agent and mission lifecycle management."""

    def __init__(self):
        self.base_path = get_base_path()
        self.coordination_dir = self.base_path / ".coordination"
        self.blackboard_file = self.coordination_dir / "blackboard.json"
        self.missions_dir = self.coordination_dir / "missions"
        self.event_chronicle = self.coordination_dir / "event_chronicle.md"
        self.agent_registry = self.coordination_dir / "agent_registry.json"

        # ELF Standards
        self.HEARTBEAT_INTERVAL = 30  # seconds
        self.MAX_STALE_TIME = 120  # seconds before agent considered stale
        self.MISSION_TIMEOUT = 3600  # 1 hour default mission timeout

        # Ensure directories exist
        self.coordination_dir.mkdir(exist_ok=True)
        self.missions_dir.mkdir(exist_ok=True)

        # Initialize systems
        self._ensure_blackboard()
        self._ensure_agent_registry()

    def _ensure_blackboard(self):
        """Initialize blackboard if doesn't exist."""
        if not self.blackboard_file.exists():
            initial_blackboard = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "initializing",
                "mission": None,
                "mission_id": None,
                "agents": {},
                "swarm_status": "idle",
                "coordination": {
                    "protocol": "blackboard",
                    "heartbeat_interval": self.HEARTBEAT_INTERVAL,
                    "max_stale_time": self.MAX_STALE_TIME,
                    "failure_recovery": "automatic",
                },
                "issues": [],
            }
            self._save_blackboard(initial_blackboard)

    def _ensure_agent_registry(self):
        """Initialize agent registry if doesn't exist."""
        if not self.agent_registry.exists():
            registry = {
                "timestamp": datetime.now().isoformat(),
                "registered_agents": {},
                "available_personas": [
                    "researcher",
                    "architect",
                    "creative",
                    "skeptic",
                ],
                "agent_templates": {
                    "researcher": {
                        "role": "Deep investigation and analysis",
                        "capabilities": ["analysis", "research", "documentation"],
                    },
                    "architect": {
                        "role": "System design and planning",
                        "capabilities": ["design", "planning", "architecture"],
                    },
                    "creative": {
                        "role": "Novel solutions and ideation",
                        "capabilities": ["ideation", "innovation", "problem_solving"],
                    },
                    "skeptic": {
                        "role": "Quality assurance and testing",
                        "capabilities": ["testing", "qa", "critical_analysis"],
                    },
                },
            }
            self.agent_registry.write_text(json.dumps(registry, indent=2))

    def _load_blackboard(self) -> Dict[str, Any]:
        """Load current blackboard state."""
        return json.loads(self.blackboard_file.read_text())

    def _save_blackboard(self, data: Dict[str, Any]):
        """Save blackboard state."""
        data["timestamp"] = datetime.now().isoformat()
        self.blackboard_file.write_text(json.dumps(data, indent=2))

    def _log_event(self, event_type: str, details: Dict[str, Any]):
        """Log event to event chronicle."""
        timestamp = datetime.now().isoformat()
        log_entry = f"\n## {timestamp} - {event_type}\n\n"
        for key, value in details.items():
            log_entry += f"- **{key}:** {value}\n"
        log_entry += "\n---\n"

        with open(self.event_chronicle, "a") as f:
            f.write(log_entry)

    def create_mission(self, mission_config: str) -> str:
        """Create a new mission from JSON config."""
        try:
            config = json.loads(mission_config)
        except json.JSONDecodeError:
            raise ValueError("Invalid mission configuration JSON")

        # Generate mission ID
        mission_id = f"mission-{int(time.time())}"

        # Validate mission structure
        required_fields = ["mission_name", "objective", "agents"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        # Create mission file
        mission_data = {
            "mission_id": mission_id,
            "created_at": datetime.now().isoformat(),
            "status": "ready",
            "config": config,
            "coordination": {
                "heartbeat_interval": self.HEARTBEAT_INTERVAL,
                "max_stale_time": self.MAX_STALE_TIME,
                "communication_protocol": "blackboard",
                "failure_recovery": "automatic",
            },
        }

        mission_file = self.missions_dir / f"{mission_id}.json"
        mission_file.write_text(json.dumps(mission_data, indent=2))

        # Log mission creation
        self._log_event(
            "MISSION_CREATED",
            {
                "mission_id": mission_id,
                "mission_name": config.get("mission_name", "Unnamed"),
                "agents_count": len(config.get("agents", [])),
                "objective": config.get("objective", "No objective specified"),
            },
        )

        return mission_id

    def launch_mission(self, mission_id: str) -> bool:
        """Launch a mission and initialize agents."""
        mission_file = self.missions_dir / f"{mission_id}.json"
        if not mission_file.exists():
            print(f"Mission {mission_id} not found")
            return False

        mission_data = json.loads(mission_file.read_text())
        config = mission_data["config"]

        # Update blackboard
        blackboard = self._load_blackboard()
        blackboard["mission"] = config["mission_name"]
        blackboard["mission_id"] = mission_id
        blackboard["swarm_status"] = "launching"
        blackboard["agents"] = {}

        # Initialize agents
        agents = config.get("agents", [])
        for agent_config in agents:
            agent_id = agent_config["id"]
            agent_data = {
                "type": agent_config.get("type", "researcher"),
                "role": agent_config.get("role", "Agent"),
                "task": agent_config.get("task", "No task specified"),
                "status": "launching",  # ELF lifecycle: launching → active → completing → completed/failed
                "progress": 0,
                "last_seen": datetime.now().isoformat(),
                "error": None,
                "heartbeat_interval": self.HEARTBEAT_INTERVAL,
                "created_at": datetime.now().isoformat(),
            }
            blackboard["agents"][agent_id] = agent_data

        # Update mission status
        mission_data["status"] = "launching"
        mission_data["launched_at"] = datetime.now().isoformat()
        mission_file.write_text(json.dumps(mission_data, indent=2))

        self._save_blackboard(blackboard)

        # Log mission launch
        self._log_event(
            "MISSION_LAUNCHED",
            {
                "mission_id": mission_id,
                "mission_name": config["mission_name"],
                "agents_launched": len(agents),
                "swarm_status": "launching",
            },
        )

        return True

    def monitor_and_recover(self) -> Dict[str, Any]:
        """Monitor agents and perform automatic recovery."""
        blackboard = self._load_blackboard()
        agents = blackboard.get("agents", {})
        current_time = datetime.now()

        recovery_actions = []
        stale_agents = []
        active_agents = []
        completed_agents = []
        failed_agents = []

        # Check each agent
        for agent_id, agent in agents.items():
            last_seen = datetime.fromisoformat(agent["last_seen"])
            age_seconds = (current_time - last_seen).total_seconds()

            agent_status = agent.get("status", "unknown")

            # Categorize agents
            if agent_status in ["completed", "failed"]:
                if agent_status == "completed":
                    completed_agents.append(agent_id)
                else:
                    failed_agents.append(agent_id)
            elif age_seconds > self.MAX_STALE_TIME:
                stale_agents.append(agent_id)
                # Automatic recovery for stale agents
                if agent_status != "restarting":
                    agent["status"] = "restarting"
                    agent["last_seen"] = current_time.isoformat()
                    recovery_actions.append(f"Restarted stale agent {agent_id}")
            elif agent_status == "launching" and age_seconds > 60:
                # Agents stuck in launching for too long
                agent["status"] = "restarting"
                recovery_actions.append(f"Restarted stuck agent {agent_id}")
            elif agent_status == "active":
                active_agents.append(agent_id)

        # Update swarm status based on agent states
        total_agents = len(agents)
        if total_agents == 0:
            swarm_status = "idle"
        elif len(completed_agents) + len(failed_agents) == total_agents:
            swarm_status = "completed"
        elif len(active_agents) > 0:
            swarm_status = "active"
        else:
            swarm_status = "launching"

        # Update blackboard
        blackboard["swarm_status"] = swarm_status
        blackboard["issues"] = [
            {"agent": agent, "issue": "stale"} for agent in stale_agents
        ]
        self._save_blackboard(blackboard)

        # Prepare report
        report = {
            "timestamp": current_time.isoformat(),
            "swarm_status": swarm_status,
            "agents": {
                "total": total_agents,
                "active": len(active_agents),
                "stale": len(stale_agents),
                "completed": len(completed_agents),
                "failed": len(failed_agents),
                "recovery_actions": recovery_actions,
            },
        }

        # Log if recovery actions taken
        if recovery_actions:
            self._log_event(
                "AUTOMATIC_RECOVERY",
                {"actions_count": len(recovery_actions), "actions": recovery_actions},
            )

        return report

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        blackboard = self._load_blackboard()
        agents = blackboard.get("agents", {})

        # Count agents by status
        status_counts = {}
        for agent in agents.values():
            status = agent.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Get mission info
        mission_info = None
        mission_id = blackboard.get("mission_id")
        if mission_id:
            mission_file = self.missions_dir / f"{mission_id}.json"
            if mission_file.exists():
                mission_info = json.loads(mission_file.read_text())

        return {
            "system_status": blackboard.get("system_status", "unknown"),
            "swarm_status": blackboard.get("swarm_status", "idle"),
            "current_mission": blackboard.get("mission"),
            "mission_id": mission_id,
            "agents_summary": status_counts,
            "agents_detail": agents,
            "mission_info": mission_info,
            "coordination": blackboard.get("coordination", {}),
            "issues": blackboard.get("issues", []),
        }

    def stop_mission(self, mission_id: str) -> bool:
        """Stop a specific mission."""
        mission_file = self.missions_dir / f"{mission_id}.json"
        if not mission_file.exists():
            return False

        mission_data = json.loads(mission_file.read_text())
        mission_data["status"] = "stopped"
        mission_data["stopped_at"] = datetime.now().isoformat()
        mission_file.write_text(json.dumps(mission_data, indent=2))

        # Clear blackboard if this is the current mission
        blackboard = self._load_blackboard()
        if blackboard.get("mission_id") == mission_id:
            blackboard["swarm_status"] = "idle"
            blackboard["mission"] = None
            blackboard["mission_id"] = None
            blackboard["agents"] = {}
            self._save_blackboard(blackboard)

        self._log_event(
            "MISSION_STOPPED",
            {
                "mission_id": mission_id,
                "mission_name": mission_data["config"]["mission_name"],
            },
        )

        return True

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        status = self.get_status()

        health_issues = []

        # Check coordination directory
        if not self.coordination_dir.exists():
            health_issues.append("Coordination directory missing")

        # Check blackboard integrity
        try:
            blackboard = self._load_blackboard()
            required_keys = ["timestamp", "agents", "coordination"]
            for key in required_keys:
                if key not in blackboard:
                    health_issues.append(f"Blackboard missing key: {key}")
        except Exception as e:
            health_issues.append(f"Blackboard corruption: {e}")

        # Check agent registry
        try:
            if not self.agent_registry.exists():
                health_issues.append("Agent registry missing")
        except Exception as e:
            health_issues.append(f"Agent registry error: {e}")

        # Check mission directory
        try:
            if not self.missions_dir.exists():
                health_issues.append("Missions directory missing")
        except Exception as e:
            health_issues.append(f"Missions directory error: {e}")

        # System status
        overall_health = "HEALTHY" if not health_issues else "ISSUES_DETECTED"

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "health_issues": health_issues,
            "system_status": status,
        }


def main():
    parser = argparse.ArgumentParser(description="ELF Coordinator System")
    parser.add_argument(
        "command",
        choices=[
            "status",
            "create-mission",
            "launch-mission",
            "monitor",
            "stop-mission",
            "health-check",
        ],
    )
    parser.add_argument("--mission", help="Mission ID or JSON config")

    args = parser.parse_args()

    coordinator = ELFCoordinator()

    if args.command == "status":
        status = coordinator.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "create-mission":
        if not args.mission:
            print("Error: --mission with JSON config required")
            sys.exit(1)
        mission_id = coordinator.create_mission(args.mission)
        print(f"Mission created: {mission_id}")

    elif args.command == "launch-mission":
        if not args.mission:
            print("Error: --mission with mission ID required")
            sys.exit(1)
        success = coordinator.launch_mission(args.mission)
        if success:
            print(f"Mission {args.mission} launched")
        else:
            print(f"Failed to launch mission {args.mission}")
            sys.exit(1)

    elif args.command == "monitor":
        report = coordinator.monitor_and_recover()
        print(json.dumps(report, indent=2))

    elif args.command == "stop-mission":
        if not args.mission:
            print("Error: --mission with mission ID required")
            sys.exit(1)
        success = coordinator.stop_mission(args.mission)
        if success:
            print(f"Mission {args.mission} stopped")
        else:
            print(f"Failed to stop mission {args.mission}")
            sys.exit(1)

    elif args.command == "health-check":
        health = coordinator.health_check()
        print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()
