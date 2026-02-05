#!/bin/bash
# Minimal self-test to diagnose hanging issue

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
NC='\033[0m'

# Logging setup
LOG_FILE="$LOGS_DIR/self-test-minimal-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$LOGS_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

pass() {
    echo "DEBUG: About to call tee command"
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$LOG_FILE"
    echo "DEBUG: Finished tee command"
    echo "DEBUG: About to increment TESTS_PASSED (current value: $TESTS_PASSED)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "DEBUG: Incremented TESTS_PASSED to $TESTS_PASSED"
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_FAILED++))
}

# Test variables
TESTS_PASSED=0
TESTS_FAILED=0

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
            log "DEBUG: Directory $dir exists, calling pass function"
            pass "Directory exists: $dir"
            log "DEBUG: Finished pass function for $dir"
        else
            log "DEBUG: Directory $dir does not exist, calling fail function"
            fail "Missing directory: $dir"
            log "DEBUG: Finished fail function for $dir"
        fi
        log "DEBUG: Finished checking directory $dir"
    done
    log "DEBUG: Directory structure test completed"
}

# Test 2: Database Integrity
test_database_integrity() {
    log "=== Test 2: Database Integrity ==="
    
    log "DEBUG: Checking database file $DB_PATH"

    if [ ! -f "$DB_PATH" ]; then
        fail "Database file does not exist: $DB_PATH"
        return
    fi
    pass "Database file exists"

    # Check database integrity
    log "DEBUG: Running database integrity check"
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        pass "Database integrity check passed"
    else
        fail "Database integrity check failed"
    fi
    
    log "DEBUG: Database integrity test completed"
}

# Main execution
main() {
    log "========================================="
    log "Emergent Learning Framework - Minimal Self-Test"
    log "Started: $(date)"
    log "========================================="

    test_directory_structure
    test_database_integrity
    
    log "========================================="
    log "Minimal Self-Test Summary"
    log "Tests Passed: $TESTS_PASSED"
    log "Tests Failed: $TESTS_FAILED"
    log "========================================="
}

# Run main
main
exit 0