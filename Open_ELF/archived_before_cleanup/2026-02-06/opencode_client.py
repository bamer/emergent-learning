#!/usr/bin/env python3
"""
OpenCode Client - Shared persistent-session wrapper.

All ELF components should use this wrapper so we reuse a single OpenCode
session and avoid spawning new sessions on every call.
"""

from typing import Optional, Dict, Any

from Open_ELF.orchestrator.opencode_client import get_opencode_client


class OpenCodeClient:
    """Shared OpenCode client wrapper (persistent session)."""

    def __init__(
        self,
        model: str = "llama/nemotron-v3-coder",
        server_url: str = "http://localhost:4096",
        prefer_cli: bool = True,
    ):
        self.model = model
        self.server_url = server_url
        self.prefer_cli = prefer_cli
        self._client = get_opencode_client()

    def call(
        self, prompt: str, timeout: int = 300, agent: Optional[str] = None
    ) -> Optional[str]:
        """Send a prompt through the shared persistent session."""
        success, response = self._client.send_message(prompt, agent)
        if not success:
            return None
        return response

    def get_status(self) -> Dict[str, Any]:
        """Get OpenCode status."""
        return {
            "server_available": self._client.health_check(),
            "cli_available": False,
            "model": self.model,
            "server_url": self.server_url,
            "method": "Persistent session (shared)",
        }


def call_opencode(
    prompt: str, model: str = "llama/nemotron-v3-coder", timeout: int = 120
) -> Optional[str]:
    """Simple function to call OpenCode using the shared client."""
    client = OpenCodeClient(model=model)
    return client.call(prompt, timeout)
