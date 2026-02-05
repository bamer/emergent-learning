#!/usr/bin/env python3
"""
OpenCode Connection Manager - Shared persistent-session adapter.

This keeps a single OpenCode session alive and exposes a minimal interface
compatible with previous helpers.
"""

import threading
from typing import Optional, Dict, Any, List

from Open_ELF.orchestrator.opencode_client import get_opencode_client


_instance = None
_instance_lock = threading.Lock()


class OpenCodeConnection:
    """Minimal connection adapter using the shared persistent session."""

    def __init__(
        self,
        base_url: str = "http://localhost:4096",
        timeout: int = 30,
        model: str = "opencode/big-pickle",
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.model = model
        self._client = get_opencode_client()

    def create_session(self, title: str = "elf-session") -> Optional[str]:
        return "persistent-session"

    def send_message(
        self, session_id: str, message: str, model: str = None, timeout: int = None
    ) -> Optional[str]:
        success, response = self._client.send_message(message)
        if not success:
            return None
        return response

    def close_session(self, session_id: str) -> bool:
        return True

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": "persistent-session",
                "title": "persistent",
                "created_at": None,
                "last_used": None,
                "message_count": None,
            }
        ]

    def is_healthy(self) -> bool:
        return self._client.health_check()


def get_opconnection(**kwargs) -> OpenCodeConnection:
    """Factory singleton."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = OpenCodeConnection(**kwargs)
    return _instance


def reset_opconnection():
    """Reset for tests."""
    global _instance
    with _instance_lock:
        _instance = None


__all__ = ["OpenCodeConnection", "get_opconnection", "reset_opconnection"]
