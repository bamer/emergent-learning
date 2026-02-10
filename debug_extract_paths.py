#!/usr/bin/env python3
"""
Detailed debug script to trace the trail recording issue
"""

import sys
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

from core.learning_processor import LearningProcessor, ToolEvent


def debug_extract_file_paths():
    """Debug the _extract_file_paths method with various inputs"""
    print("=== Debugging _extract_file_paths ===")
    lp = LearningProcessor()

    test_cases = [
        ("Read", {"filePath": "/home/bamer/.opencode/emergent-learning/README.md"}),
        ("read", {"filePath": "/home/bamer/.opencode/emergent-learning/README.md"}),
        ("read", {"file_path": "/home/bamer/.opencode/emergent-learning/README.md"}),
        (
            "read",
            {
                "input": {
                    "filePath": "/home/bamer/.opencode/emergent-learning/README.md"
                }
            },
        ),
        (
            "read",
            {
                "input": {
                    "file_path": "/home/bamer/.opencode/emergent-learning/README.md"
                }
            },
        ),
        ("read", {}),
        ("bash", {"command": "ls /home/bamer/.opencode/emergent-learning/README.md"}),
        (
            "bash",
            {
                "input": {
                    "command": "ls /home/bamer/.opencode/emergent-learning/README.md"
                }
            },
        ),
        ("glob", {"pattern": "**/*.py"}),
        ("glob", {"input": {"pattern": "**/*.py"}}),
    ]

    for tool_name, tool_input in test_cases:
        print(f"\nTesting: {tool_name} with input: {tool_input}")
        paths = lp._extract_file_paths(tool_name, tool_input)
        print(f"  Extracted paths: {paths}")


if __name__ == "__main__":
    debug_extract_file_paths()
