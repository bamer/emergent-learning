"""
Phase 1: Clarify Requirements
"""


def clarify_requirements(orchestrator, plan: dict) -> None:
    """
    Phase 1: Ask clarifying questions if needed.

    Uses architect to identify what information is missing.
    """
    from datetime import datetime

    print("\n🔍 Phase 1: Clarify")

    result = orchestrator.ask_agent(
        "architect",
        f"""
Task: {orchestrator.task}

What information is missing? What questions should I ask the user?
Consider: scope, tech stack, constraints, priorities.

Output format:
- QUESTION: [question]
  Rationale: [why this matters]

If all info is clear, output: "REQUIREMENTS_CLEAR"
""",
    )

    # Update context with clarification needs
    context = orchestrator.swarm_manager.load_context()
    context["clarification_needed"] = result.get("response", "")
    context["clarified_at"] = datetime.now().isoformat()
    orchestrator.swarm_manager.save_context(context)

    prompt = f"""
# Clarification Questions

{result.get("response", "")}

**Please answer these questions so the swarm can proceed with the design.**

Press Enter when ready to continue...
"""

    if "REQUIREMENTS_CLEAR" not in result.get("response", ""):
        print(f"\n{prompt}")
        # This would be interactive - for now we assume user will provide answers

    plan["clarified"] = True
    print("✓ Clarification phase complete")
