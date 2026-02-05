#!/bin/bash
# Test just the directory structure function

set -e

SCRIPT_DIR="$HOME/.opencode/emergent-learning/scripts"
BASE_DIR="$HOME/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*"
    ((TESTS_WARNINGS++))
}

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
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
    done
    
    echo "Directory structure test completed."
    echo "Passed: $TESTS_PASSED, Failed: $TESTS_FAILED, Warnings: $TESTS_WARNINGS"
}

# Run just the directory structure test
echo "========================================="
echo "Testing Directory Structure Only"
echo "========================================="

test_directory_structure