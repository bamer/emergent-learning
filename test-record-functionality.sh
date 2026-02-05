#!/bin/bash
# Test recording functionality by directly calling the Python scripts

set -e

BASE_DIR="/home/bamer/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"

echo "=== Testing Recording Functionality ==="

# Test Python-based heuristic recording
echo "Testing Python-based heuristic recording..."
if command -v python3 &> /dev/null && [ -f "$BASE_DIR/scripts/record-heuristic.py" ]; then
    if python3 "$BASE_DIR/scripts/record-heuristic.py" --title "Test heuristic" --domain "test" --content "This is a test heuristic from self-test" --confidence 0.8; then
        echo "✓ PASS: Python heuristic recording works"
    else
        echo "✗ FAIL: Python heuristic recording failed"
    fi
else
    echo "✗ FAIL: Python or record-heuristic.py not available"
fi

echo "=== Recording Functionality Test Completed ==="