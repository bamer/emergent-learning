#!/usr/bin/env python3
"""
Post-Tool Learning Hook - Delegates to LearningProcessor

This hook is the entry point for post-tool learning. It simply:
1. Reads the tool event from stdin/args
2. Passes it to the centralized LearningProcessor
3. Returns any advisory warnings (but never blocks)

All learning logic is now centralized in LearningProcessor.

Usage:
    cat event.json | python3 post_tool_learning.py
    python3 post_tool_learning.py '{"tool_name": "Read", ...}'
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent.parent  # emergent-learning root
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

# Import centralized logging
try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_warning

    logger = get_logger("post_tool_hook")
except ImportError:
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("post_tool_hook")

# Import centralized LearningProcessor
learning_processor = None
try:
    from core.learning_processor import LearningProcessor, ToolEvent

    learning_processor = LearningProcessor()
    logger.info("✅ LearningProcessor loaded for post-tool hook")
except ImportError as e:
    logger.warning(f"⚠️ LearningProcessor not available: {e}")


def get_hook_input() -> dict:
    """Read hook input from stdin or command-line argument."""
    # Try stdin first
    try:
        if not sys.stdin.isatty():
            return json.load(sys.stdin)
    except (json.JSONDecodeError, IOError, ValueError):
        pass

    # Fallback: check command-line arguments
    if len(sys.argv) > 1:
        try:
            return json.loads(sys.argv[1])
        except (json.JSONDecodeError, ValueError):
            pass

    return {}


def output_result(result: dict):
    """Output hook result to stdout."""
    print(json.dumps(result))


def run_with_learning_processor(hook_input: dict) -> dict:
    """
    Run post-tool processing using the centralized LearningProcessor.
    This is the NEW preferred path.
    """
    if not learning_processor:
        logger.error("LearningProcessor not available")
        return {"error": "LearningProcessor not available"}

    try:
        tool_name = hook_input.get("tool_name", hook_input.get("tool", ""))
        tool_input = hook_input.get("tool_input", hook_input.get("input", {}))
        tool_output = hook_input.get("tool_output", hook_input.get("output", {}))

        # Create ToolEvent for LearningProcessor
        event = ToolEvent(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
        )

        # Process through LearningProcessor
        result = learning_processor.post_tool_process(event)

        logger.info(
            f"✅ LearningProcessor processed {tool_name}: outcome={result.get('outcome')}"
        )

        # Return advisory warnings if any (but never block)
        if result.get("advisory_warnings"):
            return {
                "decision": "approve",
                "advisory": {
                    "has_warnings": True,
                    "warnings": result["advisory_warnings"],
                },
            }

        return {"decision": "approve"}

    except Exception as e:
        logger.error(f"LearningProcessor error: {e}")
        return {"error": str(e)}


def run_legacy_mode(hook_input: dict) -> dict:
    """
    Legacy mode - kept for backwards compatibility if LearningProcessor fails.
    This is DEPRECATED and will be removed once LearningProcessor is fully tested.
    """
    logger.warning(
        "Using deprecated legacy mode - LearningProcessor should be used instead"
    )

    # Basic outcome detection (simplified)
    tool_output = hook_input.get("tool_output", {})
    content = ""

    if isinstance(tool_output, dict):
        content = tool_output.get("content", "")
    elif isinstance(tool_output, str):
        content = tool_output

    # Simple failure detection
    outcome = "success"
    if "error" in content.lower() or "exception" in content.lower():
        outcome = "failure"

    return {"decision": "approve", "outcome": outcome}


def main():
    """Main hook logic - delegate to LearningProcessor."""
    hook_input = get_hook_input()

    logger.debug(f"Hook called with tool: {hook_input.get('tool_name', 'unknown')}")

    # Try LearningProcessor first
    if learning_processor:
        result = run_with_learning_processor(hook_input)
    else:
        # Fallback to legacy mode
        result = run_legacy_mode(hook_input)

    # Output result (advisory only, never blocks)
    output_result(result)


if __name__ == "__main__":
    main()
