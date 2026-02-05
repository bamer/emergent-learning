#!/bin/bash
# More complete test

set -e

BASE_DIR="."
MEMORY_DIR="$BASE_DIR/memory"
SCRIPT_DIR="$BASE_DIR/scripts"
LOGS_DIR="$BASE_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Colors for output (without color codes to test if that's the issue)
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

# Test function
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
    
    echo "About to loop through ${#required_dirs[@]} directories"
    
    for dir in "${required_dirs[@]}"; do
        echo "Checking directory: $dir"
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            echo "FAIL: Missing directory: $dir"
        fi
    done
    
    echo "Test function completed"
}

# Main execution
echo "========================================="
echo "More Complete Test"
echo "Started: $(date)"
echo "========================================="

test_directory_structure

echo "=== Self-Test Summary ==="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "Warnings: $TESTS_WARNINGS"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

echo "Script completed"