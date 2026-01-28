#!/usr/bin/env python3
"""
ELF Agent Registry and Lifecycle Manager

Handles agent registration, status tracking, and lifecycle compliance.
Enforces ELF standards for agent behavior and coordination.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent))

from coordinator import ELFCoordinator


class AgentRegistry:
    """Registry for managing agent lifecycle and compliance."""

    def __init__(self):
        self.coordinator = ELFCoordinator()
        self.registry_file = self.coordinator.agent_registry
        self.blackboard_file = self.coordinator.blackboard_file

    def register_agent(self, agent_config: Dict[str, Any]) -> str:
        """Register a new agent with ELF compliance check."""
        required_fields = ["id", "type", "role", "capabilities"]
        for field in required_fields:
            if field not in agent_config:
                raise ValueError(f"Agent missing required field: {field}")

        # Validate agent type
        registry = self._load_registry()
        available_personas = registry.get("available_personas", [])
        if agent_config["type"] not in available_personas:
            raise ValueError(f"Unknown agent type: {agent_config['type']}")

        # Register agent
        agent_id = agent_config["id"]
        registration_time = datetime.now().isoformat()

        agent_data = {
            "id": agent_id,
            "type": agent_config["type"],
            "role": agent_config["role"],
            "capabilities": agent_config["capabilities"],
            "registered_at": registration_time,
            "status": "registered",
            "heartbeat_interval": self.coordinator.HEARTBEAT_INTERVAL,
            "compliance_status": "compliant",
            "missions_completed": 0,
            "last_mission": None,
        }

        registry["registered_agents"][agent_id] = agent_data
        self._save_registry(registry)

        # Log registration
        self.coordinator._log_event(
            "AGENT_REGISTERED",
            {
                "agent_id": agent_id,
                "type": agent_config["type"],
                "role": agent_config["role"],
                "capabilities": ", ".join(agent_config["capabilities"]),
            },
        )

        return agent_id

    def update_agent_status(
        self, agent_id: str, status: str, details: Dict[str, Any] = None
    ):
        """Update agent status following ELF lifecycle."""
        valid_statuses = [
            "registered",
            "launching",
            "active",
            "completing",
            "completed",
            "failed",
            "restarting",
            "offline",
        ]

        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Valid: {valid_statuses}")

        registry = self._load_registry()
        if agent_id not in registry["registered_agents"]:
            raise ValueError(f"Agent {agent_id} not registered")

        old_status = registry["registered_agents"][agent_id]["status"]
        registry["registered_agents"][agent_id]["status"] = status
        registry["registered_agents"][agent_id]["status_updated"] = (
            datetime.now().isoformat()
        )

        if details:
            for key, value in details.items():
                registry["registered_agents"][agent_id][key] = value

        # Validate status transitions
        transition_valid = self._validate_status_transition(old_status, status)
        if not transition_valid:
            registry["registered_agents"][agent_id]["compliance_status"] = (
                "non_compliant"
            )
            registry["registered_agents"][agent_id]["violation"] = (
                f"Invalid transition: {old_status} → {status}"
            )
        else:
            registry["registered_agents"][agent_id]["compliance_status"] = "compliant"
            if "violation" in registry["registered_agents"][agent_id]:
                del registry["registered_agents"][agent_id]["violation"]

        self._save_registry(registry)

        # Log status change
        self.coordinator._log_event(
            "AGENT_STATUS_CHANGED",
            {
                "agent_id": agent_id,
                "old_status": old_status,
                "new_status": status,
                "compliant": transition_valid,
            },
        )

    def update_heartbeat(self, agent_id: str, progress: int = None, status: str = None):
        """Update agent heartbeat timestamp."""
        registry = self._load_registry()
        if agent_id not in registry["registered_agents"]:
            raise ValueError(f"Agent {agent_id} not registered")

        agent_data = registry["registered_agents"][agent_id]
        agent_data["last_heartbeat"] = datetime.now().isoformat()

        if progress is not None:
            agent_data["progress"] = progress
        if status:
            self.update_agent_status(agent_id, status)

        self._save_registry(registry)

    def check_compliance(self, agent_id: str) -> Dict[str, Any]:
        """Check agent compliance with ELF standards."""
        registry = self._load_registry()
        if agent_id not in registry["registered_agents"]:
            raise ValueError(f"Agent {agent_id} not registered")

        agent = registry["registered_agents"][agent_id]
        issues = []

        # Check heartbeat compliance
        last_heartbeat = agent.get("last_heartbeat", agent.get("registered_at", ""))
        if last_heartbeat:
            last_time = datetime.fromisoformat(last_heartbeat)
            age_seconds = (datetime.now() - last_time).total_seconds()
            if age_seconds > self.coordinator.MAX_STALE_TIME:
                issues.append(f"Heartbeat stale: {age_seconds}s old")

        # Check status compliance
        current_status = agent.get("status", "unknown")
        if current_status in ["launching", "restarting"]:
            launch_time = datetime.fromisoformat(
                agent.get("status_updated", last_heartbeat)
            )
            stuck_time = (datetime.now() - launch_time).total_seconds()
            if stuck_time > 300:  # 5 minutes
                issues.append(f"Stuck in status {current_status} for {stuck_time}s")

        # Update compliance status
        agent["compliance_status"] = "compliant" if not issues else "non_compliant"
        agent["compliance_issues"] = issues

        self._save_registry(registry)

        return {
            "agent_id": agent_id,
            "compliance_status": agent["compliance_status"],
            "issues": issues,
            "last_heartbeat": last_heartbeat,
            "current_status": current_status,
        }

    def get_available_agents(self, agent_type: str = None) -> List[Dict[str, Any]]:
        """Get list of available agents for mission assignment."""
        registry = self._load_registry()
        available_agents = []

        for agent_id, agent_data in registry["registered_agents"].items():
            if agent_data.get("status") in ["registered", "completed", "offline"]:
                if agent_type is None or agent_data["type"] == agent_type:
                    available_agents.append(agent_data)

        return available_agents

    def retire_agent(self, agent_id: str) -> bool:
        """Retire an agent from service."""
        registry = self._load_registry()
        if agent_id not in registry["registered_agents"]:
            return False

        agent_data = registry["registered_agents"][agent_id]
        agent_data["status"] = "retired"
        agent_data["retired_at"] = datetime.now().isoformat()

        self._save_registry(registry)

        # Log retirement
        self.coordinator._log_event(
            "AGENT_RETIRED",
            {
                "agent_id": agent_id,
                "type": agent_data["type"],
                "missions_completed": agent_data.get("missions_completed", 0),
            },
        )

        return True

    def _validate_status_transition(self, old_status: str, new_status: str) -> bool:
        """Validate ELF agent lifecycle transitions."""
        valid_transitions = {
            "registered": ["launching"],
            "launching": ["active", "restarting", "failed"],
            "active": ["completing", "restarting", "failed"],
            "completing": ["completed", "failed"],
            "completed": ["registered", "offline"],
            "failed": ["restarting", "offline"],
            "restarting": ["launching", "failed"],
            "offline": ["registered", "retired"],
        }

        return new_status in valid_transitions.get(old_status, [])

    def _load_registry(self) -> Dict[str, Any]:
        """Load agent registry."""
        return json.loads(self.registry_file.read_text())

    def _save_registry(self, registry: Dict[str, Any]):
        """Save agent registry."""
        registry["timestamp"] = datetime.now().isoformat()
        self.registry_file.write_text(json.dumps(registry, indent=2))

    def generate_agent_report(self) -> Dict[str, Any]:
        """Generate comprehensive agent status report."""
        registry = self._load_registry()
        agents = registry["registered_agents"]

        # Summary statistics
        status_counts = {}
        type_counts = {}
        compliance_counts = {"compliant": 0, "non_compliant": 0}

        for agent in agents.values():
            # Status counts
            status = agent.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            # Type counts
            agent_type = agent.get("type", "unknown")
            type_counts[agent_type] = type_counts.get(agent_type, 0) + 1

            # Compliance counts
            compliance = agent.get("compliance_status", "unknown")
            if compliance in compliance_counts:
                compliance_counts[compliance] += 1

        # Detailed agent list
        agent_details = []
        for agent_id, agent_data in agents.items():
            agent_details.append(
                {
                    "id": agent_id,
                    "type": agent_data.get("type", "unknown"),
                    "status": agent_data.get("status", "unknown"),
                    "compliance": agent_data.get("compliance_status", "unknown"),
                    "last_heartbeat": agent_data.get("last_heartbeat", "never"),
                    "missions_completed": agent_data.get("missions_completed", 0),
                }
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_agents": len(agents),
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "compliance_distribution": compliance_counts,
            },
            "agents": agent_details,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ELF Agent Registry")
    parser.add_argument(
        "command",
        choices=[
            "register",
            "update-status",
            "heartbeat",
            "check-compliance",
            "list-available",
            "retire",
            "report",
        ],
    )
    parser.add_argument("--agent-id", help="Agent ID")
    parser.add_argument("--type", help="Agent type")
    parser.add_argument("--status", help="Agent status")
    parser.add_argument("--progress", type=int, help="Agent progress percentage")
    parser.add_argument("--config", help="Agent configuration JSON")

    args = parser.parse_args()

    registry = AgentRegistry()

    if args.command == "register":
        if not args.config:
            print("Error: --config with JSON agent configuration required")
            sys.exit(1)

        try:
            agent_config = json.loads(args.config)
            agent_id = registry.register_agent(agent_config)
            print(f"Agent registered: {agent_id}")
        except Exception as e:
            print(f"Error registering agent: {e}")
            sys.exit(1)

    elif args.command == "update-status":
        if not args.agent_id or not args.status:
            print("Error: --agent-id and --status required")
            sys.exit(1)

        try:
            registry.update_agent_status(args.agent_id, args.status)
            print(f"Agent {args.agent_id} status updated to {args.status}")
        except Exception as e:
            print(f"Error updating status: {e}")
            sys.exit(1)

    elif args.command == "heartbeat":
        if not args.agent_id:
            print("Error: --agent-id required")
            sys.exit(1)

        try:
            registry.update_heartbeat(args.agent_id, args.progress, args.status)
            print(f"Heartbeat updated for agent {args.agent_id}")
        except Exception as e:
            print(f"Error updating heartbeat: {e}")
            sys.exit(1)

    elif args.command == "check-compliance":
        if not args.agent_id:
            print("Error: --agent-id required")
            sys.exit(1)

        try:
            compliance = registry.check_compliance(args.agent_id)
            print(json.dumps(compliance, indent=2))
        except Exception as e:
            print(f"Error checking compliance: {e}")
            sys.exit(1)

    elif args.command == "list-available":
        try:
            agents = registry.get_available_agents(args.type)
            for agent in agents:
                print(
                    f"{agent['id']} - {agent['type']} - {agent['role']} ({agent['status']})"
                )
        except Exception as e:
            print(f"Error listing agents: {e}")
            sys.exit(1)

    elif args.command == "retire":
        if not args.agent_id:
            print("Error: --agent-id required")
            sys.exit(1)

        try:
            success = registry.retire_agent(args.agent_id)
            if success:
                print(f"Agent {args.agent_id} retired")
            else:
                print(f"Agent {args.agent_id} not found")
                sys.exit(1)
        except Exception as e:
            print(f"Error retiring agent: {e}")
            sys.exit(1)

    elif args.command == "report":
        try:
            report = registry.generate_agent_report()
            print(json.dumps(report, indent=2))
        except Exception as e:
            print(f"Error generating report: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
