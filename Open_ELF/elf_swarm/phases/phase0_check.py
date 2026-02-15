"""
Phase 0: Check for Existing Plan
"""


def check_plan(orchestrator) -> bool:
    """Check if a plan already exists."""
    return orchestrator.swarm_manager.has_existing_plan()
