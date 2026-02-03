#!/usr/bin/env python3
"""
ELF Watcher Launcher

Orchestrates the tiered watcher system:
- Runs tier 1 (fast) in a loop every 30 seconds
- Escalates to tier 2 (deep) when exit code = 1
- Retries when exit code = 2 (error)
- Handles graceful shutdown

Based on original ELF design from:
https://github.com/Spacehunterz/Emergent-Learning-Framework_ELF/blob/main/src/watcher/README.md
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from datetime import datetime

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
# Path structure: Open_ELF/watcher/launcher.py -> emergent-learning root
ELF_DIR = (
    SCRIPT_DIR.parent.parent
)  # Go up 2 levels: watcher -> Open_ELF -> emergent-learning
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Import centralized logger
try:
    from agents.logger import setup_logger, log_critical_error

    watcher_logger = setup_logger("watcher")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    watcher_logger = logging.getLogger("watcher")

    def log_critical_error(component: str, message: str):
        watcher_logger.error(f"[CRITICAL ERROR] {component}: {message}")


# Import config values
try:
    # When run as module: relative import
    from Open_ELF.watcher.config import (
        POLL_INTERVAL,
        HEARTBEAT_TIMEOUT,
        OPENCODE_SERVER_URL,
        OPENCODE_MODEL,
        EXIT_NORMAL,
        EXIT_INTERVENTION,
        EXIT_ERROR,
    )
except ImportError:
    # When run directly: hardcoded fallback values
    POLL_INTERVAL: int = 30
    HEARTBEAT_TIMEOUT: int = 120
    OPENCODE_SERVER_URL: str = "http://localhost:4096"
    OPENCODE_MODEL: str = "opencode/big-pickle"
    EXIT_NORMAL: int = 0
    EXIT_INTERVENTION: int = 1
    EXIT_ERROR: int = 2

# Import OpenCode client
try:
    from agents.opencode_client import OpenCodeClient
except ImportError:
    OpenCodeClient = None
    watcher_logger.warning(
        "opencode_client not available, will not be able to call OpenCode"
    )

# Paths
COORDINATION_DIR = ELF_DIR / ".coordination"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"
STOP_FILE = COORDINATION_DIR / "watcher-stop"
LAUNCHER_LOG = COORDINATION_DIR / "launcher.log"

# Ensure coordination dir exists
COORDINATION_DIR.mkdir(parents=True, exist_ok=True)


def resolve_server_url() -> str:
    """Resolve OpenCode server URL."""
    return os.environ.get("OPENCODE_SERVER_URL") or OPENCODE_SERVER_URL


def resolve_model() -> str:
    """Resolve OpenCode model to use (same for both tiers, adapts via prompt)."""
    return os.environ.get("OPENCODE_WATCHER_MODEL") or OPENCODE_MODEL


def get_opencode_client() -> Any:
    """Get or create OpenCode client."""
    if OpenCodeClient is None:
        return None

    server_url = resolve_server_url()
    model = resolve_model()
    return OpenCodeClient(model=model, server_url=server_url)


def fetch_prompt(prompt_type: str = "prompt") -> str:
    """Fetch watcher prompt from watcher_loop.py."""
    script_path = SCRIPT_DIR / "watcher_loop.py"
    result = subprocess.run(
        [sys.executable, str(script_path), prompt_type],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def call_opencode(prompt: str, timeout: int = 300) -> Tuple[str, bool]:
    """Call OpenCode via client (API or CLI)."""
    client = get_opencode_client()
    if client is None:
        return "Error: OpenCode client not available", False

    response = client.call(prompt=prompt, timeout=timeout)

    if response is None:
        return "Error: OpenCode call failed (check server)", False

    return response, True


def append_log(text: str) -> None:
    """Append text to watcher log and also log to centralized logger."""
    existing = WATCHER_LOG.read_text() if WATCHER_LOG.exists() else ""
    WATCHER_LOG.write_text(existing + text + "\n")
    watcher_logger.info(text)


def parse_exit_code_from_summary(response: str) -> int:
    """Extract exit code from watcher summary.

    Based on watcher prompt spec:
    - STATUS: nominal or stopped = exit code 0 (check again)
    - STATUS: stale or error = exit code 1 (escalation needed)
    """
    for line in response.splitlines():
        if "STATUS:" in line:
            status = line.split("STATUS:")[-1].strip().lower()
            if status in ("nominal", "stopped"):
                return EXIT_NORMAL
            elif status in ("stale", "error"):
                return EXIT_INTERVENTION
            else:
                # Unknown status, treat as error
                return EXIT_ERROR
    # If no status found, treat as error
    return EXIT_ERROR


def run_tier1(server_url: str, model: str) -> Tuple[int, str]:
    """Run tier 1 watcher (fast, frequent checks)."""
    prompt = fetch_prompt("prompt")

    watcher_logger.info("[TIER 1] Starting watcher check...")
    print(f"[TIER 1] Checking system state...", file=sys.stderr)

    response, success = call_opencode(prompt)

    if not success:
        watcher_logger.error(f"[TIER 1 ERROR] {response}")
        return EXIT_ERROR, response

    # Log response
    append_log(f"[TIER 1] {response[:200]}")
    print(response)  # Full response to stdout

    # Parse exit code from summary
    exit_code = parse_exit_code_from_summary(response)
    watcher_logger.info(f"[TIER 1] Exit code: {exit_code}")

    return exit_code, response


def run_tier2(server_url: str, model: str, escalation_context: str) -> int:
    """Run tier 2 handler (deep analysis)."""
    handler_prompt = fetch_prompt("handler-prompt")

    watcher_logger.info("[TIER 2] Starting deep analysis...")
    print(f"\n[TIER 2] Escalating to handler for deep analysis...", file=sys.stderr)

    response, success = call_opencode(handler_prompt)

    if not success:
        watcher_logger.error(f"[TIER 2 ERROR] {response}")
        return EXIT_ERROR

    # Log response
    append_log(f"[TIER 2] {response[:200]}")
    print(response)  # Full response to stdout

    watcher_logger.info("[TIER 2] Deep analysis complete")
    return EXIT_NORMAL


def main() -> int:
    """Main entry point - runs tier 1 in loop with tier 2 escalation."""
    server_url = resolve_server_url()
    model = resolve_model()  # Single model for both tiers

    watcher_logger.info("=== ELF Watcher Starting ===")
    watcher_logger.info(f"Server: {server_url}")
    watcher_logger.info(f"Model: {model} (adapts to prompt depth)")
    watcher_logger.info(f"Poll interval: {POLL_INTERVAL}s")

    print(f"Starting ELF Watcher (Tiered)", file=sys.stderr)
    print(f"Server: {server_url}", file=sys.stderr)
    print(f"Model: {model} (adapts to prompt depth)", file=sys.stderr)
    print(f"Tier 1: Fast checks (every {POLL_INTERVAL}s)", file=sys.stderr)
    print(f"Tier 2: Deep analysis (escalation only)", file=sys.stderr)
    print(f"Stop file: {STOP_FILE}", file=sys.stderr)
    print("", file=sys.stderr)

    # Main monitoring loop
    while True:
        # Check for stop signal
        if STOP_FILE.exists():
            watcher_logger.info("Stop file detected, exiting gracefully")
            print("\nStop file detected, exiting.", file=sys.stderr)
            return EXIT_NORMAL

        try:
            # Run tier 1 watcher
            exit_code, response = run_tier1(server_url, model)

            if exit_code == EXIT_INTERVENTION:
                # Escalate to tier 2
                watcher_logger.info(
                    "Tier 1 requested intervention, escalating to tier 2"
                )
                exit_code = run_tier2(server_url, model, response)

                if exit_code == EXIT_ERROR:
                    watcher_logger.error("Tier 2 failed, will retry next cycle")
                    # Continue loop (will retry in next cycle)
                else:
                    watcher_logger.info("Tier 2 completed successfully")

            elif exit_code == EXIT_ERROR:
                watcher_logger.error("Tier 1 failed with error, will retry next cycle")
                # Continue loop (will retry in next cycle)

            # If EXIT_NORMAL, just continue loop

        except KeyboardInterrupt:
            watcher_logger.info("Received SIGINT, exiting gracefully")
            print("\nReceived interrupt signal, exiting.", file=sys.stderr)
            return EXIT_NORMAL
        except Exception as e:
            watcher_logger.error(f"Unexpected error: {e}", exc_info=True)
            log_critical_error("watcher", f"Unexpected error in main loop: {e}")
            # Continue loop (attempt to recover)

        # Wait for next cycle
        watcher_logger.info(f"Sleeping {POLL_INTERVAL}s until next check...")
        print(f"\nSleeping {POLL_INTERVAL}s...", file=sys.stderr)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
