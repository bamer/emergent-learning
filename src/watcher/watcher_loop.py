#!/usr/bin/env python3
"""
Watcher Loop - Simplified for OpenCode Integration

Provides prompts for Tier 1 (watcher) and Tier 2 (handler) analysis.
"""

import sys


def get_watcher_prompt() -> str:
    """Get the prompt for Tier 1 (watcher) analysis"""
    return """Analyze the current system state and experiments.

Your role:
1. Check system health
2. Monitor experiment progress  
3. Identify issues or anomalies
4. Decide if escalation is needed

Provide your analysis in this format:
STATUS: HEALTHY|WARNING|CRITICAL
ANALYSIS: [your findings]
RECOMMENDATION: [what should happen next]
ESCALATE: YES|NO (if yes, Tier 2 handler will be invoked)
"""


def get_handler_prompt() -> str:
    """Get the prompt for Tier 2 (handler) analysis"""
    return """You are the Handler agent for escalated issues.

The watcher has flagged a potential issue that needs deeper analysis.

Your role:
1. Understand the escalated issue
2. Perform detailed root cause analysis
3. Recommend concrete actions
4. Determine if further escalation to CEO is needed

Provide your analysis in this format:
STATUS: RESOLVED|PENDING|ESCALATE
ANALYSIS: [detailed findings]
ACTION: [recommended action]
ESCALATE: YES|NO (if yes, escalate to CEO advisor)
"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: watcher_loop.py <prompt|handler-prompt>")
        sys.exit(1)
    
    prompt_type = sys.argv[1]
    
    if prompt_type == "prompt":
        print(get_watcher_prompt())
    elif prompt_type == "handler-prompt":
        print(get_handler_prompt())
    else:
        print(f"Unknown prompt type: {prompt_type}")
        sys.exit(1)
