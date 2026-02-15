#!/usr/bin/env python3
"""
Swarm Manager - State and Plan Management
========================================

Manages swarm state, plans, and execution tracking.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class SwarmManager:
    """Manages swarm state, plans, and execution tracking."""

    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path.cwd()
        self.swarm_dir = self.work_dir / ".swarm"
        self.history_dir = self.swarm_dir / "history"

        # Ensure directories exist
        self.swarm_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def has_existing_plan(self) -> bool:
        """Check if a plan already exists."""
        return (self.swarm_dir / "plan.json").exists()

    def load_plan(self) -> Optional[Dict]:
        """Load existing plan from disk."""
        plan_file = self.swarm_dir / "plan.json"
        if not plan_file.exists():
            return None

        with open(plan_file, "r") as f:
            return json.load(f)

    def save_plan(self, plan: Dict):
        """Save plan to disk."""
        plan_file = self.swarm_dir / "plan.json"
        with open(plan_file, "w") as f:
            json.dump(plan, f, indent=2)

    def load_context(self) -> Dict:
        """Load or create context."""
        context_file = self.swarm_dir / "context.json"

        if context_file.exists():
            with open(context_file, "r") as f:
                return json.load(f)

        # Create new context
        return {
            "task": "",
            "discovery": "",
            "sme_guidance": {},
            "learnings": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def save_context(self, context: Dict):
        """Save context to disk."""
        context_file = self.swarm_dir / "context.json"
        context["updated_at"] = datetime.now().isoformat()

        with open(context_file, "w") as f:
            json.dump(context, f, indent=2)

    def create_markdown_plan(self, plan_content: str):
        """Create human-readable markdown plan."""
        plan_file = self.swarm_dir / "plan.md"
        with open(plan_file, "w") as f:
            f.write(plan_content)

    def archive_swarm(self, plan: Dict):
        """Archive the current swarm run."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = self.history_dir / f"swarm_{timestamp}.md"

        # Combine plan and context into archive
        content = f"""# Swarm Archive

Date: {datetime.now().isoformat()}
Task: {plan.get("task", "")}
Status: {plan.get("status", "unknown")}

## Plan
{plan.get("plan_content", "No plan content")}

---

## Context
"""

        # Load context
        context = self.load_context()
        content += f"""
### Discovery
{context.get("discovery", "No discovery content")}

### SME Guidance
"""
        for domain, guidance in context.get("sme_guidance", {}).items():
            content += f"\n#### {domain}\n{guidance}"

        content += f"""
### Learnings
{context.get("learnings", "No learnings")}
"""

        with open(archive_file, "w") as f:
            f.write(content)

        print(f"✓ Archived to: {archive_file}")

    def clear_swarm(self):
        """Clear all swarm state (after confirmation)."""
        if not self.swarm_dir.exists():
            return

        # Archive first
        plan = self.load_plan()
        if plan:
            self.archive_swarm(plan)

        # Remove swarm directory
        shutil.rmtree(self.swarm_dir)
        self.swarm_dir.mkdir(parents=True, exist_ok=True)
        print("✓ Swarm cleared")

    def update_task_status(self, phase_num: int, task_idx: int, status: str):
        """Update a specific task's status in the plan."""
        plan = self.load_plan()
        if not plan:
            return

        # Find the phase and task
        for phase in plan.get("phases", []):
            if phase.get("phase_num") == phase_num:
                for task in phase.get("tasks", []):
                    if task.get("task_idx") == task_idx:
                        task["status"] = status
                        if status == "completed":
                            task["completed_at"] = datetime.now().isoformat()
                        break
                break

        self.save_plan(plan)

    def get_current_state(self) -> Dict:
        """Get current swarm state."""
        plan = self.load_plan()
        context = self.load_context()

        # Calculate progress
        total_tasks = 0
        completed_tasks = 0

        if plan:
            for phase in plan.get("phases", []):
                for task in phase.get("tasks", []):
                    total_tasks += 1
                    if task.get("status") == "completed":
                        completed_tasks += 1

        progress = {
            "total": total_tasks,
            "completed": completed_tasks,
            "percentage": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
        }

        return {
            "has_plan": plan is not None,
            "plan": plan,
            "context": context,
            "progress": progress,
        }
