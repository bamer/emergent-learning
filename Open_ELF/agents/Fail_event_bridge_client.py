#!/usr/bin/env python3
"""
Event Bridge Client - Connects agents to the ELF Event Bridge

This client replaces the old opencode_client and provides a simple interface
for agents to communicate with the ELF system through the event bridge.
"""

import requests
import json
from typing import Optional, Dict, Any
import sys


class EventBridgeClient:
    """Client for communicating with the ELF Event Bridge."""

    def __init__(self, server_url: str = "http://localhost:9998"):
        self.server_url = server_url
        self.available = self._check_bridge()

    def _check_bridge(self) -> bool:
        """Check if Event Bridge is available."""
        try:
            resp = requests.get(f"{self.server_url}/status", timeout=2)
            return resp.status_code == 200
        except:
            return False

    def call(
        self,
        prompt: str,
        agent: Optional[str] = None,
        timeout: int = 120,
        component: str = "agent_execution",
        request_type: str = "agent_analysis",
    ) -> Optional[str]:
        """
        Call Event Bridge with a prompt.

        Args:
            prompt: The prompt to send
            agent: The agent type to use (e.g., "researcher", "CEO")
            timeout: Request timeout in seconds
            component: The component making the request
            request_type: The type of request being made

        Returns:
            The response from Event Bridge
        """
        if not self.available:
            print(
                f"Error: Event Bridge not available at {self.server_url}",
                file=sys.stderr,
            )
            return None

        try:
            payload = {
                "component": component,
                "request_type": request_type,
                "data": {
                    "prompt": prompt,
                    "agent": agent,
                    "timestamp": self._get_timestamp(),
                },
                "priority": 2,
            }

            resp = requests.post(
                f"{self.server_url}/api/v1/ask",
                json=payload,
                timeout=timeout,
            )

            if resp.status_code == 200:
                data = resp.json()
                # Extract response text
                if (
                    isinstance(data, dict)
                    and "data" in data
                    and "ai_analysis" in data["data"]
                ):
                    return data["data"]["ai_analysis"]
                elif isinstance(data, dict) and "data" in data and "analysis" in data["data"]:
                    return data["data"]["analysis"]
                elif isinstance(data, dict) and "response" in data:
                    return data["response"]
                else:
                    return json.dumps(data)

            return None

        except requests.exceptions.ConnectionError:
            print(
                f"Error: Cannot connect to Event Bridge at {self.server_url}",
                file=sys.stderr,
            )
            return None
        except requests.exceptions.Timeout:
            print(
                f"Error: Event Bridge request timed out (> {timeout}s)",
                file=sys.stderr,
            )
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_status(self) -> Dict[str, Any]:
        """Get Event Bridge status."""
        return {
            "bridge_available": self.available,
            "bridge_url": self.server_url,
        }


def call_event_bridge(
    prompt: str,
    agent: Optional[str] = None,
    timeout: int = 120,
    component: str = "agent_execution",
    request_type: str = "agent_analysis",
) -> Optional[str]:
    """Simple function to call Event Bridge."""
    client = EventBridgeClient()
    return client.call(
        prompt, agent, timeout, component, request_type
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: event_bridge_client.py <prompt> [agent] [timeout]")
        sys.exit(1)

    prompt = sys.argv[1]
    agent = sys.argv[2] if len(sys.argv) > 2 else None
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120

    client = EventBridgeClient()

    status = client.get_status()
    print(f"Event Bridge Status: {status}", file=sys.stderr)

    response = client.call(prompt, agent, timeout)

    if response:
        print(response)
    else:
        print("Error: No response from Event Bridge", file=sys.stderr)
        sys.exit(1)