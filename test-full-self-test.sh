#!/bin/bash

SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
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
LOG_FILE="$LOGS_DIR/self-test-debug-full.log"
mkdir -p "$LOGS_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_FAILED++))
    FAILURE_DETAILS+=("$*")
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_WARNINGS++))
}

info() {
    echo -e "ℹ INFO: $*" | tee -a "$LOG_FILE"
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
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
    done
}

# Test 2: Database Integrity
test_database_integrity() {
    log "=== Test 2: Database Integrity ==="
    
    if [ ! -f "$DB_PATH" ]; then
        fail "Database file does not exist: $DB_PATH"
        return
    fi
    pass "Database file exists"
    
    # Check database integrity
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        pass "Database integrity check passed"
    else
        fail "Database integrity check failed"
    fi
    
    # Check required tables
    local required_tables=("learnings" "heuristics" "experiments" "ceo_reviews")
    for table in "${required_tables[@]}"; do
        if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
            pass "Table exists: $table"
        else
            fail "Missing table: $table"
        fi
    done
    
    # Check for orphaned records
    local orphaned=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings WHERE filepath NOT LIKE '%/%'")
    if [ "$orphaned" -eq 0 ]; then
        pass "No orphaned records in learnings table"
    else
        warn "Found $orphaned potentially orphaned records in learnings"
    fi
}

# Main execution
main() {
    log "========================================="
    log "Emergent Learning Framework - Full Self-Test (Debug)"
    log "Started: $(date)"
    log "========================================="
    
    test_directory_structure
    test_database_integrity
    
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
main