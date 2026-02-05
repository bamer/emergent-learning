#!/usr/bin/env python3
"""
TIER 1 Watcher Agent - Fast Monitoring Check
Monitors multi-agent swarm coordination state
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path


def load_coordination_state():
    """Load the coordination state from .coordination/"""
    # Load coordination state
    state_file = Path(".coordination/coordination-state.json")
    if not state_file.exists():
        return {"error": "Coordination state file not found"}

    try:
        with open(state_file, "r") as f:
            coord_state = json.load(f)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in coordination state: {e}"}
    except Exception as e:
        return {"error": f"Failed to read coordination state: {e}"}

    # Load blackboard data
    blackboard_file = Path(".coordination/blackboard.json")
    if blackboard_file.exists():
        try:
            with open(blackboard_file, "r") as f:
                blackboard = json.load(f)
            # Merge blackboard data into coordination state
            coord_state["blackboard"] = blackboard
        except Exception as e:
            coord_state["blackboard_error"] = str(e)

    return coord_state


def check_agent_heartbeats(coordination_data):
    """Check for stale agents (no heartbeat > 120s)"""
    issues = []
    blackboard = coordination_data.get("blackboard", {})
    agents = blackboard.get("agents", {})

    if not agents:
        return {"status": "no_agents", "message": "No active agents"}

    now = datetime.now()
    stale_threshold = timedelta(seconds=120)

    for agent_id, agent_data in agents.items():
        if "heartbeat" in agent_data:
            try:
                heartbeat_time = datetime.fromisoformat(agent_data["heartbeat"])
                if now - heartbeat_time > stale_threshold:
                    issues.append(
                        {
                            "agent": agent_id,
                            "issue": "stale",
                            "last_heartbeat": agent_data["heartbeat"],
                            "stale_seconds": (now - heartbeat_time).total_seconds(),
                        }
                    )
            except ValueError:
                issues.append(
                    {
                        "agent": agent_id,
                        "issue": "invalid_heartbeat",
                        "heartbeat": agent_data["heartbeat"],
                    }
                )
        else:
            issues.append({"agent": agent_id, "issue": "no_heartbeat"})

    return {"status": "checked", "issues": issues}


def check_errors(coordination_data):
    """Check for errors in blackboard"""
    errors = []

    # Check for error in coordination data itself
    if "error" in coordination_data:
        errors.append(
            {"type": "coordination_error", "message": coordination_data["error"]}
        )

    # Check blackboard for errors
    blackboard = coordination_data.get("blackboard", {})
    if "error" in blackboard:
        errors.append({"type": "blackboard_error", "message": blackboard["error"]})

    # Check for agents with errors
    agents = blackboard.get("agents", {})
    for agent_id, agent_data in agents.items():
        if agent_data.get("status") == "error":
            errors.append(
                {
                    "type": "agent_error",
                    "agent": agent_id,
                    "message": agent_data.get("error_message", "Unknown error"),
                }
            )

    return errors


def check_stuck_tasks(coordination_data):
    """Check for stuck tasks"""
    stuck_tasks = []
    blackboard = coordination_data.get("blackboard", {})

    # Check if there's a task running and if it's been too long
    if blackboard.get("status") == "running":
        # Look for tasks without recent updates
        agent_files = coordination_data.get("agent_files", [])
        for agent_file in agent_files:
            if "task" in agent_file and agent_file.get("status") == "running":
                # Simple check - if task has been running > 10 minutes, consider it stuck
                if "started_at" in agent_file:
                    try:
                        started_time = datetime.fromisoformat(agent_file["started_at"])
                        if datetime.now() - started_time > timedelta(minutes=10):
                            stuck_tasks.append(
                                {
                                    "task": agent_file.get("task", "unknown"),
                                    "agent": agent_file.get("agent", "unknown"),
                                    "stuck_minutes": (
                                        datetime.now() - started_time
                                    ).total_seconds()
                                    / 60,
                                }
                            )
                    except ValueError:
                        stuck_tasks.append(
                            {
                                "task": agent_file.get("task", "unknown"),
                                "agent": agent_file.get("agent", "unknown"),
                                "issue": "invalid_timestamp",
                            }
                        )

    return stuck_tasks


def determine_overall_status(heartbeat_check, errors, stuck_tasks):
    """Determine overall swarm status"""
    if errors:
        return "error"
    if stuck_tasks:
        return "stale"  # stuck tasks count as stale
    if heartbeat_check.get("status") == "no_agents":
        return "nominal"
    if heartbeat_check.get("issues"):
        return "stale"
    return "nominal"


def take_corrective_actions(status, heartbeat_check, errors, stuck_tasks):
    """Take basic corrective actions if needed"""
    actions = []

    if status == "error":
        # Log error details
        for error in errors:
            actions.append(f"LOG_ERROR: {error['type']} - {error['message']}")

    if status == "stale":
        # Log stale agents/tasks
        for issue in heartbeat_check.get("issues", []):
            actions.append(f"LOG_STALE: Agent {issue['agent']} - {issue['issue']}")

        for task in stuck_tasks:
            actions.append(
                f"LOG_STUCK: Task {task['task']} on agent {task['agent']} stuck for {task.get('stuck_minutes', 0):.1f} minutes"
            )

    return actions


def log_findings(
    status, coordination_data, heartbeat_check, errors, stuck_tasks, actions
):
    """Log findings to watcher-log.md"""
    log_entry = f"""# Swarm Watcher Check - {datetime.now().isoformat()}

## Status: {status.upper()}

## Coordination State
- Blackboard Status: {coordination_data.get("blackboard", {}).get("status", "unknown")}
- Active Agents: {len(coordination_data.get("blackboard", {}).get("agents", {}))}
- Stop Requested: {coordination_data.get("stop_requested", False)}

## Heartbeat Check
{json.dumps(heartbeat_check, indent=2)}

## Errors Found
{json.dumps(errors, indent=2) if errors else "None"}

## Stuck Tasks
{json.dumps(stuck_tasks, indent=2) if stuck_tasks else "None"}

## Actions Taken
{chr(10).join(actions) if actions else "None"}

---
"""

    log_file = Path("watcher-log.md")
    try:
        with open(log_file, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write log: {e}", file=sys.stderr)


def main():
    """Main monitoring check"""
    # Load coordination state
    coordination_data = load_coordination_state()

    if "error" in coordination_data:
        print(f"ERROR: {coordination_data['error']}", file=sys.stderr)
        sys.exit(1)  # Escalate due to error

    # Perform checks
    heartbeat_check = check_agent_heartbeats(coordination_data)
    errors = check_errors(coordination_data)
    stuck_tasks = check_stuck_tasks(coordination_data)

    # Determine status
    status = determine_overall_status(heartbeat_check, errors, stuck_tasks)

    # Take corrective actions
    actions = take_corrective_actions(status, heartbeat_check, errors, stuck_tasks)

    # Log findings
    log_findings(
        status, coordination_data, heartbeat_check, errors, stuck_tasks, actions
    )

    # Output summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "active_agents": len(coordination_data.get("blackboard", {}).get("agents", {})),
        "errors_found": len(errors),
        "stale_agents": len(
            [i for i in heartbeat_check.get("issues", []) if i.get("issue") == "stale"]
        ),
        "stuck_tasks": len(stuck_tasks),
        "actions_taken": len(actions),
    }

    print(f"SUMMARY: {json.dumps(summary)}")

    # Exit code: 0 = check again in 30s, 1 = escalate
    if status == "nominal":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
