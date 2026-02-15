"""
Phase 6: Complete Phase
"""


def complete_phase(orchestrator, plan: dict) -> None:
    """
    Phase 6: Archive and cleanup.
    """
    from datetime import datetime

    print("\n🔍 Phase 6: Phase Complete")

    # Re-scan with researcher
    print("\n  📸 Re-scanning codebase...")
    result = orchestrator.ask_agent(
        "researcher",
        f"Scan the codebase and report what was implemented for: {orchestrator.task}",
    )

    # Update context with learnings
    print("\n  💑 Extracting learnings...")
    result2 = orchestrator.ask_agent(
        "learning-extractor",
        f"""
Task: {orchestrator.task}

Scan results: {result.get("response", "")}

Extract key learnings to add to context.md.
""",
    )

    # Save to context
    context = orchestrator.swarm_manager.load_context()
    context["learnings"] = result2.get("response", "")
    context["scan_results"] = result.get("response", "")
    context["completed_at"] = datetime.now().isoformat()
    orchestrator.swarm_manager.save_context(context)

    # Append to markdown context
    context_file = orchestrator.swarm_manager.swarm_dir / "context.md"
    with open(context_file, "a") as f:
        f.write(f"\n## Post-Implementation Scan\n{result.get('response', '')}\n")
        f.write(f"\n## Learnings\n{result2.get('response', '')}\n")

    # Archive
    orchestrator.swarm_manager.archive_swarm(plan)

    # Update plan status
    plan["status"] = "completed"
    plan["completed_at"] = datetime.now().isoformat()

    print("✓ Phase complete")
    print("✓ Results archived")
