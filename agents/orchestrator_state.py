"""
ELF Orchestrator State Persistence
==================================

Handles persistence of orchestrator state to disk so that:
1. Multiple API calls can read the current state
2. The orchestrator can recover from crashes
3. Dashboard can display real-time agent status

State is stored in: /home/bamer/.opencode/emergent-learning/.coordination/orchestrator-state.json
"""

import json
import fcntl
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# State file location
STATE_DIR = Path("/home/bamer/.opencode/emergent-learning/.coordination")
STATE_FILE = STATE_DIR / "orchestrator-state.json"
LOCK_FILE = STATE_DIR / "orchestrator-state.lock"


class OrchestratorState:
    """Manages persistent state for the orchestrator."""

    def __init__(self):
        self._ensure_directories()
        self._lock_fd = None

    def _ensure_directories(self):
        """Ensure state directories exist."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self):
        """Acquire exclusive lock for state file access."""
        try:
            self._lock_fd = open(LOCK_FILE, "w")
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            return False

    def _release_lock(self):
        """Release the lock file."""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
            except Exception:
                pass
            finally:
                self._lock_fd = None

    def save_state(self, state: Dict[str, Any]):
        """
        Save orchestrator state to disk.

        Args:
            state: Dictionary containing orchestrator state
        """
        if not self._acquire_lock():
            return False

        try:
            # Add timestamp
            state["_last_updated"] = datetime.now().isoformat()

            # Write atomically
            temp_file = STATE_FILE.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(state, f, indent=2)
            temp_file.replace(STATE_FILE)

            return True
        except Exception as e:
            print(f"Error saving state: {e}", file=__import__("sys").stderr)
            return False
        finally:
            self._release_lock()

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load orchestrator state from disk.

        Returns:
            State dictionary or None if not found
        """
        if not STATE_FILE.exists():
            return None

        if not self._acquire_lock():
            # If can't acquire lock, try to read anyway (might be stale but better than nothing)
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except Exception:
                return None

        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state: {e}", file=__import__("sys").stderr)
            return None
        finally:
            self._release_lock()

    def update_agent_status(self, agent_type: str, status: Dict[str, Any]):
        """
        Update status for a specific agent.

        Args:
            agent_type: Type of agent (e.g., 'sentinel', 'watcher')
            status: Agent status dictionary
        """
        state = self.load_state() or {}

        if "agents" not in state:
            state["agents"] = {}

        state["agents"][agent_type] = status
        state["_last_updated"] = datetime.now().isoformat()

        self.save_state(state)

    def get_agent_status(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get status for a specific agent.

        Args:
            agent_type: Type of agent

        Returns:
            Agent status or None
        """
        state = self.load_state()
        if not state:
            return None

        return state.get("agents", {}).get(agent_type)

    def clear_state(self):
        """Clear all state (useful for shutdown)."""
        if STATE_FILE.exists():
            try:
                STATE_FILE.unlink()
            except Exception:
                pass


# Global state instance
_state_instance = None


def get_state() -> OrchestratorState:
    """Get global state instance."""
    global _state_instance
    if _state_instance is None:
        _state_instance = OrchestratorState()
    return _state_instance
