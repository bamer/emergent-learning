#!/usr/bin/env python3
"""
Simple OpenCode Client - Direct Node.js call

Since the CLI has JS module issues, call Node.js directly.
"""

import subprocess
import json
from typing import Optional
import sys

OPENCODE_BIN = "/home/bamer/Downloads/opencode-1.1.34/packages/opencode/bin/opencode"

class SimpleOpenCodeClient:
    """Simple client that calls OpenCode via Node.js."""
    
    def __init__(self, model: str = "opencode/big-pickle"):
        self.model = model
        self.available = self._check_node()
    
    def _check_node(self) -> bool:
        """Check if Node.js is available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                timeout=2,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def call(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """Call OpenCode with prompt."""
        if not self.available:
            print("Error: Node.js not found", file=sys.stderr)
            return None
        
        try:
            # Call Node.js directly with the opencode binary
            # The binary is a Node.js script
            result = subprocess.run(
                ["node", OPENCODE_BIN, "--model", self.model, "--prompt", prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            if result.stderr:
                print(f"OpenCode error: {result.stderr[:200]}", file=sys.stderr)
            
            return None
            
        except subprocess.TimeoutExpired:
            print(f"Error: OpenCode timed out (>{timeout}s)", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
    
    def get_status(self) -> dict:
        """Get status."""
        return {
            "node_available": self.available,
            "model": self.model,
            "method": "Node.js direct call"
        }

def call_opencode(prompt: str, model: str = "opencode/big-pickle", timeout: int = 120) -> Optional[str]:
    """Simple function to call OpenCode."""
    client = SimpleOpenCodeClient(model=model)
    return client.call(prompt, timeout)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: simple_opencode_client.py <prompt> [model] [timeout]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "opencode/big-pickle"
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    
    client = SimpleOpenCodeClient(model=model)
    status = client.get_status()
    print(f"Status: {status}", file=sys.stderr)
    
    response = client.call(prompt, timeout)
    
    if response:
        print(response)
    else:
        sys.exit(1)
