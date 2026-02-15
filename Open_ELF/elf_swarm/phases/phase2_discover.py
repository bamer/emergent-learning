"""
Phase 2: Discover Codebase
"""


def discover_codebase(orchestrator, plan: dict) -> None:
    """Phase 2: Discover codebase structure."""
    print("\n🔍 Phase 2: Discover")

    result = orchestrator.ask_agent(
        "researcher",
        f"""
Task: {orchestrator.task}

Explore the codebase to understand:
- Project structure and organization
- Languages and frameworks used
- Existing patterns and conventions
- Relevant files and modules

Report findings in ## DISCOVERY section.
""",
    )

    # Save to context
    context = orchestrator.swarm_manager.load_context()
    context["discovery"] = result.get("response", "")
    context["discovered_at"] = None
    orchestrator.swarm_manager.save_context(context)

    # Also save to markdown file for human reference
    context_file = orchestrator.swarm_manager.swarm_dir / "context.md"
    with open(context_file, "w") as f:
        from datetime import datetime

        f.write(f"# Swarm Context\n\n")
        f.write(f"Created: {datetime.now().isoformat()}\n\n")
        f.write(f"## Task\n{orchestrator.task}\n\n")
        f.write(f"## Discovery\n{result.get('response', '')}\n")

    plan["discovered"] = True
    print("✓ Discovery complete")
