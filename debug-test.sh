#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
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
FAILURE_DETAILS=()

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" 
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*"
    ((TESTS_FAILED++))
    FAILURE_DETAILS+=("$*")
}

# Test 1: Directory Structure
test_directory_structure() {
    log "=== Test 1: Directory Structure ==="
    
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
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
    done
}

# Run just the directory test
test_directory_structure
echo "Test completed. Passed: $TESTS_PASSED, Failed: $TESTS_FAILED"