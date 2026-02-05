#!/bin/bash
# Debug Self-Test Script for Emergent Learning Framework

set -e

echo "DEBUG: Starting script"

SCRIPT_DIR="$HOME/.opencode/emergent-learning/scripts"
BASE_DIR="$HOME/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

echo "DEBUG: Variables set"
echo "DEBUG: SCRIPT_DIR=$SCRIPT_DIR"
echo "DEBUG: BASE_DIR=$BASE_DIR"
echo "DEBUG: MEMORY_DIR=$MEMORY_DIR"
echo "DEBUG: DB_PATH=$DB_PATH"
echo "DEBUG: LOGS_DIR=$LOGS_DIR"

# Create logs directory if it doesn't exist
echo "DEBUG: Creating logs directory"
mkdir -p "$LOGS_DIR"
echo "DEBUG: Logs directory created"

# Detect Python command
echo "DEBUG: Detecting Python command"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "DEBUG: Using python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "DEBUG: Using python"
else
    echo "Error: Python not found. Install from https://python.org"
    exit 1
fi

# Simple output (no colors)
pass() {
    echo "PASS: $*"
}

fail() {
    echo "FAIL: $*"
}

warn() {
    echo "WARN: $*"
}

# Test 1: Directory Structure
test_directory_structure() {
    echo "DEBUG: Entering test_directory_structure"
    echo "=== Test 1: Directory Structure ==="
    
    local required_dirs=(
        "$MEMORY_DIR"
    )
    
    echo "DEBUG: About to loop through directories"
    for dir in "${required_dirs[@]}"; do
        echo "DEBUG: Checking directory: $dir"
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
    done
    
    echo "DEBUG: Exiting test_directory_structure"
}

# Main execution
main() {
    echo "DEBUG: Entering main function"
    echo "========================================="
    echo "Emergent Learning Framework - Debug Self-Test"
    echo "Started: $(date)"
    echo "========================================="
    
    echo "DEBUG: About to call test_directory_structure"
    test_directory_structure
    echo "DEBUG: Returned from test_directory_structure"
    
    echo "DEBUG: Script completed"
}

# Run main
echo "DEBUG: About to call main function"
main
echo "DEBUG: Script finished"