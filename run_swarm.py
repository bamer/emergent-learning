import os
import argparse
from tools import swarm_task, swarm_spawn_subtask

parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True)
parser.add_argument("--mode", required=True)
args = parser.parse_args()

# Execute swarm task
swarm_response = swarm_task(task=args.task, mode=args.mode, context="")

# Extract and save task ID
task_id = swarm_response.get("task_id", "unknown")
with open("/tmp/run_swarm_task_id", "w") as f:
    f.write(task_id)
os.chmod("/tmp/run_swarm_task_id", 0o755)

# Spawn deep analysis subtask
subtask_result = swarm_spawn_subtask(
    bead_id=task_id,
    epic_id=task_id,
    subtask_title="Analyze heuristics regression, identify bottlenecks, propose remediation",
    subtask_description="Deep analysis of heuristics regression to identify performance bottlenecks and propose remediation strategies.",
    files=[],
    shared_context="",
)

# Save output to markdown
os.makedirs("memory/analysis", exist_ok=True)
with open("memory/analysis/heuristics-regression.md", "w") as f:
    f.write(
        f"## Analysis Results\n\n{subtask_result.get('output', 'No output captured')}"
    )
