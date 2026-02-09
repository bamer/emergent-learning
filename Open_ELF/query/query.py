#!/usr/bin/env python3
"""
Emergent Learning Framework - Query System

This is a thin entry point that delegates to the async implementation in cli.py.
The actual query logic lives in core.py (async) with mixins in queries/.

For programmatic use:
    # Async API (preferred)
    from query.core import QuerySystem
    qs = await QuerySystem.create()
    result = await qs.build_context("task")
    await qs.cleanup()

For CLI use:
    python query.py --context
    python query.py --domain debugging --limit 5

REFACTORED: 2025-12-31
Previously a 2600-line monolith duplicating core.py.
Now delegates to cli.py which uses the async core.py internally.
"""

# Suppress verbose logging from migrations and database layers BEFORE any imports
import logging
import warnings

logging.getLogger("query.migrations").setLevel(logging.CRITICAL)
logging.getLogger("migrations").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(
    logging.CRITICAL
)  # Suppress unclosed session warnings
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Portable venv detection and re-exec
# If critical dependencies are missing, try to re-exec with the venv python
import os
import sys
from pathlib import Path


def _ensure_venv_python():
    """Re-exec with venv python if current python lacks dependencies.

      IMPORTANT: Skip re-exec when:
      1. Already in correct venv (dependencies available)
      2. Running in non-interactive mode (e.g., from agent subprocess)
    This prevents terminal window doubling and subprocess crashes.
    """
    # Check if we already have peewee_aio
    try:
        import peewee_aio

        return  # Already in correct environment
    except ImportError:
        pass

    # IMPORTANT: Skip re-exec when NOT in TTY (running from agent/scheduled task)
    # This prevents terminal window issues and subprocess crashes
    if not sys.stdout.isatty():
        # Running from agent subprocess - don't try to re-exec
        # Will fail gracefully later if dependencies missing
        return

    # If running in a batch/script context or no TTY, skip venv re-exec
    # to avoid spawning windows and subprocess issues
    if not (sys.stdin.isatty() or sys.stdout.isatty()):
        return

    # Find the .venv directory relative to this script
    script_dir = Path(__file__).resolve().parent
    venv_dir = script_dir.parent.parent.parent / ".venv"
    venv_python = None

    # Try common venv locations
    for possible_venv in [
        venv_dir,  # ../../.venv (repo root .venv)
        script_dir / ".venv",  # ./.venv
        Path.home()
        / ".opencode"
        / "emergent-learning"
        / ".venv",  # ~/.opencode/emergent-learning/.venv
    ]:
        if possible_venv.exists():
            # Try different python executable names
            for exe_name in ["python3", "python"]:
                candidate = possible_venv / "bin" / exe_name
                if candidate.exists():
                    venv_python = str(candidate)
                    break
            if venv_python:
                break

    if not venv_python:
        # No venv found, continue with current python (will likely fail later)
        return

    # Check if we're already running the venv python to avoid infinite re-exec
    current_python = sys.executable
    if current_python == venv_python:
        return  # Already in venv python, don't re-exec

    # Re-exec this script with venv python
    # Only re-exec if we're NOT already using the venv python
    try:
        os.execve(venv_python, [venv_python] + sys.argv, os.environ)
    except Exception as e:
        # If re-exec fails, just continue and let it fail normally later
        # This prevents crashes in subprocess contexts
        return


# Only run venv detection when executed as script, not when imported
if __name__ == "__main__":
    _ensure_venv_python()

# Handle both module import and script execution
try:
    # When imported as module: from query import QuerySystem
    from .core import QuerySystem
    from .exceptions import (
        QuerySystemError,
        ValidationError,
        DatabaseError,
        TimeoutError,
        ConfigurationError,
    )
    from .validators import (
        MAX_DOMAIN_LENGTH,
        MAX_QUERY_LENGTH,
        MAX_TAG_COUNT,
        MAX_TAG_LENGTH,
        MIN_LIMIT,
        MAX_LIMIT,
        DEFAULT_TIMEOUT,
        MAX_TOKENS,
    )
    from .formatters import format_output, generate_accountability_banner
    from .setup import ensure_hooks_installed, ensure_full_setup
    from .cli import main
except ImportError:
    # When run as script: python query.py --context
    from core import QuerySystem
    from exceptions import (
        QuerySystemError,
        ValidationError,
        DatabaseError,
        TimeoutError,
        ConfigurationError,
    )
    from validators import (
        MAX_DOMAIN_LENGTH,
        MAX_QUERY_LENGTH,
        MAX_TAG_COUNT,
        MAX_TAG_LENGTH,
        MIN_LIMIT,
        MAX_LIMIT,
        DEFAULT_TIMEOUT,
        MAX_TOKENS,
    )
    from formatters import format_output, generate_accountability_banner
    from setup import ensure_hooks_installed, ensure_full_setup
    from cli import main

__all__ = [
    # Core
    "QuerySystem",
    # Exceptions
    "QuerySystemError",
    "ValidationError",
    "DatabaseError",
    "TimeoutError",
    "ConfigurationError",
    # Constants
    "MAX_DOMAIN_LENGTH",
    "MAX_QUERY_LENGTH",
    "MAX_TAG_COUNT",
    "MAX_TAG_LENGTH",
    "MIN_LIMIT",
    "MAX_LIMIT",
    "DEFAULT_TIMEOUT",
    "MAX_TOKENS",
    # Utilities
    "format_output",
    "generate_accountability_banner",
    "ensure_hooks_installed",
    "ensure_full_setup",
    # CLI
    "main",
]

if __name__ == "__main__":
    # When run as script, delegate to cli.main()
    exit(main())
