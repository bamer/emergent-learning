#!/usr/bin/env python3
"""
Add minimal logging to post_tool_learning.py without breaking it
"""


def add_minimal_logging():
    """Add only essential logging calls"""
    with open("post_tool_learning.py", "r") as f:
        content = f.read()

    # Add simple logging import at the end of imports
    if "# Simple logging" not in content:
        # Find where to insert (after existing imports)
        insert_pos = content.find("from typing import List, Dict, Optional, Tuple")
        if insert_pos != -1:
            insert_pos = content.find("\n", insert_pos) + 1
            logging_code = """
# Simple logging
try:
    from simple_logger import log_start, log_success, log_error, log_info
except ImportError:
    def log_start(): pass
    def log_success(msg): pass
    def log_error(msg): pass
    def log_info(msg): pass
"""
            content = content[:insert_pos] + logging_code + content[insert_pos:]

    # Add logging at key points
    if "def main():" in content and "log_start()" not in content:
        content = content.replace(
            'def main():\n    """Main hook logic."""',
            'def main():\n    """Main hook logic."""\n    log_start()',
        )

    # Add success logging at the end
    if "output_result({})" in content and "log_success" not in content:
        content = content.replace(
            "output_result({})", 'log_success("Hook completed")\n    output_result({})'
        )

    # Add error logging
    if "RuntimeError(error_msg) from e" in content:
        content = content.replace(
            "raise RuntimeError(error_msg) from e",
            "log_error(error_msg)\n        raise RuntimeError(error_msg) from e",
        )

    with open("post_tool_learning.py", "w") as f:
        f.write(content)

    print("✓ Added minimal logging to post_tool_learning.py")


if __name__ == "__main__":
    add_minimal_logging()
