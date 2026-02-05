#!/bin/bash
# Simplified Self-Test Script for Emergent Learning Framework (WITH DEBUG)

set -e

SCRIPT_DIR="$HOME/.opencode/emergent-learning/scripts"
BASE_DIR="$HOME/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Install from https://python.org"
    exit 1
fi

# Colors for output
RED='[RED]'
GREEN='[GREEN]'
YELLOW='[YELLOW]'
NC='[NC]' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

pass() {
    echo "$GREEN PASS $NC: $*"
    ((TESTS_PASSED++))
}

fail() {
    echo "$RED FAIL $NC: $*"
    ((TESTS_FAILED++))
}

warn() {
    echo "$YELLOW WARN $NC: $*"
    ((TESTS_WARNINGS++))
}

# Test 1: Directory Structure
test_directory_structure() {
    echo "=== Test 1: Directory Structure ==="
    
    echo "DEBUG: Setting up required_dirs array"
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
    
    echo "DEBUG: Array created with ${#required_dirs[@]} elements"
    
    echo "DEBUG: About to loop through directories"
    for dir in "${required_dirs[@]}"; do
        echo "DEBUG: Checking directory: $dir"
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
        echo "DEBUG: Finished checking directory: $dir"
    done
    echo "DEBUG: Finished looping through directories"
}

# Main execution
main() {
    echo "========================================="
    echo "Emergent Learning Framework - Simple Self-Test"
    echo "Started: $(date)"
    echo "========================================="
    
    echo "DEBUG: About to call test_directory_structure"
    test_directory_structure
    echo "DEBUG: Returned from test_directory_structure"
    
    echo "=== Self-Test Summary ==="
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Warnings: $TESTS_WARNINGS"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo "Overall Status: ALL TESTS PASSED"
        return 0
    else
        echo "Overall Status: SOME TESTS FAILED"
        return 1
    fi
}

# Run main
echo "DEBUG: Script starting"
main
echo "DEBUG: Script completed normally"