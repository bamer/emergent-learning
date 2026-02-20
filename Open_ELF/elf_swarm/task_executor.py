"""
Task Executor - Implements coder → reviewer → test loop with retries
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import importlib.util
import sys
from pathlib import Path

from agents.agent_manager import get_agent_manager
from .plan_parser import Task, Phase
from .swarm_manager import SwarmManager


def _import_mission_store():
    """Import mission_store module using importlib (avoids sys.path issues).

    Returns:
        The mission_store module
    """
    backend_path = Path(
        "/home/bamer/OPC_ELF/Open_ELF/dashboard-app/backend/mission_store.py"
    )

    if not backend_path.exists():
        raise ImportError(f"mission_store.py not found at {backend_path}")

    spec = importlib.util.spec_from_file_location("mission_store", backend_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for mission_store at {backend_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["mission_store"] = module
    spec.loader.exec_module(module)

    return module


class TaskExecutor:
    """Executes tasks with coder → reviewer → test loop."""

    def __init__(
        self,
        agent_manager=None,
        swarm_manager: SwarmManager = None,
        max_attempts: int = 3,
    ):
        self.agent_manager = agent_manager or get_agent_manager()
        self.swarm_manager = swarm_manager
        self.max_attempts = max_attempts

    def execute_all_tasks(
        self, phases: List[Phase], plan: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all tasks in all phases."""
        execution_summary = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "skipped_tasks": 0,
            "total_attempts": 0,
        }

        for phase in phases:
            print(f"\n{'=' * 60}")
            print(f"📋 {phase.name}")
            print(f"{'=' * 60}")

            for task in phase.tasks:
                execution_summary["total_tasks"] += 1

                status = self._execute_single_task(task, phase, plan, context)

                if status == "completed":
                    execution_summary["completed_tasks"] += 1
                elif status == "failed":
                    execution_summary["failed_tasks"] += 1
                else:
                    execution_summary["skipped_tasks"] += 1

                execution_summary["total_attempts"] += task.attempts

        plan["execution_summary"] = execution_summary
        return plan

    def _execute_single_task(
        self, task: Task, phase: Phase, plan: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Execute a single task with coder → reviewer → test loop."""
        print(f"\n  Task {task.task_idx}.1: {task.name}")
        desc_preview = (
            task.description[:80] + "..."
            if len(task.description) > 80
            else task.description
        )
        print(f"  Description: {desc_preview}")

        # Check dependencies
        for dep in task.dependencies:
            dependent_task = self._find_task_by_name(plan.get("phases", []), dep)
            if dependent_task and dependent_task.get("status") == "failed":
                print(f"  ⚠️  Skipped: Dependency {dep} failed")
                task.status = "skipped"
                task.logs.append(f"Skipped: dependency {dep} failed")
                return "skipped"

        task.status = "in_progress"
        task.max_attempts = self.max_attempts

        for attempt in range(1, self.max_attempts + 1):
            task.attempts = attempt
            print(f"\n  🔄 Attempt {attempt}/{self.max_attempts}")

            mission_id = self._create_mission_for_task(task, phase, context)

            # Coder
            coder_result = self._execute_coder(task, phase, plan, context, mission_id)

            if not coder_result.get("success"):
                task.status = "failed"
                task.error = coder_result.get("error", "Unknown error")
                print(f"  ❌ Coder failed: {task.error}")
                self._update_mission_failed(mission_id, task.error)
                continue

            # Reviewer
            reviewer_result = self._execute_reviewer(
                task, phase, plan, context, coder_result["output"], mission_id
            )

            if not reviewer_result.get("success"):
                if attempt < self.max_attempts:
                    print(f"  ⚠️  Reviewer rejected on attempt {attempt}")
                    task.logs.append(
                        f"Reviewer rejected: {reviewer_result.get('error')}"
                    )
                    self._update_mission_running(
                        mission_id, f"Reviewer rejected - retrying..."
                    )
                    continue
                else:
                    task.status = "failed"
                    task.error = reviewer_result.get(
                        "error", "Max attempts exceeded after reviewer rejection"
                    )
                    print(
                        f"  ❌ Reviewer rejected after {attempt} attempts: {task.error}"
                    )
                    self._update_mission_failed(mission_id, task.error)
                    break

            # Tester
            test_result = self._execute_tester(task, phase, plan, context, mission_id)

            if not test_result.get("success"):
                if attempt < self.max_attempts:
                    print(f"  ⚠️  Tests failed on attempt {attempt}")
                    task.logs.append(f"Tests failed: {test_result.get('error')}")
                    self._update_mission_running(
                        mission_id, f"Tests failed - fixing..."
                    )
                    continue
                else:
                    task.status = "failed"
                    task.error = test_result.get(
                        "error", "Max attempts exceeded after test failure"
                    )
                    print(f"  ❌ Tests failed after {attempt} attempts: {task.error}")
                    self._update_mission_failed(mission_id, task.error)
                    break

            # Success!
            task.status = "completed"
            task.result = coder_result.get("output", "")
            print(f"  ✅ Task completed (attempt {attempt})")
            self._update_mission_completed(mission_id, task.result)
            break

        self._update_plan_checkbox(plan, task, phase)
        self.swarm_manager.save_plan(plan)

        return task.status

    def _find_task_by_name(self, phases: List[Dict], task_name: str) -> Optional[Dict]:
        """Find a task by name."""
        for phase in phases:
            for task in phase.get("tasks", []):
                if task_name in task.get("name", ""):
                    return task
        return None

    def _create_mission_for_task(self, task: Task, phase: Phase, context: Dict) -> str:
        """Create mission for dashboard tracking."""
        try:
            mission_store = _import_mission_store()
            get_mission_store = mission_store.get_mission_store

            mission_store = get_mission_store()

            task_desc = f"""Phase {phase.phase_num} - {phase.name}
Task {task.task_idx}: {task.name}

Description:
{task.description}

Acceptance Criteria:
{chr(10).join(f"- [ ] {c}" for c in task.acceptance_criteria)}

Dependencies:
{", ".join(task.dependencies) if task.dependencies else "None"}

Context:
Task: {context.get("task", "N/A")}
"""

            mission = mission_store.create_mission(
                agent_type="elf_swarm", mission_text=task_desc
            )

            mission_store.start_mission(mission.id, "elf_swarm_execution")
            return mission.id

        except Exception as e:
            print(f"  ⚠️  Failed to create mission: {e}")
            return f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _update_mission_running(self, mission_id: str, message: str) -> None:
        """Update mission status to running."""
        try:
            mission_store_module = _import_mission_store()
            get_mission_store = mission_store_module.get_mission_store

            mission_store = get_mission_store()
            mission = mission_store.get_mission(mission_id)

            if mission:
                mission.logs.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "info",
                        "message": message,
                    }
                )
                mission_store.update_mission(mission)

        except Exception as e:
            print(f"  ⚠️  Failed to update mission: {e}")

    def _update_mission_completed(self, mission_id: str, result: str) -> None:
        """Mark mission as completed."""
        try:
            mission_store_module = _import_mission_store()
            get_mission_store = mission_store_module.get_mission_store

            mission_store = get_mission_store()
            mission_store.complete_mission(mission_id, result)

        except Exception as e:
            print(f"  ⚠️  Failed to complete mission: {e}")

    def _update_mission_failed(self, mission_id: str, error: str) -> None:
        """Mark mission as failed."""
        try:
            mission_store_module = _import_mission_store()
            get_mission_store = mission_store_module.get_mission_store

            mission_store = get_mission_store()
            mission_store.fail_mission(mission_id, error)

        except Exception as e:
            print(f"  ⚠️  Failed to fail mission: {e}")

    def _execute_coder(self, task, phase, plan, context, mission_id) -> Dict:
        """Execute Coder agent."""
        print(f"    🤖 @coder: Implementing...")

        lang = self._detect_language(task, plan, context)

        # Use coder-agent for all languages (most reliable)
        coder_agent = "coder-agent"

        prompt = f"""Task: {task.description}

Description: {task.description}

Acceptance Criteria:
{chr(10).join(f"- {c}" for c in task.acceptance_criteria)}

Context:
{self._build_context_text(context)}

Implement this task. Report in ## IMPLEMENTATION section."""

        result = self.agent_manager.ask_agent(coder_agent, prompt)

        if result.get("success"):
            print(f"    ✅ Implementation complete")
            return {
                "success": True,
                "output": result.get("response", ""),
                "agent": coder_agent,
            }
        else:
            print(f"    ❌ Implementation failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", ""),
                "agent": coder_agent,
            }

    def _execute_reviewer(
        self, task, phase, plan, context, implementation, mission_id
    ) -> Dict:
        """Execute Reviewer agent."""
        print(f"    🤖 @reviewer: Checking...")

        prompt = f"""Task: {task.description}

Implementation:
## IMPLEMENTATION
{implementation}
##

Acceptance Criteria:
{chr(10).join(f"- {c}" for c in task.acceptance_criteria)}

Review against acceptance criteria. Output:
APPROVED if passes, REJECTED if changes needed.
Include reasoning and required changes."""

        reviewer_agent = (
            "code-reviewer"
            if "code" in task.description.lower()
            else "architect-reviewer"
        )

        result = self.agent_manager.ask_agent(reviewer_agent, prompt)

        response = result.get("response", "")

        if "APPROVED" in response.upper():
            print(f"    ✅ Review passed")
            return {
                "success": True,
                "output": result.get("response", ""),
                "agent": reviewer_agent,
            }
        else:
            error = self._extract_error_from_review(response)
            print(f"    ⚠️  Review rejected: {error}")
            return {"success": False, "error": error, "agent": reviewer_agent}

    def _execute_tester(self, task, phase, plan, context, mission_id) -> Dict:
        """Execute Test agent."""
        print(f"    🤖 @test: Testing...")

        prompt = f"""Task: {task.description}

Acceptance Criteria:
{chr(10).join(f"- {c}" for c in task.acceptance_criteria)}

Write comprehensive tests. Output:
## Test Code
[code]

## Test Results
- Test 1: PASS/FAIL
- Overall: PASS/FAIL

If tests fail, provide details and fixes."""

        tester_agent = "test-automator"
        result = self.agent_manager.ask_agent(tester_agent, prompt)

        response = result.get("response", "")

        if "PASS" in response.upper() and "FAIL" not in response.upper()[50:]:
            print(f"    ✅ All tests passed")
            return {
                "success": True,
                "output": result.get("response", ""),
                "agent": tester_agent,
            }
        else:
            error = self._extract_error_from_tests(response)
            print(f"    ⚠️  Tests failed: {error}")
            return {"success": False, "error": error, "agent": tester_agent}

    def _detect_language(self, task, plan, context) -> str:
        """Detect task language."""
        text = f"{task.description} {plan.get('task', '')} {str(context)}".lower()

        language_mapping = {
            "python": ["python", "py", "django", "flask", "fastapi", "pandas"],
            "typescript": ["typescript", "ts", "react", "node", "express", "npm"],
            "rust": ["rust", "cargo"],
            "go": ["go", "golang"],
            "java": ["java", "maven", "gradle", "spring"],
            "javascript": ["javascript", "js", "node"],
        }

        for lang, keywords in language_mapping.items():
            if any(keyword in text for keyword in keywords):
                return lang
        return "python"

    def _build_context_text(self, context: Dict) -> str:
        """Build context text."""
        parts = []
        for key, value in context.items():
            if value and value != "None":
                parts.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(parts)

    def _extract_error_from_review(self, response: str) -> str:
        """Extract error from review."""
        if "Required changes:" in response:
            start = response.find("Required changes:")
            return response[start:].strip()
        elif "Specific issues found:" in response:
            start = response.find("Specific issues found:")
            return response[start:].strip()
        responses = response.split(".")[:2]
        return ".".join(responses).strip()

    def _extract_error_from_tests(self, response: str) -> str:
        """Extract error from tests."""
        if "## Test Results" in response:
            section = response[response.find("## Test Results") :]
            fail_lines = [line for line in section.split("\n") if "FAIL" in line]
            return "\n".join(fail_lines[:3])
        return "Tests failed - see full output for details"

    def _update_plan_checkbox(self, plan, task, phase):
        """Update plan.md with checkbox."""
        plan_file = self.swarm_manager.swarm_dir / "plan.md"

        if not plan_file.exists():
            return

        content = plan_file.read_text()

        # Update task header with status
        old = f"### Task {task.task_idx}: {task.name}"
        icon = "✅" if task.status == "completed" else "⏳"
        new = f"### Task {task.task_idx}: {task.name} ({icon})"
        content = content.replace(old, new)

        plan_file.write_text(content)

        # Update JSON phases
        if "phases" in plan:
            for p in plan["phases"]:
                if p.get("phase_num") == phase.phase_num:
                    for t in p.get("tasks", []):
                        if t.get("task_idx") == task.task_idx:
                            t["status"] = task.status
                            t["attempts"] = task.attempts
                            if task.result:
                                t["result"] = task.result
                            if task.error:
                                t["error"] = task.error
                            break
                    break
