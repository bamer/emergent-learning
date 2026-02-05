#!/bin/bash

echo "========================================="
echo "Emergent Learning Framework - System Check"
echo "========================================="

# Test 1: Directory Structure
echo ""
echo "Test 1: Directory Structure"
echo "=========================="
cd /home/bamer/.opencode/emergent-learning

DIRECTORIES=(
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

all_passed=true

for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ PASS: $dir"
    else
        echo "  ✗ FAIL: $dir"
        all_passed=false
    fi
done

# Test 2: Database Integrity
echo ""
echo "Test 2: Database Integrity"
echo "========================="
if [ -f "memory/index.db" ]; then
    echo "  ✓ PASS: Database file exists"
    
    # Check integrity
    if sqlite3 memory/index.db "PRAGMA integrity_check" | grep -q "ok"; then
        echo "  ✓ PASS: Database integrity check passed"
    else
        echo "  ✗ FAIL: Database integrity check failed"
        all_passed=false
    fi
    
    # Check required tables
    REQUIRED_TABLES=("learnings" "heuristics" "experiments" "ceo_reviews")
    for table in "${REQUIRED_TABLES[@]}"; do
        if sqlite3 memory/index.db ".tables" | tr ' ' '\n' | grep -q "^$table$"; then
            echo "  ✓ PASS: Table exists: $table"
        else
            echo "  ✗ FAIL: Missing table: $table"
            all_passed=false
        fi
    done
else
    echo "  ✗ FAIL: Database file missing"
    all_passed=false
fi

# Test 3: Script Availability
echo ""
echo "Test 3: Script Availability"
echo "==========================="
SCRIPTS=(
    "scripts/record-failure.sh"
    "scripts/record-heuristic.sh"
    "query/query.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  ✓ PASS: $script exists"
    else
        echo "  ✗ FAIL: $script missing"
        all_passed=false
    fi
done

# Test 4: Query System Functionality
echo ""
echo "Test 4: Query System Functionality"
echo "=================================="
if python3 query/query.py --stats >/dev/null 2>&1; then
    echo "  ✓ PASS: query.py --stats works"
else
    echo "  ✗ FAIL: query.py --stats failed"
    all_passed=false
fi

if python3 query/query.py --golden-rules >/dev/null 2>&1; then
    echo "  ✓ PASS: query.py --golden-rules works"
else
    echo "  ✗ FAIL: query.py --golden-rules failed"
    all_passed=false
fi

# Test 5: Learning Metrics
echo ""
echo "Test 5: Learning Metrics"
echo "======================="
if ./scripts/learning-metrics.sh --json >/dev/null 2>&1; then
    echo "  ✓ PASS: learning-metrics.sh works"
else
    echo "  ✗ FAIL: learning-metrics.sh failed"
    all_passed=false
fi

# Final Summary
echo ""
echo "========================================="
echo "System Check Summary"
echo "========================================="

if [ "$all_passed" = true ]; then
    echo "🎉 ALL SYSTEM CHECKS PASSED"
    echo ""
    echo "The Emergent Learning Framework is fully functional."
    echo "Core components verified:"
    echo "  - Directory structure intact"
    echo "  - Database operational"
    echo "  - Query system responsive"
    echo "  - Metrics system working"
    exit 0
else
    echo "❌ SOME SYSTEM CHECKS FAILED"
    echo ""
    echo "There are issues with the Emergent Learning Framework that need attention."
    exit 1
fi