"""
Phase 4.5: Critic Gate
"""


def critic_gate(orchestrator, plan: dict) -> str:
    """
    Phase 4.5: Critic reviews the plan.

    Returns: "APPROVED", "NEEDS_REVISION", or "REJECTED"
    """
    print("\n🔍 Phase 4.5: Critic Gate")

    result = orchestrator.ask_agent(
        "skeptic",
        f"""
Review this implementation plan critically:

{plan.get("plan_content", "")}

Evaluate:
- Feasibility: Can this be accomplished?
- Completeness: Are we missing anything critical?
- Quality: Are the acceptance criteria clear and testable?
- Risks: What could go wrong?

Output in format:
APPROVED if plan is solid
NEEDS_REVISION if there are issues to fix
REJECTED if fundamentally flawed

Follow with:
- Reasoning: ...
- Specific concerns: [list]
- Revision suggestions: [list]
""",
    )

    response = result.get("response", "").upper()

    if "APPROVED" in response:
        print("✓ Plan approved")
        return "APPROVED"
    elif "NEEDS_REVISION" in response:
        print("⚠️  Plan needs revision")
        return "NEEDS_REVISION"
    else:
        print("✗ Plan rejected")
        return "REJECTED"
