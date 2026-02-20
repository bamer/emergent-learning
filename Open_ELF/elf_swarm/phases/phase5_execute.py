"""
Phase 5: Execute Tasks
"""


def execute_tasks(orchestrator, plan: dict, max_attempts: int = 3) -> None:
    """
    Phase 5: Execute all tasks in the plan.

    Uses TaskExecutor to run coder → reviewer → test loop.

    Args:
        orchestrator: SwarmOrchestrator instance
        plan: Plan dictionary
        max_attempts: Maximum attempts per task (3-5000)
    """
    from datetime import datetime
    import sys

    print("\n🔍 Phase 5: Execute")

    # Load context
    context = orchestrator.swarm_manager.load_context()

    # Need to parse plan content from plan.md
    plan_file = orchestrator.swarm_manager.swarm_dir / "plan.md"

    if not plan_file.exists():
        print("⚠️  No plan.md found. Cannot execute.")
        plan["execution_status"] = "no_plan"
        return

    import sys

    sys.path.insert(0, "/home/bamer/OPC_ELF")
    from Open_ELF.elf_swarm.plan_parser import parse_plan

    # Parse plan
    with open(plan_file, "r") as f:
        plan_content = f.read()

    phases = parse_plan(plan_content)

    if not phases:
        print("⚠️  No tasks found in plan.md")
        plan["execution_status"] = "no_tasks"
        return

    print(
        f"\nFound {len(phases)} phase(s) with {sum(len(p.tasks) for p in phases)} task(s)"
    )

    # Get config for max attempts
    # Default: 3, but can be configured via ELF golden rules or user preference
    max_attempts = (
        3  # Could check building for: python /.../query.py --rule "swarm max_attempts"
    )

    # Create task executor
    from Open_ELF.elf_swarm.task_executor import TaskExecutor

    executor = TaskExecutor(
        swarm_manager=orchestrator.swarm_manager, max_attempts=max_attempts
    )

    # Execute all tasks
    try:
        plan = executor.execute_all_tasks(phases, plan, context)
        plan["execution_status"] = (
            "completed"
            if plan.get("execution_summary", {}).get("failed_tasks", 0) == 0
            else "partial"
        )
    except Exception as e:
        print(f"\n❌ Execution error: {e}")
        plan["execution_status"] = "error"
        plan["execution_error"] = str(e)

    # Show summary
    print("\n" + "=" * 60)
    print("Execution Summary")
    print("=" * 60)

    summary = plan.get("execution_summary", {})
    print(f"Total tasks:  {summary.get('total_tasks', 0)}")
    print(f"Completed:     {summary.get('completed_tasks', 0)}")
    print(f"Failed:        {summary.get('failed_tasks', 0)}")
    print(f"Skipped:       {summary.get('skipped_tasks', 0)}")
    print(f"Total attempts: {summary.get('total_attempts', 0)}")

    plan["execution_started"] = datetime.now().isoformat()
