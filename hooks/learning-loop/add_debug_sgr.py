#!/usr/bin/env python3
"""
Add simple debug logging to sync-golden-rules.py
"""


def add_debug_logging():
    with open("../post_tool_use/sync-golden-rules.py", "r") as f:
        content = f.read()

    # Add debug at run function start
    if "def run():" in content and "[DEBUG]" not in content:
        content = content.replace(
            "def run():",
            'def run():\n    # Debug log\n    from datetime import datetime\n    from pathlib import Path\n    LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"\n    LOG_DIR.mkdir(parents=True, exist_ok=True)\n    with open(LOG_DIR / f"{datetime.now().strftime("%Y%m%d")}.log", "a") as f:\n        f.write(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DEBUG] sync-golden-rules START\\n")',
        )

    with open("../post_tool_use/sync-golden-rules.py", "w") as f:
        f.write(content)

    print("✓ Added debug logging to sync-golden-rules.py")


if __name__ == "__main__":
    add_debug_logging()
