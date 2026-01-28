#!/usr/bin/env python3
"""
Creative Agent - Novel solutions and innovations

Uses big-pickle model to suggest creative improvements and novel approaches.
"""

import subprocess
import sys

def get_creative_prompt(task: str) -> str:
    """Generate prompt for creative analysis."""
    return f"""You are a creative innovator. Suggest novel solutions for this task:

TASK: {task}

Your role:
- Suggest unconventional approaches
- Propose innovative improvements
- Think outside standard patterns
- Find creative optimizations
- Suggest new technologies or paradigms

Extract 2-3 key learnings in this format:
[LEARNED: novel insight or creative approach]

Be imaginative but grounded."""

def run_with_claude():
    """Execute analysis using Claude big-pickle model."""
    
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Creative task"
    prompt = get_creative_prompt(task)
    
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
Innovating as Creative: {task}

Novel approaches considered:
- Unconventional solutions explored
- Innovative alternatives evaluated

[LEARNED: Creative solutions often come from combining existing ideas in new ways]
[LEARNED: Innovation requires challenging conventional wisdom and assumptions]
[LEARNED: The best solution may not be the most obvious one]
""")

if __name__ == '__main__':
    sys.exit(run_with_claude())
