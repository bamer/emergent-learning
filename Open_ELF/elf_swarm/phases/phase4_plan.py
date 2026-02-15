"""
Phase 4: Create Plan
"""

from datetime import datetime


def create_plan(orchestrator, plan: dict) -> None:
    """
    Phase 4: Create detailed implementation plan.

    Uses architect to create phases, tasks, and acceptance criteria.
    """
    from datetime import datetime

    print("\n🔍 Phase 4: Plan")

    # Load context for the architect
    context = orchestrator.swarm_manager.load_context()

    context_prompt = f"""
Discovery:
{context.get("discovery", "None")}

SME Guidance:
{", ".join(context.get("sme_guidance", {}).keys())}
"""

    result = orchestrator.ask_agent(
        "architect",
        f"""
Task: {orchestrator.task}

{context_prompt}

Create a detailed implementation plan with:
- Phases (logical groupings)
- Tasks within each phase
- Acceptance criteria for each task
- Dependencies between tasks

Output format:
# Swarm Implementation Plan

## Phase 1: [Phase Name]
### Task 1.1: [Task Description]
- Description: ...
- Acceptance Criteria:
  - [ ] [criterion 1]
  - [ ] [criterion 2]
- Dependencies: none

Continue for all phases. Start with Foundation, then Core Implementation, then Polish.
""",
    )

    # Save plan content
    plan_content = result.get("response", "")

    # Save to JSON
    plan["planned"] = True
    plan["plan_content"] = plan_content
    plan["planned_at"] = datetime.now().isoformat()

    # Also save to markdown
    orchestrator.swarm_manager.create_markdown_plan(plan_content)

    print("✓ Plan created")
    print(f"  Plan saved to: {orchestrator.swarm_manager.swarm_dir}/plan.md")


def revise_plan(orchestrator, plan: dict) -> None:
    """
    Revise plan based on critic feedback.
    """
    print("\n📝 Phase 4: Revise Plan")

    result = orchestrator.ask_agent(
        "architect",
        f"""
Original plan:

{plan.get("plan_content", "")}

Revise the plan to address any issues or concerns.
Output the revised in the same format as the original plan.
""",
    )

    plan_content = result.get("response", "")
    plan["plan_content"] = plan_content
    plan["revised_at"] = datetime.now().isoformat()

    orchestrator.swarm_manager.create_markdown_plan(plan_content)
    print("✓ Plan revised")
