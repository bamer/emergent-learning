#!/usr/bin/env python3
"""
Swarm Orchestrator - Phased Multi-Agent Workflow
================================================

Coordinates the complete phased swarm workflow:
1. Check for existing plan
2. Clarify requirements
3. Discover codebase
4. Consult SMEs
5. Create plan
6. Critic gate
7. Execute (coder → reviewer → test loop)
8. Complete phase
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from agents.agent_manager import get_agent_manager

from .swarm_manager import SwarmManager


class SwarmOrchestrator:
    """Orchestrates the proper phased swarm workflow."""

    def __init__(self, task: str, work_dir: Path = None, max_attempts: int = 3):
        """Initialize SwarmOrchestrator.

        Args:
            task: The task description
            work_dir: Working directory for the swarm
            max_attempts: Maximum attempts per task (3-5000, default: 3)
        """
        # Validate max_attempts
        if not isinstance(max_attempts, int) or max_attempts < 3 or max_attempts > 5000:
            raise ValueError("max_attempts must be an integer between 3 and 5000")

        self.task = task
        self.work_dir = work_dir or Path.cwd()
        self.swarm_manager = SwarmManager(self.work_dir)
        self.agent_manager = get_agent_manager()
        self.max_attempts = max_attempts

    def run(self):
        """Run the complete swarm workflow."""
        self._print_header()

        # Phase 0: Check for existing plan
        if self.swarm_manager.has_existing_plan():
            print("\n📋 Existing plan found. Checking...")
            plan = self.swarm_manager.load_plan()

            # Check if it's the same task - if not, start fresh
            existing_task = plan.get("task", "")
            if existing_task != self.task:
                print(f"\n⚠️  Different task detected!")
                print(f"   Existing: {existing_task[:50]}...")
                print(f"   New:      {self.task[:50]}...")
                print("   Starting fresh...")
                plan = self._create_initial_plan()
            else:
                print("\n📋 Resuming same task...")
        else:
            print("\n📝 New task. Starting fresh...")
            plan = self._create_initial_plan()

        # Phase 1: Clarify (if needed)
        if not plan.get("clarified"):
            from .phases.phase1_clarify import clarify_requirements

            clarify_requirements(self, plan)
            self.swarm_manager.save_plan(plan)

        # Phase 2: Discover codebase
        if not plan.get("discovered"):
            from .phases.phase2_discover import discover_codebase

            discover_codebase(self, plan)
            self.swarm_manager.save_plan(plan)

        # Phase 3: Consult SMEs
        if not plan.get("sme_consulted"):
            from .phases.phase3_sme import consult_smes

            consult_smes(self, plan)
            self.swarm_manager.save_plan(plan)

        # Phase 4: Create plan
        if not plan.get("planned"):
            from .phases.phase4_plan import create_plan

            create_plan(self, plan)
            self.swarm_manager.save_plan(plan)

        # Phase 4.5: Critic gate
        from .phases.phase45_critic import critic_gate

        approval = critic_gate(self, plan)

        if approval == "REJECTED":
            print(f"\n❌ Plan rejected. Escalating to user.")
            plan["status"] = "user_review_needed"
            self.swarm_manager.save_plan(plan)
            return

        if approval == "NEEDS_REVISION":
            print(f"\n⚠️  Plan needs revision.")

            # Revision cycle (max 2)
            for i in range(2):
                print(f"\n📝 Revision {i + 1}...")
                from .phases.phase4_plan import revise_plan

                revise_plan(self, plan)
                self.swarm_manager.save_plan(plan)
                approval = critic_gate(self, plan)

                if approval == "APPROVED":
                    break

            if approval != "APPROVED":
                print(f"\n❌ Plan rejected after revisions. Escalating.")
                plan["status"] = "user_review_needed"
                self.swarm_manager.save_plan(plan)
                return

        # Phase 5: Execute
        from .phases.phase5_execute import execute_tasks

        execute_tasks(self, plan, max_attempts=self.max_attempts)
        self.swarm_manager.save_plan(plan)

        # Phase 6: Complete
        from .phases.phase6_complete import complete_phase

        complete_phase(self, plan)
        self.swarm_manager.save_plan(plan)

        self._print_completion()

    def _print_header(self):
        """Print header."""
        print(f"\n{'=' * 60}")
        print(f"🚀 OpenCode Swarm - ELF Phased Workflow")
        print(f"{'=' * 60}")
        print(f"Task: {self.task}\n")

    def _print_completion(self):
        """Print completion message."""
        print(f"\n{'=' * 60}")
        print(f"✅ Swarm Complete!")
        print(f"{'=' * 60}")

        # Show progress
        state = self.swarm_manager.get_current_state()
        progress = state["progress"]
        print(f"\nProgress: {progress['completed']}/{progress['total']} tasks")
        print(f"Percentage: {progress['percentage']:.1f}%")

        print(f"\nResults saved to: {self.swarm_manager.swarm_dir}")

    def _create_initial_plan(self) -> Dict:
        """Create initial plan structure."""
        return {
            "task": self.task,
            "status": "initializing",
            "clarified": False,
            "discovered": False,
            "sme_consulted": False,
            "planned": False,
            "approved": False,
            "phases": [],
            "context": {},
            "created_at": datetime.now().isoformat(),
        }

    def ask_agent(self, agent: str, prompt: str, context: Dict = None) -> Dict:
        """Ask an agent and get response."""
        full_prompt = prompt
        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            full_prompt = f"\nContext:\n{context_str}\n\n{prompt}"

        return self.agent_manager.ask_agent(agent, full_prompt)
