#!/bin/bash

set -e

BASE_DIR="/home/bamer/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
LOGS_DIR="$BASE_DIR/logs"

required_dirs=(
    "$MEMORY_DIR"
    "$MEMORY_DIR/failures"
    "$MEMORY_DIR/successes"
    "$MEMORY_DIR/heuristics"
    "$BASE_DIR/scripts"
    "$BASE_DIR/query"
    "$BASE_DIR/golden-rules"
    "$BASE_DIR/ceo-inbox"
    "$BASE_DIR/experiments"
    "$LOGS_DIR"
)

echo "Starting directory check test..."
echo "Checking ${#required_dirs[@]} directories"

for i in "${!required_dirs[@]}"; do
    dir="${required_dirs[$i]}"
    echo "Checking directory $dir (index $i)"
    if [ -d "$dir" ]; then
        echo "PASS: Directory exists: $dir"
    else
        echo "FAIL: Missing directory: $dir"
    fi
    echo "Finished checking directory $dir"
done

echo "Directory check test completed"