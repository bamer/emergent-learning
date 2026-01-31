"""
OpenCode Swarm Manager
======================

Manages OpenCode agent swarms for complex multi-agent tasks.
OpenCode agents are prompt-based personas (not processes like ELF agents).

Available OpenCode agents (from ~/.config/opencode/agents/):
- architect: System design and structure
- researcher: Investigation and evidence gathering
- skeptic: Critical analysis and risk identification
- creative: Innovation and possibilities
- learning-extractor: Meta-learning and insights
- ceo: Executive decisions and strategic direction
- multi-agent-coordinator: Complex workflow orchestration

Usage:
    from opencode_swarm import OpenCodeSwarmManager, SwarmMode

    manager = OpenCodeSwarmManager()
    result = manager.run_swarm(
        task="Analyze this codebase",
        mode=SwarmMode.ANALYSIS
    )
"""

import json
import os
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

# OpenCode agents directory
OPENCODE_AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"


class SwarmMode(Enum):
    """Predefined swarm configurations for different task types."""

    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    LEARNING = "learning"
    ALL = "all"


# Agent sequences for each mode
SWARM_SEQUENCES = {
    SwarmMode.ANALYSIS: ["researcher", "architect"],
    SwarmMode.DESIGN: ["architect", "creative", "skeptic"],
    SwarmMode.IMPLEMENTATION: ["architect", "researcher", "skeptic"],
    SwarmMode.LEARNING: ["learning-extractor", "researcher", "architect"],
    SwarmMode.ALL: [
        "researcher",
        "architect",
        "skeptic",
        "creative",
        "learning-extractor",
    ],
}


class OpenCodeSwarmManager:
    """
    Manages OpenCode agent swarms.

    Unlike ELF agents (which are Python processes), OpenCode agents are
    prompt-based personas used by the AI model (Claude, etc.).
    """

    def __init__(self):
        self.agents_dir = OPENCODE_AGENTS_DIR
        self.available_agents = self._discover_agents()

    def _discover_agents(self) -> Dict[str, Dict[str, Any]]:
        """Discover available OpenCode agents from the agents directory."""
        agents = {}

        if not self.agents_dir.exists():
            return agents

        for agent_file in self.agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            try:
                content = agent_file.read_text()
                # Parse frontmatter if present
                if content.startswith("---"):
                    lines = content.split("\n")
                    frontmatter = {}
                    in_frontmatter = False
                    for line in lines[1:]:
                        if line.startswith("---"):
                            break
                        if ":" in line:
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()

                    agents[agent_name] = {
                        "name": frontmatter.get("name", agent_name),
                        "description": frontmatter.get("description", ""),
                        "file": str(agent_file),
                    }
                else:
                    agents[agent_name] = {
                        "name": agent_name,
                        "description": "",
                        "file": str(agent_file),
                    }
            except Exception as e:
                print(f"Error reading agent {agent_name}: {e}")

        return agents

    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available OpenCode agents."""
        return [
            {"id": key, "name": info["name"], "description": info["description"]}
            for key, info in self.available_agents.items()
        ]

    def run_swarm(
        self,
        task: str,
        context: str = "",
        mode: SwarmMode = SwarmMode.ALL,
        custom_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run a swarm of OpenCode agents on a task.

        Args:
            task: Main task description
            context: Optional additional context
            mode: Swarm mode (analysis, design, implementation, learning, all)
            custom_agents: Optional list of specific agents to use (overrides mode)

        Returns:
            Dictionary with swarm results
        """
        results = {
            "task": task,
            "context": context,
            "mode": mode.value,
            "timestamp": datetime.now().isoformat(),
            "agents": [],
            "status": "initialized",
        }

        # Determine agent sequence
        if custom_agents:
            agent_sequence = custom_agents
        else:
            agent_sequence = SWARM_SEQUENCES.get(mode, SWARM_SEQUENCES[SwarmMode.ALL])

        # Validate agents
        valid_agents = []
        for agent_name in agent_sequence:
            if agent_name in self.available_agents:
                valid_agents.append(agent_name)
            else:
                results["agents"].append(
                    {
                        "name": agent_name,
                        "status": "skipped",
                        "reason": "Agent not found",
                    }
                )

        if not valid_agents:
            results["status"] = "failed"
            results["error"] = "No valid agents found for swarm"
            return results

        # Load agent prompts
        for agent_name in valid_agents:
            agent_info = self.available_agents[agent_name]
            try:
                prompt_content = Path(agent_info["file"]).read_text()
                results["agents"].append(
                    {
                        "name": agent_name,
                        "display_name": agent_info["name"],
                        "status": "ready",
                        "prompt_file": agent_info["file"],
                        "prompt_length": len(prompt_content),
                    }
                )
            except Exception as e:
                results["agents"].append(
                    {
                        "name": agent_name,
                        "display_name": agent_info["name"],
                        "status": "error",
                        "error": str(e),
                    }
                )

        results["status"] = "ready"
        results["agent_count"] = len(
            [a for a in results["agents"] if a["status"] == "ready"]
        )

        return results

    def get_agent_prompt(self, agent_name: str) -> Optional[str]:
        """Get the full prompt for an OpenCode agent."""
        if agent_name not in self.available_agents:
            return None

        agent_file = Path(self.available_agents[agent_name]["file"])
        try:
            return agent_file.read_text()
        except Exception:
            return None

    def get_recommended_sequence(self, task_type: str) -> List[str]:
        """Get recommended agent sequence for a task type."""
        mode = (
            SwarmMode(task_type)
            if task_type in [m.value for m in SwarmMode]
            else SwarmMode.ALL
        )
        return SWARM_SEQUENCES.get(mode, SWARM_SEQUENCES[SwarmMode.ALL])


# Convenience functions for CLI/API usage
def list_opencode_agents() -> List[Dict[str, str]]:
    """List all available OpenCode agents."""
    manager = OpenCodeSwarmManager()
    return manager.get_available_agents()


def run_swarm_task(
    task: str,
    mode: str = "all",
    context: str = "",
) -> Dict[str, Any]:
    """Run a swarm task (convenience function)."""
    manager = OpenCodeSwarmManager()
    swarm_mode = (
        SwarmMode(mode) if mode in [m.value for m in SwarmMode] else SwarmMode.ALL
    )
    return manager.run_swarm(task=task, context=context, mode=swarm_mode)


if __name__ == "__main__":
    # Test the swarm manager
    print("OpenCode Swarm Manager Test")
    print("=" * 50)

    manager = OpenCodeSwarmManager()

    print("\nAvailable agents:")
    for agent in manager.get_available_agents():
        print(f"  - {agent['id']}: {agent['name']}")

    print("\nTest swarm (analysis mode):")
    result = manager.run_swarm(
        task="Analyze the current codebase structure", mode=SwarmMode.ANALYSIS
    )
    print(f"Status: {result['status']}")
    print(f"Agents ready: {result.get('agent_count', 0)}")
    for agent in result["agents"]:
        print(f"  - {agent['name']}: {agent['status']}")
