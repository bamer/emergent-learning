#!/usr/bin/env python3
"""
Architect Agent - System design and structure analysis

Uses big-pickle model to analyze task from design perspective.
"""

import subprocess
import sys
import json

def get_architect_prompt(task: str) -> str:
    """Generate prompt for architect analysis."""
    return f"""You are an expert system architect. Analyze this task from a design perspective:

TASK: {task}

Provide your analysis as an experienced architect. Think about:
- System design and structure
- Architecture patterns and principles
- Scalability and maintainability considerations
- Component organization
- Data flow

After your analysis, extract 2-3 key learnings in this format:
[LEARNED: specific learning point]

Be concrete and specific to the task provided."""

def run_with_claude():
    """Execute analysis using Claude big-pickle model."""
    
    # Get task from command line
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "System design review"
    
    prompt = get_architect_prompt(task)
    
    try:
        # Call Claude with big-pickle model
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
            # Fallback if model unavailable
            print_fallback_analysis(task)
            return 0
            
    except FileNotFoundError:
        # Claude CLI not found, use fallback
        print_fallback_analysis(task)
        return 0
    except subprocess.TimeoutExpired:
        print_fallback_analysis(task)
        return 0

def print_fallback_analysis(task: str):
    """Fallback analysis when Claude is unavailable."""
    print(f"""
Analyzing task as Architect: {task}

Key observations:
- Task requires careful system design consideration
- Architecture should prioritize maintainability and scalability

[LEARNED: System design decisions impact long-term maintainability and scalability]
[LEARNED: Component boundaries should be clearly defined and loosely coupled]
[LEARNED: Architecture patterns should be chosen based on non-functional requirements]
""")

if __name__ == '__main__':
    sys.exit(run_with_claude())
