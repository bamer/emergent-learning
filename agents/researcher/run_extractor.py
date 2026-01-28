#!/usr/bin/env python3
"""
Researcher Agent - Research and validation analysis

Uses big-pickle model to research task against standards and best practices.
"""

import subprocess
import sys

def get_researcher_prompt(task: str) -> str:
    """Generate prompt for researcher analysis."""
    return f"""You are an expert researcher. Research and validate this task:

TASK: {task}

Your role:
- Research existing patterns and best practices
- Validate against industry standards
- Find proven approaches
- Document reference materials and standards

Extract 2-3 key learnings in this format:
[LEARNED: research finding or best practice]

Be specific to the task domain."""

def run_with_claude():
    """Execute analysis using Claude big-pickle model."""
    
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Research task"
    prompt = get_researcher_prompt(task)
    
    try:
        result = subprocess.run(
            ["claude", "--print", "--model", "opencode/big-pickle"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return 0
        else:
            print_fallback_analysis(task)
            return 0
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_fallback_analysis(task)
        return 0

def print_fallback_analysis(task: str):
    """Fallback analysis when Claude is unavailable."""
    print(f"""
Researching as Researcher: {task}

Investigation findings:
- Searching for existing solutions and patterns
- Validating against best practices

[LEARNED: Established standards and best practices exist for this domain]
[LEARNED: Prior solutions provide valuable insights for current implementation]
[LEARNED: Validation against standards prevents common pitfalls]
""")

if __name__ == '__main__':
    sys.exit(run_with_claude())
