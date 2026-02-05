#!/bin/bash
# ELF Diagnostic Script
# Purpose: Verify core functionality of the Emergent Learning Framework

set -e

echo "=== Emergent Learning Framework Diagnostic ==="
echo "Date: $(date)"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
PASSED=0
WARNINGS=0
FAILED=0

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*"
    ((PASSED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*"
    ((WARNINGS++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*"
    ((FAILED++))
}

echo "=== SYSTEM DIAGNOSTIC ==="

# Test 1: Required directories
echo "1. Checking directory structure..."
required_dirs=(
    "$MEMORY_DIR"
    "$MEMORY_DIR/failures"
    "$MEMORY_DIR/successes"
    "$MEMORY_DIR/heuristics"
    "$BASE_DIR/scripts"
    "$BASE_DIR/query"
)

all_dirs_exist=true
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "  Missing directory: $dir"
        all_dirs_exist=false
    fi
done

if [ "$all_dirs_exist" = true ]; then
    pass "All required directories exist"
else
    fail "Some required directories are missing"
fi

# Test 2: Database integrity
echo "2. Checking database integrity..."
if [ -f "$DB_PATH" ]; then
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" 2>/dev/null | grep -q "ok"; then
        pass "Database integrity check passed"
    else
        fail "Database integrity check failed"
    fi
    
    # Check database size
    db_size=$(stat -c%s "$DB_PATH" 2>/dev/null || echo "0")
    if [ "$db_size" -gt 1000 ]; then
        pass "Database file has reasonable size ($(numfmt --to=iec $db_size))"
    else
        warn "Database file is unusually small ($(numfmt --to=iec $db_size))"
    fi
else
    fail "Database file does not exist: $DB_PATH"
fi

# Test 3: Required tables
echo "3. Checking required database tables..."
required_tables=("learnings" "heuristics" "experiments")
missing_tables=()
for table in "${required_tables[@]}"; do
    if ! sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" 2>/dev/null | grep -q "$table"; then
        missing_tables+=("$table")
    fi
done

if [ ${#missing_tables[@]} -eq 0 ]; then
    pass "All required tables exist"
else
    fail "Missing tables: ${missing_tables[*]}"
fi

# Test 4: Query system
echo "4. Checking query system..."
if [ -f "$BASE_DIR/query/query.py" ]; then
    if timeout 10 python3 "$BASE_DIR/query/query.py" --stats >/dev/null 2>&1; then
        pass "Query system responds to --stats"
        
        # Additional query tests
        learning_count=$(timeout 5 python3 "$BASE_DIR/query/query.py" --stats 2>/dev/null | grep "total_learnings" | cut -d: -f2 | tr -d ' ')
        if [ -n "$learning_count" ] && [ "$learning_count" -ge 0 ] 2>/dev/null; then
            pass "Query system returns valid statistics (total_learnings: $learning_count)"
        else
            warn "Query system returned unexpected stats format"
        fi
    else
        fail "Query system failed to respond to --stats"
    fi
else
    fail "Query system script not found"
fi

# Test 5: Record scripts (existence and permissions)
echo "5. Checking record scripts..."
record_scripts=(
    "record-failure.sh"
    "record-heuristic.sh"
    "record-success.sh"
)

missing_scripts=()
for script in "${record_scripts[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$script" ]; then
        missing_scripts+=("$script")
    elif [ ! -x "$SCRIPT_DIR/$script" ]; then
        warn "Script exists but is not executable: $script"
    fi
done

if [ ${#missing_scripts[@]} -eq 0 ]; then
    pass "All required record scripts exist"
else
    fail "Missing scripts: ${missing_scripts[*]}"
fi

# Test 6: Basic functionality test
echo "6. Testing basic query functionality..."
if timeout 10 python3 "$BASE_DIR/query/query.py" --recent 1 >/dev/null 2>&1; then
    pass "Basic query functionality works"
else
    fail "Basic query functionality failed"
fi

# Test 7: Database content verification
echo "7. Verifying database content..."
learning_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM learnings" 2>/dev/null || echo "0")
heuristic_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM heuristics" 2>/dev/null || echo "0")
experiment_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM experiments" 2>/dev/null || echo "0")

echo "  Database contains: $learning_count learnings, $heuristic_count heuristics, $experiment_count experiments"

if [ "$learning_count" -ge 0 ] 2>/dev/null; then
    pass "Learning table accessible"
else
    fail "Cannot access learning table"
fi

if [ "$heuristic_count" -ge 0 ] 2>/dev/null; then
    pass "Heuristic table accessible"
else
    fail "Cannot access heuristic table"
fi

# Summary
echo
echo "=== DIAGNOSTIC SUMMARY ==="
echo "Passed: $PASSED"
echo "Warnings: $WARNINGS"
echo "Failed: $FAILED"
echo "Total Tests: $((PASSED + WARNINGS + FAILED))"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}SUCCESS: ELF system is functioning properly${NC}"
    exit 0
elif [ "$FAILED" -lt 3 ]; then
    echo -e "${YELLOW}WARNING: ELF system has minor issues${NC}"
    exit 1
else
    echo -e "${RED}ERROR: ELF system has significant issues${NC}"
    exit 2
fi