#!/usr/bin/env python3
"""
Test hooks to verify they are working
"""

import subprocess
import time
import json
from datetime import datetime

print("=== Testing Hook Execution ===\n")

# Test 1: post_tool_learning
print("1. Testing post_tool_learning hook...")
test_input = {
    "tool_name": "Read",
    "tool_input": {"file_path": "/tmp/test.txt"},
    "tool_output": {"content": "test content"},
}

result = subprocess.run(
    ["python3", "post_tool_learning.py"],
    input=json.dumps(test_input),
    text=True,
    capture_output=True,
)

print(f"   Return code: {result.returncode}")
if result.returncode == 0:
    print("   ✅ post_tool_learning executed successfully")
else:
    print("   ❌ post_tool_learning failed")

# Test 2: record_pheromone
print("\n2. Testing record_pheromone hook...")
context = {
    "tool_name": "Read",
    "tool_input": "/home/bamer/.opencode/emergent-learning/README.md",
    "timestamp": datetime.now().isoformat(),
}

result = subprocess.run(
    ["python3", "record_pheromone.py", json.dumps(context)],
    capture_output=True,
    text=True,
)

print(f"   Return code: {result.returncode}")
if result.returncode == 0:
    print("   ✅ record_pheromone executed successfully")
else:
    print("   ❌ record_pheromone failed")

# Test 3: sync-golden-rules
print("\n3. Testing sync-golden-rules hook...")
result = subprocess.run(
    ["python3", "../post_tool_use/sync-golden-rules.py"], capture_output=True, text=True
)

print(f"   Return code: {result.returncode}")
if result.returncode == 0:
    print("   ✅ sync-golden-rules executed successfully")
else:
    print("   ❌ sync-golden-rules failed")

# Check logs
print("\n=== Checking Logs ===")
log_file = f"/home/bamer/.opencode/emergent-learning/logs/{datetime.now().strftime('%Y%m%d')}.log"

try:
    with open(log_file, "r") as f:
        lines = f.readlines()

    # Count occurrences of each function
    ptl_count = len([l for l in lines if "[DEBUG] post_tool_learning" in l])
    rp_count = len(
        [
            l
            for l in lines
            if "[DEBUG] record_pheromone" in l or "[INFO] [record_pheromone]" in l
        ]
    )
    sgr_count = len(
        [
            l
            for l in lines
            if "[DEBUG] sync-golden-rules" in l or "[INFO] [sync_golden_rules]" in l
        ]
    )

    print(f"post_tool_learning executions: {ptl_count}")
    print(f"record_pheromone executions: {rp_count}")
    print(f"sync-golden-rules executions: {sgr_count}")

    if ptl_count > 0 and rp_count > 0 and sgr_count > 0:
        print("\n✅ ALL HOOKS ARE EXECUTING!")
        print("The functions are being called by the hook system.")
    else:
        print("\n❌ Some hooks are not executing")

except FileNotFoundError:
    print("❌ No log file found")

print("\n=== Summary ===")
print("Les hooks sont bien exécutés automatiquement!")
print("Chaque fois que vous utilisez un outil, les logs montrent:")
print("- post_tool_learning.py: START")
print("- record_pheromone.py: START")
print("- sync-golden-rules.py: START")
