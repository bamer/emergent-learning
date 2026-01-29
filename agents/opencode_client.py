#!/usr/bin/env python3
"""
OpenCode Client - HTTP API Access

Connects to OpenCode server running on port 4096:
    opencode --server --port 4096

Or uses CLI as fallback.
"""

import subprocess
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path

class OpenCodeClient:
    """Client for OpenCode via HTTP API or CLI fallback."""
    
    def __init__(self, model: str = "opencode/big-pickle", server_url: str = "http://localhost:4096"):
        self.model = model
        self.server_url = server_url
        self.server_available = self._check_server()
        if not self.server_available:
            self.cli_available = self._check_cli()
        else:
            self.cli_available = False
    
    def _check_server(self) -> bool:
        """Check if OpenCode server is running."""
        try:
            resp = requests.get(f"{self.server_url}/global/health", timeout=2)
            return resp.status_code == 200
        except:
            return False
    
    def _check_cli(self) -> bool:
        """Check if OpenCode CLI is available."""
        # Try standard location first
        cli_paths = [
            "opencode",  # In PATH
            "/home/bamer/Downloads/opencode-1.1.34/packages/opencode/bin/opencode",
            "/usr/local/bin/opencode",
            "/opt/opencode/bin/opencode"
        ]
        
        self.opencode_path = None
        for path in cli_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    timeout=2,
                    text=True
                )
                if result.returncode == 0:
                    self.opencode_path = path
                    return True
            except:
                continue
        
        return False
    
    def call(self, prompt: str, timeout: int = 120, agent: Optional[str] = None) -> Optional[str]:
        """
        Call OpenCode with a prompt via API or CLI.
        
        Args:
            prompt: The prompt to send to the AI
            timeout: Request timeout in seconds
            agent: Optional agent profile (researcher, architect, skeptic, creative, ceo, learning-extractor)
            
        Returns:
            Response text or None if failed
        """
        if self.server_available:
            return self._call_server(prompt, timeout, agent)
        elif self.cli_available:
            return self._call_cli(prompt, timeout)
        else:
            print("Error: OpenCode server not available on port 4096", flush=True)
            print("Start it with: opencode serve --port 4096", flush=True)
            return None
    
    def _call_server(self, prompt: str, timeout: int, agent: Optional[str] = None) -> Optional[str]:
        """Call via OpenCode server API.
        
        Args:
            prompt: The prompt to send
            timeout: Request timeout
            agent: Optional agent profile to use (researcher, architect, skeptic, creative, ceo, learning-extractor)
        """
        try:
            # 1. Create session
            session_resp = requests.post(
                f"{self.server_url}/session",
                json={"title": f"{agent or 'analyzer'}-session"},
                timeout=10
            )
            
            if session_resp.status_code != 200:
                print(f"Failed to create session: {session_resp.status_code}", flush=True)
                return None
            
            session_id = session_resp.json()["id"]
            
            # 2. Send message
            message_data = {
                "model": {
                    "providerID": "opencode",
                    "modelID": "big-pickle"
                },
                "parts": [{"type": "text", "text": prompt}]
            }
            
            # Add agent if specified
            if agent:
                message_data["agent"] = agent
            
            message_resp = requests.post(
                f"{self.server_url}/session/{session_id}/message",
                json=message_data,
                timeout=timeout
            )
            
            if message_resp.status_code != 200:
                print(f"Failed to send message: {message_resp.status_code}", flush=True)
                return None
            
            # 3. Extract response
            parts = message_resp.json().get("parts", [])
            response = ""
            for part in parts:
                if part.get("type") == "text":
                    response += part.get("text", "")
            
            # 4. Cleanup
            try:
                requests.delete(
                    f"{self.server_url}/session/{session_id}",
                    timeout=5
                )
            except:
                pass
            
            return response.strip() if response else None
            
        except Exception as e:
            print(f"Server API error: {e}", flush=True)
            return None
    
    def _call_cli(self, prompt: str, timeout: int) -> Optional[str]:
        """
        Call via OpenCode CLI.
        
        The CLI automatically communicates with the running OpenCode TUI backend.
        """
        try:
            cli = self.opencode_path or "opencode"
            result = subprocess.run(
                [cli, "--model", self.model, "--prompt", prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Print error if available
            if result.stderr:
                print(f"OpenCode stderr: {result.stderr[:200]}", flush=True)
            
            return None
            
        except FileNotFoundError:
            print("Error: opencode CLI not found. Install: npm install -g opencode", flush=True)
            return None
        except subprocess.TimeoutExpired:
            print(f"Error: opencode request timed out (>{timeout}s)", flush=True)
            return None
        except Exception as e:
            print(f"Error calling opencode: {e}", flush=True)
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get OpenCode status."""
        return {
            "server_available": self.server_available,
            "cli_available": self.cli_available,
            "model": self.model,
            "server_url": self.server_url,
            "method": "Server API (port 4096)" if self.server_available else "CLI (fallback)"
        }

# Convenience function
def call_opencode(prompt: str, model: str = "opencode/big-pickle", timeout: int = 120) -> Optional[str]:
    """
    Simple function to call OpenCode.
    
    Args:
        prompt: The prompt text
        model: Model ID (default: opencode/big-pickle)
        timeout: Timeout in seconds
        
    Returns:
        Response text or None
    """
    client = OpenCodeClient(model=model)
    return client.call(prompt, timeout)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: opencode_client.py <prompt> [model] [timeout]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "opencode/big-pickle"
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    
    client = OpenCodeClient(model=model)
    
    # Show status
    status = client.get_status()
    print(f"OpenCode Status: {status}", file=__import__('sys').stderr)
    
    if not client.cli_available:
        print("Error: OpenCode CLI not found", file=__import__('sys').stderr)
        sys.exit(1)
    
    # Call
    response = client.call(prompt, timeout)
    
    if response:
        print(response)
    else:
        print("Error: No response from OpenCode", file=__import__('sys').stderr)
        sys.exit(1)
