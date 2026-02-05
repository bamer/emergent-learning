#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "SCRIPT_DIR: $SCRIPT_DIR"

BASE_DIR="$(dirname "$SCRIPT_DIR")"
echo "BASE_DIR: $BASE_DIR"

MEMORY_DIR="$BASE_DIR/memory"
echo "MEMORY_DIR: $MEMORY_DIR"

DB_PATH="$MEMORY_DIR/index.db"
echo "DB_PATH: $DB_PATH"

LOGS_DIR="$BASE_DIR/logs"
echo "LOGS_DIR: $LOGS_DIR"

# Test 1: Directory Structure
test_directory_structure() {
    echo "=== Test 1: Directory Structure ==="
    
    local required_dirs=(
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
    
    echo "Checking ${#required_dirs[@]} directories..."
    
    for dir in "${required_dirs[@]}"; do
        echo "Checking: $dir"
        if [ -d "$dir" ]; then
            echo "PASS: Directory exists: $dir"
        else
            echo "FAIL: Missing directory: $dir"
        fi
    done
}

# Run just the directory test
test_directory_structure