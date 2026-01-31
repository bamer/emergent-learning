#!/usr/bin/env python3
"""
Add simple debug logging to record_pheromone.py
"""


def add_debug_logging():
    with open("record_pheromone.py", "r") as f:
        content = f.read()

    # Add debug at main start
    if "def main():" in content and "[DEBUG]" not in content:
        content = content.replace(
            "def main():",
            'def main():\n    # Debug log\n    from datetime import datetime\n    from pathlib import Path\n    LOG_DIR = Path.home() / ".opencode" / "emergent-learning" / "logs"\n    LOG_DIR.mkdir(parents=True, exist_ok=True)\n    with open(LOG_DIR / f"{datetime.now().strftime("%Y%m%d")}.log", "a") as f:\n        f.write(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DEBUG] record_pheromone START\\n")',
        )

    with open("record_pheromone.py", "w") as f:
        f.write(content)

    print("✓ Added debug logging to record_pheromone.py")


if __name__ == "__main__":
    add_debug_logging()
