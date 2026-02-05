#!/bin/bash
# Test just the database integrity function

set -e

SCRIPT_DIR="$HOME/.opencode/emergent-learning/scripts"
BASE_DIR="$HOME/.opencode/emergent-learning"
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

# Test 2: Database Integrity
test_database_integrity() {
    echo "=== Test 2: Database Integrity ==="
    
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
    
    echo "Database integrity test completed."
    echo "Passed: $TESTS_PASSED, Failed: $TESTS_FAILED, Warnings: $TESTS_WARNINGS"
}

# Run just the database integrity test
echo "========================================="
echo "Testing Database Integrity Only"
echo "========================================="

test_database_integrity