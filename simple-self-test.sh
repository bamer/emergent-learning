#!/bin/bash
# Simplified Self-Test Script for Emergent Learning Framework

set -e

SCRIPT_DIR="$HOME/.opencode/emergent-learning/scripts"
BASE_DIR="$HOME/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

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

# Test 1: Directory Structure
test_directory_structure() {
    echo "=== Test 1: Directory Structure ==="
    
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
}

# Test 3: File-Database Sync
test_file_database_sync() {
    echo "=== Test 3: File-Database Synchronization ==="
    
    # Count files in each category
    local failure_files=$(find "$MEMORY_DIR/failures" -name "*.md" -type f 2>/dev/null | wc -l)
    local success_files=$(find "$MEMORY_DIR/successes" -name "*.md" -type f 2>/dev/null | wc -l)
    
    # Count DB records
    local db_failures=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings WHERE type='failure'")
    local db_successes=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings WHERE type='success'")
    
    echo "Failure files: $failure_files, DB records: $db_failures"
    echo "Success files: $success_files, DB records: $db_successes"
    
    # Allow some discrepancy due to TEMPLATE files
    if [ "$((failure_files - db_failures))" -le 1 ] && [ "$((failure_files - db_failures))" -ge -1 ]; then
        pass "Failure files and DB records are synchronized"
    else
        warn "Mismatch: $failure_files failure files vs $db_failures DB records"
    fi
    
    if [ "$((success_files - db_successes))" -le 10 ] && [ "$((success_files - db_successes))" -ge -10 ]; then
        pass "Success files and DB records are synchronized"
    else
        warn "Mismatch: $success_files success files vs $db_successes DB records"
    fi
}

# Test 4: Script Functionality
test_script_functionality() {
    echo "=== Test 4: Script Functionality ==="
    
    local required_scripts=(
        "$SCRIPT_DIR/record-failure.sh"
        "$SCRIPT_DIR/record-heuristic.sh"
        "$SCRIPT_DIR/init.sh"
        "$BASE_DIR/query/query.py"
    )
    
    # Check if scripts directory exists
    if [ ! -d "$SCRIPT_DIR" ]; then
        fail "Scripts directory does not exist: $SCRIPT_DIR"
        return
    fi
    
    for script in "${required_scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ] || [[ "$script" == *.py ]]; then
                pass "Script exists and is executable: $(basename $script)"
            else
                warn "Script exists but is not executable: $(basename $script)"
            fi
        else
            fail "Missing script: $(basename $script)"
        fi
    done
    
    # Test query.py basic functionality
    if $PYTHON_CMD "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
        pass "query.py --stats executes successfully"
    else
        fail "query.py --stats failed to execute"
    fi
}

# Test 5: Memory System Tests
test_memory_system() {
    echo "=== Test 5: Memory System ==="
    
    # Test recent query
    if $PYTHON_CMD "$BASE_DIR/query/query.py" --recent 1 >/dev/null 2>&1; then
        pass "Recent learnings query works"
    else
        fail "Recent learnings query failed"
    fi
    
    # Test domain query (use a domain we know exists)
    local domains=$(sqlite3 "$DB_PATH" "SELECT DISTINCT domain FROM learnings LIMIT 1")
    if [ -n "$domains" ]; then
        if $PYTHON_CMD "$BASE_DIR/query/query.py" --domain "$domains" --limit 1 >/dev/null 2>&1; then
            pass "Domain query works"
        else
            fail "Domain query failed"
        fi
    else
        warn "No domains found in database to test query"
    fi
    
    # Test stats query
    local stats=$($PYTHON_CMD "$BASE_DIR/query/query.py" --stats 2>/dev/null)
    if echo "$stats" | grep -q "total_learnings"; then
        pass "Statistics query works"
    else
        fail "Statistics query failed or returned unexpected format"
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "Emergent Learning Framework - Simple Self-Test"
    echo "Started: $(date)"
    echo "========================================="
    
    test_directory_structure
    test_database_integrity
    test_file_database_sync
    test_script_functionality
    test_memory_system
    
    echo "=== Self-Test Summary ==="
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Warnings: $TESTS_WARNINGS"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo "Overall Status: ${GREEN}ALL TESTS PASSED${NC}"
        return 0
    else
        echo "Overall Status: ${RED}SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Run main
main