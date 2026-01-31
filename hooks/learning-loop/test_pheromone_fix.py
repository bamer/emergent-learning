#!/usr/bin/env python3
"""
Test pheromone recording fix
"""

import json
import subprocess
from datetime import datetime

# Test record_pheromone with a valid file path
test_context = {
    "tool_name": "Read",
    "tool_input": "./post_tool_learning.py",  # File within ELF directory
    "timestamp": datetime.now().isoformat(),
}

print("Testing pheromone recording...")
print(f"Test context: {test_context}")

# Run the record_pheromone script (test both stdin and argv)
result = subprocess.run(
    ["python3", "record_pheromone.py", json.dumps(test_context)],
    text=True,
    capture_output=True,
)

# Also test with stdin
result_stdin = subprocess.run(
    ["python3", "record_pheromone.py"],
    input=json.dumps(test_context),
    text=True,
    capture_output=True,
)

print(f"Return code: {result.returncode}")
if result.stderr:
    print(f"STDERR: {result.stderr}")
else:
    print("✅ No SQL constraint error!")

# Verify the trail was recorded
import sqlite3
from pathlib import Path

conn = sqlite3.connect("/home/bamer/.opencode/emergent-learning/memory/index.db")
cursor = conn.cursor()

# The stored path is the resolved absolute path
test_file = Path(test_context["tool_input"]).expanduser().resolve()
cursor.execute(
    "SELECT COUNT(*) FROM pheromone_trails WHERE file_path = ?", (str(test_file),)
)
count = cursor.fetchone()[0]

print(f"Looking for: {test_file}")
cursor.execute(
    "SELECT file_path, tool_name, access_count FROM pheromone_trails ORDER BY id DESC LIMIT 5"
)
trails = cursor.fetchall()
print("Recent trails:")
for trail in trails:
    print(f"  - {trail[0]} ({trail[1]}) - {trail[2]} accesses")

conn.close()

print(f"Trails recorded for file: {count}")
if count > 0:
    print("✅ Pheromone trail recording FIXED!")
else:
    print("❌ Trail recording still failing")
