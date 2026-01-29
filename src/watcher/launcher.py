#!/usr/bin/env python3
"""
OpenCode watcher launcher using big-pickle model.

Uses the opencode CLI with big-pickle model for both Tier 1 (watcher) and Tier 2 (handler).
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from elf_paths import get_base_path

COORDINATION_DIR = Path(os.environ.get("ELF_BASE_PATH", str(get_base_path()))) / ".coordination"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"
STOP_FILE = COORDINATION_DIR / "watcher-stop"

DEFAULT_MODEL = "opencode/big-pickle"
DEFAULT_INTERVAL = 30


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


def call_opencode(model: str, prompt: str) -> Tuple[str, bool]:
    """Call opencode CLI with the given model and prompt."""
    try:
        result = subprocess.run(
            ["opencode", "--model", model, "--prompt", prompt],
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
        return "Error: opencode CLI not found. Install with: npm install -g opencode", False
    except Exception as e:
        return f"Error calling opencode: {e}", False


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


def run_single_pass(model: str) -> int:
    """Run one watcher monitoring pass."""
    print(f"[WATCHER] Fetching prompt...", file=sys.stderr)
    
    # Get watcher prompt
    prompt = fetch_prompt("prompt")
    print(f"[WATCHER] Sending to {model}...", file=sys.stderr)
    
    # Call OpenCode with watcher prompt
    response, success = call_opencode(model, prompt)
    
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
        handler_response, success = call_opencode(model, handler_prompt)
        
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
    model = resolve_model()
    interval = resolve_interval()
    once = "--once" in sys.argv

    print(f"Starting OpenCode Watcher with model: {model}", file=sys.stderr)
    print(f"Interval: {interval}s", file=sys.stderr)

    while True:
        if STOP_FILE.exists():
            print("Stop file detected, exiting.", file=sys.stderr)
            return 0
        
        exit_code = run_single_pass(model)
        
        if exit_code != 0 or once:
            return exit_code
        
        print(f"Sleeping {interval}s...", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
