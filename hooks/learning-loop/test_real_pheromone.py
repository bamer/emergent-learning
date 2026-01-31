#!/usr/bin/env python3
"""
Final test of pheromone recording with real tool input
"""

import json
import subprocess
from datetime import datetime

# Test with realistic tool input
test_contexts = [
    {
        "tool_name": "Read",
        "tool_input": {
            "file_path": "/home/bamer/.opencode/emergent-learning/README.md"
        },
        "timestamp": datetime.now().isoformat(),
    },
    {
        "tool_name": "Grep",
        "tool_input": {
            "pattern": "test",
            "path": "/home/bamer/.opencode/emergent-learning/",
        },
        "timestamp": datetime.now().isoformat(),
    },
    {
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la /home/bamer/.opencode/emergent-learning/"},
        "timestamp": datetime.now().isoformat(),
    },
]

for i, context in enumerate(test_contexts):
    print(f"\n--- Test {i + 1}: {context['tool_name']} ---")

    # Test with stdin
    result = subprocess.run(
        ["python3", "record_pheromone.py"],
        input=json.dumps(context),
        text=True,
        capture_output=True,
    )

    print(f"Return code: {result.returncode}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")

    # Check trails
    import sqlite3

    conn = sqlite3.connect("/home/bamer/.opencode/emergent-learning/memory/index.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pheromone_trails")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"Total trails in DB: {count}")
