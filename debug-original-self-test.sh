#!/bin/bash
# Self-Test Script for Emergent Learning Framework (DEBUG VERSION)
# Purpose: Meta-learning - can the system detect its own bugs?

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

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
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0
FAILURE_DETAILS=()

# Logging setup
LOG_FILE="$LOGS_DIR/self-test-$(date +%Y%m%d-%H%M%S)-debug.log"
mkdir -p "$LOGS_DIR"

echo "DEBUG: Script started, LOG_FILE=$LOG_FILE"

log() {
    echo "DEBUG: About to log: $*"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
    echo "DEBUG: Finished logging: $*"
}

pass() {
    echo "DEBUG: About to pass: $*"
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_PASSED++))
    echo "DEBUG: Finished passing: $*"
}

fail() {
    echo "DEBUG: About to fail: $*"
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_FAILED++))
    FAILURE_DETAILS+=("$*")
    echo "DEBUG: Finished failing: $*"
}

warn() {
    echo "DEBUG: About to warn: $*"
    echo -e "${YELLOW}⚠ WARN${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_WARNINGS++))
    echo "DEBUG: Finished warning: $*"
}

info() {
    echo "DEBUG: About to info: $*"
    echo -e "ℹ INFO: $*" | tee -a "$LOG_FILE"
    echo "DEBUG: Finished infom: $*"
}

# Test 1: Directory Structure
test_directory_structure() {
    echo "DEBUG: Entering test_directory_structure"
    log "=== Test 1: Directory Structure ==="
    echo "DEBUG: After log call in test_directory_structure"
    
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
    
    echo "DEBUG: Starting directory loop"
    for dir in "${required_dirs[@]}"; do
        echo "DEBUG: Checking directory: $dir"
        if [ -d "$dir" ]; then
            echo "DEBUG: Directory exists, about to pass: $dir"
            pass "Directory exists: $dir"
            echo "DEBUG: Finished passing: $dir"
        else
            echo "DEBUG: Directory missing, about to fail: $dir"
            fail "Missing directory: $dir"
            echo "DEBUG: Finished failing: $dir"
        fi
        echo "DEBUG: Done checking directory: $dir"
    done
    echo "DEBUG: Exiting test_directory_structure"
}

# Test 2: Database Integrity
test_database_integrity() {
    echo "DEBUG: Entering test_database_integrity"
    log "=== Test 2: Database Integrity ==="
    echo "DEBUG: After log call in test_database_integrity"
}

# Main execution
main() {
    echo "DEBUG: Entering main function"
    log "========================================="
    log "Emergent Learning Framework - Self-Test (DEBUG)"
    log "Started: $(date)"
    log "========================================="
    echo "DEBUG: After initial log calls in main"
    
    test_directory_structure
    echo "DEBUG: After test_directory_structure"
    
    test_database_integrity
    echo "DEBUG: After test_database_integrity"
    
    log "=== Self-Test Summary ==="
    log "Tests Passed: $TESTS_PASSED"
    log "Tests Failed: $TESTS_FAILED"
    log "Warnings: $TESTS_WARNINGS"
    log "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        log "Overall Status: ${GREEN}ALL TESTS PASSED${NC}"
        return 0
    else
        log "Overall Status: ${RED}SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Run main
echo "DEBUG: About to call main"
main
echo "DEBUG: Script completed"