#!/usr/bin/env python3
"""
Swarm CLI - Command-line interface for ELF swarm execution.

Usage:
    python swarm_cli.py run --task "Analyze authentication system"
    python swarm_cli.py run --task "Find security vulnerabilities" --mode analysis
    python swarm_cli.py run --task "Design new API" --agents architect creative skeptic
    python swarm_cli.py status
    python swarm_cli.py agents
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coordinator.swarm_controller import SwarmController, SWARM_MODES, AGENT_ROLES


def cmd_run(args):
    controller = SwarmController(max_workers=args.workers, timeout=args.timeout)
    custom_agents = args.agents if args.agents else None

    result = controller.execute_swarm(
        task_description=args.task,
        mode=args.mode,
        custom_agents=custom_agents,
    )

    if args.json_output:
        for agent_result in result.get("agent_results", {}).values():
            if "response" in agent_result:
                agent_result["response_length"] = len(agent_result["response"])
                agent_result["response"] = agent_result["response"][:200] + "..."
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\nTask: {result['task']}")
        print(f"Status: {result['status']}")
        print(f"Completed: {result.get('completed_count', 0)}/{result.get('total_count', 0)}")
        print(f"Learnings: {result.get('total_learnings', 0)}")

        if result.get("all_learnings"):
            print("\nExtracted Learnings:")
            for i, learning in enumerate(result["all_learnings"], 1):
                print(f"  {i}. [{learning['domain']}] {learning['lesson'][:100]}")

        for agent_name, agent_result in result.get("agent_results", {}).items():
            print(f"\n--- {agent_name} ({agent_result['status']}) ---")
            if agent_result.get("response"):
                print(agent_result["response"][:500])
                if len(agent_result.get("response", "")) > 500:
                    print(f"  ... ({len(agent_result['response'])} chars total)")
            elif agent_result.get("error"):
                print(f"  Error: {agent_result['error']}")


def cmd_status(args):
    try:
        from Open_ELF.core.coordination import get_coordination_store
        store = get_coordination_store()
    except ImportError:
        from core.coordination import get_coordination_store
        store = get_coordination_store()

    agents = store.get_all_agents()
    tasks = store.get_active_tasks()

    print("ELF Coordination Status")
    print("=" * 40)

    print(f"\nRegistered Agents ({len(agents)}):")
    for agent in agents:
        icon = {"active": "+", "stale": "?", "stopped": "-"}.get(agent["status"], "?")
        print(f"  [{icon}] {agent['name']} (pid:{agent['pid']}, {agent['status']})")
        print(f"      Last heartbeat: {agent['last_heartbeat']}")

    print(f"\nActive Tasks ({len(tasks)}):")
    for task in tasks:
        print(f"  [{task['state']}] {task['id']} (owner: {task['owner']})")
    if not tasks:
        print("  No active tasks")


def cmd_agents(args):
    print("Available Swarm Agents:")
    print("=" * 40)
    for name, info in AGENT_ROLES.items():
        print(f"\n  {name}:")
        print(f"    Role: {info['role']}")
        print(f"    Perspective: {info['perspective']}")

    print("\n\nSwarm Modes:")
    for mode, agents in SWARM_MODES.items():
        print(f"  {mode}: {', '.join(agents)}")


def main():
    parser = argparse.ArgumentParser(description="ELF Swarm CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    run_parser = subparsers.add_parser("run", help="Execute a swarm task")
    run_parser.add_argument("--task", "-t", required=True, help="Task description")
    run_parser.add_argument("--mode", "-m", default="all", choices=list(SWARM_MODES.keys()))
    run_parser.add_argument("--agents", "-a", nargs="+", choices=list(AGENT_ROLES.keys()))
    run_parser.add_argument("--workers", "-w", type=int, default=4)
    run_parser.add_argument("--timeout", type=int, default=120)
    run_parser.add_argument("--json", dest="json_output", action="store_true")

    subparsers.add_parser("status", help="Show coordination status")
    subparsers.add_parser("agents", help="List available agents")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "agents":
        cmd_agents(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
