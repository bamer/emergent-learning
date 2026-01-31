#!/usr/bin/env python3
"""
Create a simple test to see what's happening with pheromone
"""

import subprocess
import json
from datetime import datetime

# Create a context that should definitely work
context = {
    "tool_name": "Read",
    "tool_input": {"file_path": "/home/bamer/.opencode/emergent-learning/README.md"},
    "timestamp": datetime.now().isoformat(),
}

print(f"Context: {context}")

# Direct call with verbose
result = subprocess.run(
    [
        "python3",
        "-c",
        '''
import sys
import json
sys.path.insert(0, ".")
from record_pheromone import main

# Test direct call
test_context = """ + json.dumps(context) + """
print(f"Calling main() with: {test_context}")
sys.argv = ["record_pheromone.py", test_context]
result = main()
print(f"Result: {result}")
''',
    ],
    capture_output=True,
    text=True,
)

print(f"Output:\n{result.stdout}")
print(f"Error:\n{result.stderr}")
print(f"Return code: {result.returncode}")
