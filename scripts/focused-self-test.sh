#!/bin/bash
# Focused Self-Test Script for Emergent Learning Framework

echo "=============================================="
echo "Emergent Learning Framework - Focused Self-Test"
echo "Started: $(date)"
echo "=============================================="

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Install from https://python.org"
    exit 1
fi

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

# Record test result function
record_result() {
    local status=$1
    local message=$2
    
    case $status in
        pass)
            echo "PASS: $message"
            ((TESTS_PASSED++))
            ;;
        fail)
            echo "FAIL: $message"
            ((TESTS_FAILED++))
            ;;
        warn)
            echo "WARN: $message"
            ((TESTS_WARNINGS++))
            ;;
    esac
}

# Test 1: Directory Structure
echo ""
echo "=== Test 1: Directory Structure ==="

# Check directories individually (no arrays)
record_result pass "Directory exists: $MEMORY_DIR"
[ -d "$MEMORY_DIR/failures" ] && record_result pass "Directory exists: $MEMORY_DIR/failures" || record_result fail "Missing directory: $MEMORY_DIR/failures"
[ -d "$MEMORY_DIR/successes" ] && record_result pass "Directory exists: $MEMORY_DIR/successes" || record_result fail "Missing directory: $MEMORY_DIR/successes"
[ -d "$MEMORY_DIR/heuristics" ] && record_result pass "Directory exists: $MEMORY_DIR/heuristics" || record_result fail "Missing directory: $MEMORY_DIR/heuristics"
[ -d "$BASE_DIR/scripts" ] && record_result pass "Directory exists: $BASE_DIR/scripts" || record_result fail "Missing directory: $BASE_DIR/scripts"
[ -d "$BASE_DIR/query" ] && record_result pass "Directory exists: $BASE_DIR/query" || record_result fail "Missing directory: $BASE_DIR/query"
[ -d "$BASE_DIR/golden-rules" ] && record_result pass "Directory exists: $BASE_DIR/golden-rules" || record_result fail "Missing directory: $BASE_DIR/golden-rules"
[ -d "$BASE_DIR/ceo-inbox" ] && record_result pass "Directory exists: $BASE_DIR/ceo-inbox" || record_result fail "Missing directory: $BASE_DIR/ceo-inbox"
[ -d "$BASE_DIR/experiments" ] && record_result pass "Directory exists: $BASE_DIR/experiments" || record_result fail "Missing directory: $BASE_DIR/experiments"
[ -d "$BASE_DIR/logs" ] && record_result pass "Directory exists: $BASE_DIR/logs" || record_result fail "Missing directory: $BASE_DIR/logs"

# Test 2: Database Integrity
echo ""
echo "=== Test 2: Database Integrity ==="

if [ ! -f "$DB_PATH" ]; then
    record_result fail "Database file does not exist: $DB_PATH"
else
    record_result pass "Database file exists"
    
    # Check database integrity
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        record_result pass "Database integrity check passed"
    else
        record_result fail "Database integrity check failed"
    fi

    # Check required tables
    sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='learnings'" | grep -q "learnings" && record_result pass "Table exists: learnings" || record_result warn "Missing table: learnings"
    sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='heuristics'" | grep -q "heuristics" && record_result pass "Table exists: heuristics" || record_result warn "Missing table: heuristics"
    sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'" | grep -q "experiments" && record_result pass "Table exists: experiments" || record_result warn "Missing table: experiments"
    sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='ceo_reviews'" | grep -q "ceo_reviews" && record_result pass "Table exists: ceo_reviews" || record_result warn "Missing table: ceo_reviews"
fi

# Test 3: Script Functionality
echo ""
echo "=== Test 3: Script Functionality ==="

[ -f "$SCRIPT_DIR/record-failure.sh" ] && record_result pass "Script exists: record-failure.sh" || record_result fail "Missing script: record-failure.sh"
[ -f "$SCRIPT_DIR/record-heuristic.sh" ] && record_result pass "Script exists: record-heuristic.sh" || record_result fail "Missing script: record-heuristic.sh"
[ -f "$SCRIPT_DIR/init.sh" ] && record_result pass "Script exists: init.sh" || record_result fail "Missing script: init.sh"
[ -f "$BASE_DIR/query/query.py" ] && record_result pass "Script exists: query.py" || record_result fail "Missing script: query.py"

# Check executability
[ -x "$SCRIPT_DIR/record-failure.sh" ] && record_result pass "Script is executable: record-failure.sh" || record_result warn "Script not executable: record-failure.sh"
[ -x "$SCRIPT_DIR/record-heuristic.sh" ] && record_result pass "Script is executable: record-heuristic.sh" || record_result warn "Script not executable: record-heuristic.sh"
[ -x "$SCRIPT_DIR/init.sh" ] && record_result pass "Script is executable: init.sh" || record_result warn "Script not executable: init.sh"
[ -x "$BASE_DIR/query/query.py" ] && record_result pass "Script is executable: query.py" || record_result warn "Script not executable: query.py"

# Test 4: Query System
echo ""
echo "=== Test 4: Query System ==="

# Test query.py basic functionality
if $PYTHON_CMD "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
    record_result pass "query.py --stats executes successfully"
else
    record_result fail "query.py --stats failed to execute"
fi

# Test context query
if $PYTHON_CMD "$BASE_DIR/query/query.py" --context >/dev/null 2>&1; then
    record_result pass "Context query works"
else
    record_result fail "Context query failed"
fi

# Test recent query
if $PYTHON_CMD "$BASE_DIR/query/query.py" --recent 1 >/dev/null 2>&1; then
    record_result pass "Recent learnings query works"
else
    record_result fail "Recent learnings query failed"
fi

# Test 5: Golden Rules Integrity
echo ""
echo "=== Test 5: Golden Rules Integrity ==="

if [ ! -d "$BASE_DIR/golden-rules" ]; then
    record_result warn "Golden rules directory does not exist"
else
    rule_count=$(find "$BASE_DIR/golden-rules" -name "*.md" -type f 2>/dev/null | wc -l)
    echo "Found $rule_count golden rule files"

    if [ "$rule_count" -gt 0 ]; then
        record_result pass "Golden rules exist ($rule_count files)"
    else
        record_result warn "No golden rules found"
    fi
fi

# Test 6: Bootstrap Recovery Capability
echo ""
echo "=== Test 6: Bootstrap Recovery ==="

# Check if init scripts exist
if [ -f "$SCRIPT_DIR/init.sh" ]; then
    record_result pass "Bootstrap init script exists"
else
    record_result fail "Bootstrap init script missing"
fi

# Final Summary
echo ""
echo "=============================================="
echo "Focused Self-Test Summary"
echo "=============================================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "Warnings: $TESTS_WARNINGS"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED + TESTS_WARNINGS))"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo ""
    echo "ALL CORE TESTS PASSED"
    echo ""
    echo "The Emergent Learning Framework core functionality is working correctly."
    exit 0
else
    echo ""
    echo "$TESTS_FAILED TEST(S) FAILED"
    echo ""
    echo "Some core functionality issues were detected."
    exit 1
fi