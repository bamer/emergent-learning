#!/bin/bash
# Fast Self-Test for ELF System

# Removed set -e to see all test results

echo "=== Fast ELF Self-Test ==="

SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
QUERY_DIR="/home/bamer/.opencode/emergent-learning/Open_ELF/query"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
DB_PATH="$BASE_DIR/memory/index.db"

FAILURES=0
PASSED=0

pass() {
    echo "✓ PASS: $1"
    ((PASSED++))
}

fail() {
    echo "✗ FAIL: $1"
    ((FAILURES++))
}

# Test 1: Directory Structure
echo "1. Checking directory structure..."
if [ -d "$BASE_DIR/memory" ] && [ -d "$BASE_DIR/scripts" ] && [ -d "$BASE_DIR/Open_ELF/query" ]; then
    pass "Required directories exist"
else
    fail "Missing required directories"
fi

# Test 2: Database
echo "2. Checking database..."
if [ -f "$DB_PATH" ]; then
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        pass "Database integrity check passed"
    else
        fail "Database integrity check failed"
    fi
    
    # Check required tables
    required_tables=("learnings" "heuristics" "experiments" "ceo_reviews")
    for table in "${required_tables[@]}"; do
        if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
            pass "Table exists: $table"
        else
            fail "Missing table: $table"
        fi
    done
else
    fail "Database file does not exist: $DB_PATH"
fi

# Test 3: Scripts
echo "3. Checking scripts..."
if [ -f "$SCRIPT_DIR/record-failure.sh" ] && [ -x "$SCRIPT_DIR/record-failure.sh" ]; then
    pass "record-failure.sh exists and is executable"
else
    fail "record-failure.sh missing or not executable"
fi

if [ -f "$SCRIPT_DIR/record-heuristic.sh" ] && [ -x "$SCRIPT_DIR/record-heuristic.sh" ]; then
    pass "record-heuristic.sh exists and is executable"
else
    fail "record-heuristic.sh missing or not executable"
fi

if [ -f "$QUERY_DIR/query.py" ]; then
    pass "query.py exists"
else
    fail "query.py missing"
fi

# Test 4: Query functionality
echo "4. Testing query functionality..."
if python3 "$QUERY_DIR/query.py" --stats >/dev/null 2>&1; then
    pass "query.py --stats executes successfully"
else
    fail "query.py --stats failed to execute"
fi

# Summary
echo "=== Test Summary ==="
echo "Passed: $PASSED"
echo "Failed: $FAILURES"
echo "Total: $((PASSED + FAILURES))"

if [ "$FAILURES" -eq 0 ]; then
    echo "Result: ALL TESTS PASSED"
    exit 0
else
    echo "Result: SOME TESTS FAILED"
    exit 1
fi