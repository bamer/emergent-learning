#!/usr/bin/env python3
"""
mock_agent.py - Mock agent for testing swarm without real agents

Simulates agent execution and generates [LEARNED:] markers.
"""

import sys
import random
from pathlib import Path

LEARNINGS = {
    'architect': [
        "[LEARNED: Authentication should be decoupled from core app logic]",
        "[LEARNED: Token-based auth scales better than session-based]",
        "[LEARNED: Multi-factor authentication requires async verification]",
    ],
    'researcher': [
        "[LEARNED: OAuth 2.0 is industry standard for auth]",
        "[LEARNED: OIDC provides better security than custom auth]",
    ],
    'skeptic': [
        "[LEARNED: Token replay attacks must be prevented with nonce/timestamp]",
        "[LEARNED: Password reset endpoints are common vulnerability vectors]",
        "[LEARNED: Concurrent login sessions create race conditions]",
    ],
    'creative': [
        "[LEARNED: Passwordless auth improves UX significantly]",
        "[LEARNED: WebAuthn reduces phishing attack surface]",
    ]
}

def main():
    # Parse which agent this is
    agent_name = Path(__file__).stem.split('_')[0] if '_' in Path(__file__).stem else 'architect'
    
    # Get from argv if provided
    if len(sys.argv) > 1:
        # Find --agent or agent name in args
        for arg in sys.argv:
            if arg in LEARNINGS:
                agent_name = arg
                break
    
    # Default to architect if not found
    if agent_name not in LEARNINGS:
        agent_name = 'architect'
    
    # Print analysis
    print(f"\n[MOCK {agent_name.upper()} AGENT]")
    print(f"Analyzing task: {' '.join(sys.argv[1:])}\n")
    
    # Print learnings
    for learning in LEARNINGS[agent_name]:
        print(learning)
    
    # Print some discussion
    print(f"\n[Analysis complete for {agent_name}]\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
