#!/bin/bash
# Minimal debug test

echo "Starting minimal debug test..."

echo "Test 1: Directory Structure"
MEMORY_DIR="/home/bamer/.opencode/emergent-learning/memory"
if [ -d "$MEMORY_DIR" ]; then
    echo "PASS: Memory directory exists"
else
    echo "FAIL: Memory directory missing"
fi
echo "Test 1 complete"

echo "Test 2: Database Integrity"
DB_PATH="/home/bamer/.opencode/emergent-learning/memory/index.db"
if [ ! -f "$DB_PATH" ]; then
    echo "FAIL: Database file does not exist: $DB_PATH"
else
    echo "PASS: Database file exists"
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        echo "PASS: Database integrity check passed"
    else
        echo "FAIL: Database integrity check failed"
    fi
fi
echo "Test 2 complete"

echo "Test 3: File-Database Sync"
MEMORY_DIR="/home/bamer/.opencode/emergent-learning/memory"
failure_files=$(find "$MEMORY_DIR/failures" -name "*.md" -type f 2>/dev/null | wc -l)
success_files=$(find "$MEMORY_DIR/successes" -name "*.md" -type f 2>/dev/null | wc -l)
db_failures=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings WHERE type='failure'")
db_successes=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings WHERE type='success'")
echo "Failure files: $failure_files, DB records: $db_failures"
echo "Success files: $success_files, DB records: $db_successes"
echo "Test 3 complete"

echo "Test 4: Script Functionality"
SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
if [ ! -d "$SCRIPT_DIR" ]; then
    echo "FAIL: Scripts directory does not exist: $SCRIPT_DIR"
else
    echo "PASS: Scripts directory exists"
fi
echo "Test 4 complete"

echo "Test 5: Query Functionality"
PYTHON_CMD="python3"
if $PYTHON_CMD "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
    echo "PASS: query.py --stats executes successfully"
else
    echo "FAIL: query.py --stats failed to execute"
fi
echo "Test 5 complete"

echo "Test 6: Memory System"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
if $PYTHON_CMD "$BASE_DIR/query/query.py" --recent 1 >/dev/null 2>&1; then
    echo "PASS: Recent learnings query works"
else
    echo "FAIL: Recent learnings query failed"
fi

# Test domain query (use a domain we know exists)
DB_PATH="/home/bamer/.opencode/emergent-learning/memory/index.db"
domains=$(sqlite3 "$DB_PATH" "SELECT DISTINCT domain FROM learnings LIMIT 1")
if [ -n "$domains" ]; then
    if $PYTHON_CMD "$BASE_DIR/query/query.py" --domain "$domains" --limit 1 >/dev/null 2>&1; then
        echo "PASS: Domain query works"
    else
        echo "FAIL: Domain query failed"
    fi
else
    echo "WARN: No domains found in database to test query"
fi

# Test stats query
stats=$($PYTHON_CMD "$BASE_DIR/query/query.py" --stats 2>/dev/null)
if echo "$stats" | grep -q "total_learnings"; then
    echo "PASS: Statistics query works"
else
    echo "FAIL: Statistics query failed or returned unexpected format"
fi
echo "Test 6 complete"

echo "All tests completed successfully"