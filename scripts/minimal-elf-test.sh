#!/bin/bash
# Minimal ELF Test Script
# Purpose: Quickly verify core ELF functionality

set -e

echo "=== Minimal ELF Test ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*"
    ((FAILED++))
}

# Test 1: Directory structure
echo "Test 1: Directory structure"
if [ -d "$MEMORY_DIR" ] && [ -d "$MEMORY_DIR/failures" ] && [ -d "$MEMORY_DIR/successes" ]; then
    pass "Required directories exist"
else
    fail "Missing required directories"
fi

# Test 2: Database integrity
echo "Test 2: Database integrity"
if [ -f "$DB_PATH" ]; then
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        pass "Database integrity check passed"
    else
        fail "Database integrity check failed"
    fi
else
    fail "Database file does not exist"
fi

# Test 3: Required tables
echo "Test 3: Required tables"
required_tables=("learnings" "heuristics" "experiments")
all_tables_found=true
for table in "${required_tables[@]}"; do
    if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
        continue
    else
        all_tables_found=false
    fi
done

if [ "$all_tables_found" = true ]; then
    pass "All required tables exist"
else
    fail "Some required tables are missing"
fi

# Test 4: Query script
echo "Test 4: Query script"
if [ -f "$BASE_DIR/query/query.py" ]; then
    if python3 "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
        pass "query.py executes successfully"
    else
        fail "query.py failed to execute"
    fi
else
    fail "query.py does not exist"
fi

# Test 5: Record scripts
echo "Test 5: Record scripts"
if [ -f "$SCRIPT_DIR/record-failure.sh" ] && [ -f "$SCRIPT_DIR/record-heuristic.sh" ]; then
    if [ -x "$SCRIPT_DIR/record-failure.sh" ] && [ -x "$SCRIPT_DIR/record-heuristic.sh" ]; then
        pass "Record scripts exist and are executable"
    else
        fail "Record scripts exist but are not executable"
    fi
else
    fail "Record scripts are missing"
fi

# Summary
echo "=== Test Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total: $((PASSED + FAILED))"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ELF system is functioning correctly.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi