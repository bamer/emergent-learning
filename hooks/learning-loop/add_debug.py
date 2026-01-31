#!/usr/bin/env python3
"""
Add simple debug logging to post_tool_learning.py
"""


def add_debug_logging():
    """Add debug logging at key points"""
    with open("post_tool_learning.py", "r") as f:
        content = f.read()

    # Add debug logging function at the start
    if "def debug_log(" not in content:
        debug_function = '''
def debug_log(msg):
    """Simple debug log function"""
    import sys
    from datetime import datetime
    from pathlib import Path
    
    LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] [DEBUG] [post_tool_learning] {msg}\\n")

'''
        # Insert after imports
        insert_pos = content.find("# Import trail helper")
        if insert_pos != -1:
            content = (
                content[:insert_pos] + debug_function + "\n" + content[insert_pos:]
            )

    # Add debug calls at key points
    if "def main():" in content:
        content = content.replace(
            'def main():\n    """Main hook logic."""',
            'def main():\n    """Main hook logic."""\n    debug_log("=== FUNCTION START ===")',
        )

    # Add logging for tool_name
    if 'tool_name = hook_input.get("tool_name"' in content:
        content = content.replace(
            'tool_name = hook_input.get("tool_name", hook_input.get("tool"))',
            'tool_name = hook_input.get("tool_name", hook_input.get("tool"))\n    debug_log(f"Tool: {tool_name}")',
        )

    # Add success logging
    if "output_result({})" in content:
        content = content.replace(
            "output_result({})",
            'debug_log("=== FUNCTION END SUCCESS ===")\n    output_result({})',
        )

    with open("post_tool_learning.py", "w") as f:
        f.write(content)

    print("✓ Added debug logging to post_tool_learning.py")


if __name__ == "__main__":
    add_debug_logging()
