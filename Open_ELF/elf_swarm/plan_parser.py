"""
Plan Parser - Extract phases and tasks from markdown plan
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class Task:
    """Represents a task in the plan."""

    phase_num: int
    task_idx: int
    name: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3
    logs: List[str] = field(default_factory=list)
    result: str = ""
    error: str = ""


@dataclass
class Phase:
    """Represents a phase in the plan."""

    phase_num: int
    name: str
    tasks: List[Task]
    status: str = "pending"


def parse_plan(plan_content: str) -> List[Phase]:
    """
    Parse plan markdown and extract phases and tasks.

    Args:
        plan_content: Markdown content from plan.md

    Returns:
        List of Phase objects containing Tasks
    """
    import re

    phases = []
    current_phase = None
    phase_pattern = r"## Phase (\d+): (.+)"
    task_pattern = r"### Task (\d+\.\d+): (.+)"

    lines = plan_content.split("\n")

    for line in lines:
        line = line.strip()

        # Check for phase header
        phase_match = re.match(phase_pattern, line)
        if phase_match:
            phase_num = int(phase_match.group(1))
            phase_name = phase_match.group(2).strip()

            # Save previous phase
            if current_phase:
                phases.append(current_phase)

            # Start new phase
            current_phase = Phase(phase_num=phase_num, name=phase_name, tasks=[])
            continue

        # Check for task header
        task_match = re.match(task_pattern, line)
        if task_match and current_phase:
            task_id = task_match.group(1)
            task_name = task_match.group(2).strip()

            # Start new task
            current_task = Task(
                phase_num=current_phase.phase_num,
                task_idx=len(current_phase.tasks) + 1,
                name=task_name,
                description=task_name,
                acceptance_criteria=[],
                dependencies=[],
            )
            current_phase.tasks.append(current_task)
            current_phase.tasks.sort(key=lambda t: t.task_idx)
            continue

        # Extract task details (description, criteria, dependencies)
        if current_phase and current_phase.tasks:
            current_task = current_phase.tasks[-1]

            if line.startswith("- Description:"):
                current_task.description = line.replace("- Description:", "").strip()
            elif line.startswith("- Acceptance Criteria:"):
                pass
            elif line.strip().startswith("- [ ]"):
                criterion = line.strip().replace("- [ ]", "").strip()
                if criterion:
                    current_task.acceptance_criteria.append(criterion)
            elif line.startswith("- Dependencies:"):
                deps = line.replace("- Dependencies:", "").strip()
                if deps and deps.lower() != "none":
                    current_task.dependencies = [d.strip() for d in deps.split(",")]

    # Don't forget last phase
    if current_phase:
        phases.append(current_phase)

    return phases


def plan_to_dict(phases: List[Phase]) -> Dict[str, Any]:
    """Convert phases list to dictionary for JSON serialization."""
    return {
        "phases": [
            {
                "phase_num": p.phase_num,
                "name": p.name,
                "status": p.status,
                "tasks": [
                    {
                        "phase_num": t.phase_num,
                        "task_idx": t.task_idx,
                        "name": t.name,
                        "description": t.description,
                        "acceptance_criteria": t.acceptance_criteria,
                        "dependencies": t.dependencies,
                        "status": t.status,
                        "attempts": t.attempts,
                        "max_attempts": t.max_attempts,
                        "logs": t.logs,
                        "result": t.result,
                        "error": t.error,
                    }
                    for t in p.tasks
                ],
            }
            for p in phases
        ]
    }
