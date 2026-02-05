#!/bin/bash
# Comprehensive Self-Test Script for Emergent Learning Framework

set -e

BASE_DIR="/home/bamer/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

echo "========================================="
echo "Emergent Learning Framework - Comprehensive Self-Test"
echo "Started: $(date)"
echo "========================================="

# Test 1: Check if required directories exist
echo "=== Test 1: Directory Structure ==="
required_dirs=(
    "$MEMORY_DIR"
    "$MEMORY_DIR/failures"
    "$MEMORY_DIR/successes"
    "$MEMORY_DIR/heuristics"
    "$BASE_DIR/scripts"
    "$BASE_DIR/query"
    "$BASE_DIR/golden-rules"
    "$BASE_DIR/ceo-inbox"
    "$BASE_DIR/experiments"
)

all_present=true
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ PASS: Directory exists: $dir"
    else
        echo "✗ FAIL: Missing directory: $dir"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo "✓ PASS: All required directories present"
else
    echo "✗ FAIL: Some required directories missing"
fi

# Test 2: Check database file and integrity
echo "=== Test 2: Database Integrity ==="
if [ -f "$DB_PATH" ]; then
    echo "✓ PASS: Database file exists"
    
    if command -v sqlite3 &> /dev/null && sqlite3 "$DB_PATH" "PRAGMA integrity_check" | grep -q "ok"; then
        echo "✓ PASS: Database integrity check passed"
    else
        echo "✗ FAIL: Database integrity check failed"
    fi
    
    # Check required tables
    required_tables=("learnings" "heuristics" "experiments" "ceo_reviews")
    tables_ok=true
    for table in "${required_tables[@]}"; do
        if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
            echo "✓ PASS: Table exists: $table"
        else
            echo "✗ FAIL: Missing table: $table"
            tables_ok=false
        fi
    done
    
    if [ "$tables_ok" = true ]; then
        echo "✓ PASS: All required tables present"
    else
        echo "✗ FAIL: Some required tables missing"
    fi
else
    echo "✗ FAIL: Database file missing"
fi

# Test 3: Python and query script
echo "=== Test 3: Python and Query Script ==="
if command -v python3 &> /dev/null; then
    echo "✓ PASS: Python3 is available"
    
    if python3 "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
        echo "✓ PASS: Query script works correctly"
    else
        echo "✗ FAIL: Query script failed"
    fi
else
    echo "✗ FAIL: Python3 not available"
fi

# Test 4: Record scripts
echo "=== Test 4: Record Scripts ==="
if [ -f "$BASE_DIR/scripts/record-failure.sh" ] && [ -x "$BASE_DIR/scripts/record-failure.sh" ]; then
    echo "✓ PASS: record-failure.sh exists and is executable"
else
    echo "✗ FAIL: record-failure.sh missing or not executable"
fi

if [ -f "$BASE_DIR/scripts/record-heuristic.sh" ] && [ -x "$BASE_DIR/scripts/record-heuristic.sh" ]; then
    echo "✓ PASS: record-heuristic.sh exists and is executable"
else
    echo "✗ FAIL: record-heuristic.sh missing or not executable"
fi

echo "========================================="
echo "Comprehensive Self-Test Completed"
echo "========================================="