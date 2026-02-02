"""
Timeline Event Definitions for Dashboard Integration

Defines event types and their display properties for the timeline view.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimelineEventConfig:
    """Configuration for timeline event display"""

    icon: str
    color: str
    label: str
    description_template: str


# Event type configurations
EVENT_CONFIGS: Dict[str, TimelineEventConfig] = {
    "task_start": TimelineEventConfig(
        icon="Play",
        color="bg-sky-500",
        label="Task Started",
        description_template="Task {task_name} started",
    ),
    "task_end": TimelineEventConfig(
        icon="CheckCircle",
        color="bg-emerald-500",
        label="Task Completed",
        description_template="Task {task_name} completed",
    ),
    "heuristic_consulted": TimelineEventConfig(
        icon="Brain",
        color="bg-violet-500",
        label="Heuristic Consulted",
        description_template="Consulted heuristic: {heuristic_rule}",
    ),
    "heuristic_validated": TimelineEventConfig(
        icon="CheckCircle",
        color="bg-emerald-500",
        label="Heuristic Validated",
        description_template="Heuristic validated: {heuristic_rule}",
    ),
    "heuristic_violated": TimelineEventConfig(
        icon="XCircle",
        color="bg-red-500",
        label="Heuristic Violated",
        description_template="Heuristic violated: {heuristic_rule}",
    ),
    "failure_recorded": TimelineEventConfig(
        icon="AlertTriangle",
        color="bg-orange-500",
        label="Failure Recorded",
        description_template="Failure recorded: {failure_description}",
    ),
    "golden_promoted": TimelineEventConfig(
        icon="Star",
        color="bg-amber-500",
        label="Golden Promotion",
        description_template="Heuristic promoted to golden rule: {heuristic_rule}",
    ),
    "agent_spawned": TimelineEventConfig(
        icon="UserPlus",
        color="bg-blue-500",
        label="Agent Spawned",
        description_template="Agent {agent_name} spawned for task",
    ),
    "workflow_started": TimelineEventConfig(
        icon="Play",
        color="bg-green-500",
        label="Workflow Started",
        description_template="Workflow {workflow_name} started",
    ),
    "session_started": TimelineEventConfig(
        icon="LogIn",
        color="bg-purple-500",
        label="Session Started",
        description_template="New session started",
    ),
    "session_ended": TimelineEventConfig(
        icon="LogOut",
        color="bg-gray-500",
        label="Session Ended",
        description_template="Session ended",
    ),
}


def get_event_config(event_type: str) -> TimelineEventConfig:
    """Get configuration for an event type, with fallback for unknown types"""
    return EVENT_CONFIGS.get(
        event_type,
        TimelineEventConfig(
            icon="FileText",
            color="bg-slate-500",
            label=event_type.replace("_", " ").title(),
            description_template="{event_data}",
        ),
    )


def format_event_description(event_type: str, data: Dict[str, Any]) -> str:
    """Format event description using template and data"""
    config = get_event_config(event_type)

    # Try to format with available data
    try:
        return config.description_template.format(**data)
    except KeyError:
        # Fallback to generic description
        if "description" in data:
            return data["description"]
        elif "message" in data:
            return data["message"]
        else:
            return str(data)
