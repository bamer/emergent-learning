#!/usr/bin/env python3
"""
ELF AI Client - Uses the ELF backend to call AI

The ELF backend (localhost:8888) has built-in AI integration.
We can use it to analyze experiments.

Since ELF uses opencode/big-pickle, we interface through the backend.
"""

import requests
import json
from typing import Optional, Dict, Any
import sys

class ELFAIClient:
    """Client for ELF backend AI access."""
    
    def __init__(self, backend_url: str = "http://localhost:8888", model: str = "opencode/big-pickle"):
        self.backend_url = backend_url
        self.model = model
        self.available = self._check_backend()
    
    def _check_backend(self) -> bool:
        """Check if ELF backend is available."""
        try:
            resp = requests.get(f"{self.backend_url}/api/health", timeout=2)
            return resp.status_code == 200
        except:
            pass
        
        # Try alternative health endpoint
        try:
            resp = requests.get(f"{self.backend_url}/", timeout=2)
            return resp.status_code in [200, 404]  # 404 is ok, means server is there
        except:
            return False
    
    def call(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """
        Call ELF backend with a prompt.
        
        Since ELF has opencode/big-pickle integrated, we can query it directly.
        """
        if not self.available:
            print("Error: ELF backend not available at " + self.backend_url, file=sys.stderr)
            return None
        
        try:
            # ELF backend likely has an /api/analyze or similar endpoint
            # For now, we'll try a generic approach
            
            payload = {
                "prompt": prompt,
                "model": self.model,
                "system": "You are an expert experiment analyzer. Provide analysis in JSON format."
            }
            
            # Try /api/analyze endpoint (if it exists)
            resp = requests.post(
                f"{self.backend_url}/api/analyze",
                json=payload,
                timeout=timeout
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # Extract response text
                if isinstance(data, dict) and "response" in data:
                    return data["response"]
                elif isinstance(data, dict) and "text" in data:
                    return data["text"]
                else:
                    return json.dumps(data)
            
            return None
            
        except requests.exceptions.ConnectionError:
            print(f"Error: Cannot connect to ELF backend at {self.backend_url}", file=sys.stderr)
            return None
        except requests.exceptions.Timeout:
            print(f"Error: ELF backend request timed out (>{timeout}s)", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get ELF backend status."""
        return {
            "backend_available": self.available,
            "backend_url": self.backend_url,
            "model": self.model
        }

def call_elf_ai(prompt: str, model: str = "opencode/big-pickle", timeout: int = 120) -> Optional[str]:
    """Simple function to call ELF AI."""
    client = ELFAIClient(model=model)
    return client.call(prompt, timeout)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: elf_ai_client.py <prompt> [model] [timeout]")
        sys.exit(1)
    
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "opencode/big-pickle"
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    
    client = ELFAIClient(model=model)
    
    status = client.get_status()
    print(f"ELF Status: {status}", file=sys.stderr)
    
    response = client.call(prompt, timeout)
    
    if response:
        print(response)
    else:
        print("Error: No response from ELF backend", file=sys.stderr)
        sys.exit(1)
