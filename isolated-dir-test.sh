#!/bin/bash

set -e

SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "/tmp/isolated-test.log"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "/tmp/isolated-test.log"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "/tmp/isolated-test.log"
    ((TESTS_FAILED++))
    FAILURE_DETAILS+=("$*")
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*" | tee -a "/tmp/isolated-test.log"
    ((TESTS_WARNINGS++))
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

    log "DEBUG: Checking ${#required_dirs[@]} directories"
    for i in "${!required_dirs[@]}"; do
        dir="${required_dirs[$i]}"
        log "DEBUG: Checking directory $dir (index $i)"
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
        log "DEBUG: Finished checking directory $dir"
    done
    log "DEBUG: Directory structure test completed"
}

# Run the test
test_directory_structure

log "=== Test Summary ==="
log "Tests Passed: $TESTS_PASSED"
log "Tests Failed: $TESTS_FAILED"
log "Warnings: $TESTS_WARNINGS"