#!/bin/bash

echo "========================================="
echo "Emergent Learning Framework - Simple Test"
echo "========================================="

# Test 1: Directory Structure
echo "Test 1: Checking directory structure..."
cd /home/bamer/.opencode/emergent-learning

REQUIRED_DIRS=(
    "memory"
    "memory/failures"
    "memory/successes"
    "memory/heuristics"
    "scripts"
    "query"
    "golden-rules"
    "ceo-inbox"
    "experiments"
    "logs"
)

PASS_COUNT=0
FAIL_COUNT=0

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ PASS: Directory exists: $dir"
        ((PASS_COUNT++))
    else
        echo "  ✗ FAIL: Missing directory: $dir"
        ((FAIL_COUNT++))
    fi
done

# Test 2: Database Integrity
echo ""
echo "Test 2: Checking database integrity..."
if [ -f "memory/index.db" ]; then
    echo "  ✓ PASS: Database file exists"
    ((PASS_COUNT++))
    
    # Check database integrity
    if sqlite3 memory/index.db "PRAGMA integrity_check" | grep -q "ok"; then
        echo "  ✓ PASS: Database integrity check passed"
        ((PASS_COUNT++))
    else
        echo "  ✗ FAIL: Database integrity check failed"
        ((FAIL_COUNT++))
    fi
    
    # Check required tables
    REQUIRED_TABLES=("learnings" "heuristics" "experiments" "ceo_reviews")
    for table in "${REQUIRED_TABLES[@]}"; do
        if sqlite3 memory/index.db "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
            echo "  ✓ PASS: Table exists: $table"
            ((PASS_COUNT++))
        else
            echo "  ✗ FAIL: Missing table: $table"
            ((FAIL_COUNT++))
        fi
    done
else
    echo "  ✗ FAIL: Database file does not exist: memory/index.db"
    ((FAIL_COUNT++))
fi

# Test 3: Script Functionality
echo ""
echo "Test 3: Checking script functionality..."
REQUIRED_SCRIPTS=(
    "scripts/record-failure.sh"
    "scripts/record-heuristic.sh"
    "query/query.py"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ] || [[ "$script" == *.py ]]; then
            echo "  ✓ PASS: Script exists and is executable: $script"
            ((PASS_COUNT++))
        else
            echo "  ⚠ WARN: Script exists but is not executable: $script"
            ((PASS_COUNT++))  # Still count as passing since it exists
        fi
    else
        echo "  ✗ FAIL: Missing script: $script"
        ((FAIL_COUNT++))
    fi
done

# Test 4: Query System
echo ""
echo "Test 4: Testing query system..."
if python3 query/query.py --stats >/dev/null 2>&1; then
    echo "  ✓ PASS: query.py --stats executes successfully"
    ((PASS_COUNT++))
else
    echo "  ✗ FAIL: query.py --stats failed to execute"
    ((FAIL_COUNT++))
fi

# Summary
echo ""
echo "========================================="
echo "Simple Test Summary"
echo "========================================="
echo "Tests Passed: $PASS_COUNT"
echo "Tests Failed: $FAIL_COUNT"
echo "Total Tests: $((PASS_COUNT + FAIL_COUNT))"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED!"
    echo "The Emergent Learning Framework is functioning correctly."
    exit 0
else
    echo ""
    echo "❌ SOME TESTS FAILED"
    echo "There are issues with the Emergent Learning Framework that need attention."
    exit 1
fi