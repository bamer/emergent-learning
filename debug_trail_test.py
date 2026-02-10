#!/usr/bin/env python3
"""
Debug script to test trail recording from EventBridge vs direct calls
"""

import sys
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

from core.learning_processor import LearningProcessor, ToolEvent


def test_direct_call():
    """Test direct call to LearningProcessor (known to work)"""
    print("=== Testing Direct Call ===")
    lp = LearningProcessor()

    test_event = ToolEvent(
        tool_name="Read",
        tool_input={"filePath": "/home/bamer/.opencode/emergent-learning/README.md"},
        tool_output={"content": "test content"},
    )

    result = lp.post_tool_process(test_event)
    print(f"Direct call result: {result}")
    return result


def test_eventbridge_structure():
    """Test with structure that EventBridge might be sending"""
    print("\n=== Testing EventBridge Structure ===")
    lp = LearningProcessor()

    # Simulate what EventBridge might be sending based on the logs
    test_event = ToolEvent(
        tool_name="read",
        tool_input={},  # Empty input - this could be the issue!
        tool_output={},
        session_id="test_session",
    )

    result = lp.post_tool_process(test_event)
    print(f"Empty input result: {result}")
    return result


def test_nested_structure():
    """Test with nested input structure that janitor modified _extract_file_paths to handle"""
    print("\n=== Testing Nested Structure ===")
    lp = LearningProcessor()

    # Test nested structure
    test_event = ToolEvent(
        tool_name="read",
        tool_input={
            "input": {"filePath": "/home/bamer/.opencode/emergent-learning/README.md"}
        },
        tool_output={"content": "test content"},
        session_id="test_session",
    )

    result = lp.post_tool_process(test_event)
    print(f"Nested structure result: {result}")
    return result


if __name__ == "__main__":
    test_direct_call()
    test_eventbridge_structure()
    test_nested_structure()
