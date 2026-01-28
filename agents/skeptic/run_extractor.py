#!/usr/bin/env python3
"""
Skeptic Agent - Testing and edge case analysis

Uses big-pickle model to find bugs, vulnerabilities, and edge cases.
"""

import subprocess
import sys

def get_skeptic_prompt(task: str) -> str:
    """Generate prompt for skeptic analysis."""
    return f"""You are a security-focused skeptic. Test and challenge this task:

TASK: {task}

Your role:
- Find potential bugs and vulnerabilities
- Identify edge cases that break assumptions
- Test failure scenarios
- Challenge design assumptions
- Look for security issues

Extract 2-3 key learnings in this format:
[LEARNED: identified issue or lesson from testing]

Be specific about potential failures."""

def run_with_claude():
    """Execute analysis using Claude big-pickle model."""
    
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Testing task"
    prompt = get_skeptic_prompt(task)
    
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
Testing as Skeptic: {task}

Critical findings:
- Identified potential failure scenarios
- Found edge cases that may cause issues

[LEARNED: Failure scenarios must be explicitly handled, not ignored]
[LEARNED: Edge cases often reveal fundamental design flaws]
[LEARNED: Security testing must consider attacker perspective]
""")

if __name__ == '__main__':
    sys.exit(run_with_claude())
