#!/usr/bin/env python3
"""
Direct test of record_pheromone with stdin input
"""

import json
import subprocess

# Create test context
context = {
    "tool_name": "Read",
    "tool_input": {"file_path": "/home/bamer/.opencode/emergent-learning/README.md"},
    "timestamp": "2026-01-31T14:30:00",
}

print(f"Testing with context: {context}")

# Test with stdin
result = subprocess.run(
    ["python3", "record_pheromone.py"],
    input=json.dumps(context),
    text=True,
    capture_output=True,
)

print(f"Return code: {result.returncode}")
print(f"STDERR: {result.stderr}")

# Check DB
import sqlite3

conn = sqlite3.connect("/home/bamer/.opencode/emergent-learning/memory/index.db")
cursor = conn.cursor()
cursor.execute(
    "SELECT file_path, tool_name FROM pheromone_trails ORDER BY id DESC LIMIT 5"
)
trails = cursor.fetchall()
conn.close()

print("Recent trails:")
for trail in trails:
    print(f"  {trail[0]} ({trail[1]})")
