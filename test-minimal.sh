#!/bin/bash
set -e

echo "Starting test"

required_dirs=(
    "memory"
    "memory/failures"
    "memory/successes"
    "memory/heuristics"
    "scripts"
    "query"
    "golden-rules"
    "ceo-inbox"
    "experiments"
    "logs"
)

echo "About to iterate through directories"
for dir in "${required_dirs[@]}"; do
    echo "Checking: $dir"
    if [ -d "$dir" ]; then
        echo "✓ PASS: Directory exists: $dir"
    else
        echo "✗ FAIL: Missing directory: $dir"
    fi
done

echo "Finished test"
