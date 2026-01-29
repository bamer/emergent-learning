#!/usr/bin/env python3
"""
OpenCode watcher launcher using HTTP API on port 4096.

Uses the OpenCode HTTP API with big-pickle model for both Tier 1 (watcher) and Tier 2 (handler).
Replaces CLI with direct API calls for better performance and reliability.
"""

import json
import os
import sys
import time
import requests
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]  # emergent-learning dir
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Add src to path for local imports
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import the HTTP-based OpenCode client
AGENTS_DIR = ROOT_DIR / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

try:
    from opencode_client import OpenCodeClient
except ImportError:
    OpenCodeClient = None

from elf_paths import get_base_path

COORDINATION_DIR = Path(os.environ.get("ELF_BASE_PATH", str(get_base_path()))) / ".coordination"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"
STOP_FILE = COORDINATION_DIR / "watcher-stop"

DEFAULT_SERVER_URL = "http://localhost:4096"
DEFAULT_MODEL = "opencode/big-pickle"
DEFAULT_INTERVAL = 30


def resolve_server_url() -> str:
    """Resolve the OpenCode server URL."""
    return os.environ.get("OPENCODE_SERVER_URL") or DEFAULT_SERVER_URL


def resolve_model() -> str:
    """Resolve the OpenCode model to use."""
    return os.environ.get("OPENCODE_WATCHER_MODEL") or DEFAULT_MODEL


def resolve_interval() -> int:
    """Resolve the watcher interval."""
    value = os.environ.get("OPENCODE_WATCHER_INTERVAL")
    if not value:
        return DEFAULT_INTERVAL
    try:
        return int(value)
    except ValueError:
        return DEFAULT_INTERVAL


def fetch_prompt(prompt_type: str = "prompt") -> str:
    """Fetch watcher prompt from watcher_loop.py."""
    script_path = Path(__file__).with_name("watcher_loop.py")
    result = subprocess.run(
        [sys.executable, str(script_path), prompt_type],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def call_opencode_http(server_url: str, model: str, prompt: str, timeout: int = 300) -> Tuple[str, bool]:
    """Call OpenCode via HTTP API on port 4096."""
    try:
        # Create session
        session_resp = requests.post(
            f"{server_url}/session",
            json={"title": "watcher"},
            timeout=10
        )
        
        if session_resp.status_code != 201 and session_resp.status_code != 200:
            return f"Error: Failed to create session ({session_resp.status_code})", False
        
        session_data = session_resp.json()
        session_id = session_data.get("id")
        
        if not session_id:
            return f"Error: No session ID in response: {session_data}", False
        
        # Send message
        message_resp = requests.post(
            f"{server_url}/session/{session_id}/message",
            json={
                "model": {"provider": "opencode", "providerID": "opencode", "modelID": "big-pickle"},
                "parts": [{"type": "text", "text": prompt}]
            },
            timeout=timeout
        )
        
        if message_resp.status_code != 200:
            return f"Error: Failed to send message ({message_resp.status_code}): {message_resp.text}", False
        
        # Extract response
        response_data = message_resp.json()
        parts = response_data.get("parts", [])
        response = ""
        for part in parts:
            if part.get("type") == "text":
                response += part.get("text", "")
        
        # Cleanup session
        try:
            requests.delete(
                f"{server_url}/session/{session_id}",
                timeout=5
            )
        except Exception:
            pass
        
        return (response.strip() if response else "No response from OpenCode"), (bool(response))
        
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to OpenCode server at {server_url}\nStart with: opencode serve --port 4096", False
    except requests.exceptions.Timeout:
        return f"Error: OpenCode request timed out (>{timeout}s)", False
    except Exception as e:
        return f"Error calling OpenCode HTTP API: {e}", False


def call_opencode_fallback(model: str, prompt: str) -> Tuple[str, bool]:
    """Fallback to CLI if HTTP API is unavailable."""
    try:
        result = subprocess.run(
            ["opencode", model, prompt],
            capture_output=True,
            timeout=300,
            text=True,
        )
        
        if result.returncode == 0:
            return result.stdout, True
        else:
            return f"Error: opencode returned error code {result.returncode}\n{result.stderr}", False
    except subprocess.TimeoutExpired:
        return "Error: opencode request timed out (>300s)", False
    except FileNotFoundError:
        return "Error: opencode CLI not found. Start HTTP server with: opencode serve --port 4096", False
    except Exception as e:
        return f"Error calling opencode CLI: {e}", False


def append_log(text: str) -> None:
    """Append text to watcher log."""
    COORDINATION_DIR.mkdir(parents=True, exist_ok=True)
    existing = WATCHER_LOG.read_text() if WATCHER_LOG.exists() else ""
    WATCHER_LOG.write_text(existing + text + "\n")


def should_stop(response: str) -> bool:
    """Check if watcher should stop."""
    if STOP_FILE.exists():
        return True
    for line in response.splitlines():
        if line.strip().upper().startswith("STATUS:"):
            status = line.split(":", 1)[-1].strip().lower()
            if status in {"complete", "stopped"}:
                return True
    return False


def run_single_pass(server_url: str, model: str) -> int:
    """Run one watcher monitoring pass."""
    print(f"[WATCHER] Fetching prompt...", file=sys.stderr)
    
    # Get watcher prompt
    prompt = fetch_prompt("prompt")
    print(f"[WATCHER] Sending to {model} via {server_url}...", file=sys.stderr)
    
    # Call OpenCode via HTTP API, fallback to CLI
    response, success = call_opencode_http(server_url, model, prompt)
    
    if not success:
        print(f"[WATCHER] HTTP API failed, trying CLI fallback...", file=sys.stderr)
        response, success = call_opencode_fallback(model, prompt)
    
    if not success:
        print(f"Error: {response}", file=sys.stderr)
        append_log(f"[TIER 1 ERROR] {response}")
        return 2
    
    # Output and log response
    print(response)
    append_log(f"[TIER 1 WATCHER] {response[:200]}")
    
    # Check if escalation needed
    if should_stop(response):
        return 0
    
    # Check if handler escalation needed
    needs_handler = any(x in response for x in ["STATUS: error", "STATUS: stale", "STATUS: complete"])
    
    if needs_handler:
        print(f"\n[HANDLER] Escalating to handler (Tier 2)...", file=sys.stderr)
        
        # Get handler prompt
        handler_prompt = fetch_prompt("handler-prompt")
        handler_response, success = call_opencode_http(server_url, model, handler_prompt)
        
        if not success:
            print(f"[HANDLER] HTTP API failed, trying CLI fallback...", file=sys.stderr)
            handler_response, success = call_opencode_fallback(model, handler_prompt)
        
        if not success:
            print(f"Error: {handler_response}", file=sys.stderr)
            append_log(f"[TIER 2 ERROR] {handler_response}")
            return 2
        
        # Output and log handler response
        print(f"\n{handler_response}")
        append_log(f"[TIER 2 HANDLER] {handler_response[:200]}")
        
        # Return 1 if ESCALATE action was taken
        if "ESCALATE" in handler_response:
            return 1
    
    return 0


def main() -> int:
    """Main entry point."""
    server_url = resolve_server_url()
    model = resolve_model()
    interval = resolve_interval()
    once = "--once" in sys.argv

    print(f"Starting OpenCode Watcher (HTTP API)", file=sys.stderr)
    print(f"Server URL: {server_url}", file=sys.stderr)
    print(f"Model: {model}", file=sys.stderr)
    print(f"Interval: {interval}s", file=sys.stderr)
    print(f"Note: Make sure OpenCode server is running: opencode serve --port 4096", file=sys.stderr)

    while True:
        if STOP_FILE.exists():
            print("Stop file detected, exiting.", file=sys.stderr)
            return 0
        
        exit_code = run_single_pass(server_url, model)
        
        if exit_code != 0 or once:
            return exit_code
        
        print(f"Sleeping {interval}s...", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
