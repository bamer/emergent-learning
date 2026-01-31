#!/usr/bin/env python3
"""
Test script to verify all logging functions work correctly
"""

import json
import sys
from pathlib import Path

# Test post_tool_learning
print("Testing post_tool_learning...")
test_input = {
    "tool_name": "Test",
    "tool_input": {"description": "Test logging functionality"},
    "tool_output": {"content": "Test completed successfully"},
}

# Write test input to temp file
with open("/tmp/test_hook_input.json", "w") as f:
    json.dump(test_input, f)

# Run post_tool_learning with test input
import subprocess

result = subprocess.run(
    ["python3", "post_tool_learning.py"],
    input=json.dumps(test_input),
    text=True,
    capture_output=True,
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)

# Test record_pheromone
print("\nTesting record_pheromone...")
test_context = {
    "tool_name": "Read",
    "tool_input": "/home/bamer/.opencode/emergent-learning/README.md",
    "timestamp": "2026-01-31T14:00:00",
}

result = subprocess.run(
    ["python3", "record_pheromone.py", json.dumps(test_context)],
    capture_output=True,
    text=True,
)

print("Return code:", result.returncode)

# Test sync-golden-rules
print("\nTesting sync-golden-rules...")
result = subprocess.run(
    ["python3", "../post_tool_use/sync-golden-rules.py"], capture_output=True, text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

# Check logs
print("\nChecking today's log file...")
log_file = Path.home() / ".opencode" / "emergent-learning" / "logs" / "20260131.log"
if log_file.exists():
    with open(log_file, "r") as f:
        recent_logs = f.read().split("\n")[-20:]  # Last 20 lines
    for line in recent_logs:
        if line.strip():
            print(line)
else:
    print("No log file found!")

print("\n✅ Logging test complete!")
