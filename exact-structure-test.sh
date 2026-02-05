#!/bin/bash
# Exact structure test

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
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
FAILURE_DETAILS=()

# Logging setup
LOG_FILE="$LOGS_DIR/exact-structure-test-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$LOGS_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_FAILED++))
    FAILURE_DETAILS+=("$*")
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_WARNINGS++))
}

info() {
    echo -e "ℹ INFO: $*" | tee -a "$LOG_FILE"
}

# Test 1: Directory Structure
test_directory_structure() {
    log "=== Test 1: Directory Structure ==="

    local required_dirs=(
        "$MEMORY_DIR"
    )

    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            fail "Missing directory: $dir"
        fi
    done
}

# Main execution
main() {
    log "========================================="
    log "Exact Structure Test"
    log "Started: $(date)"
    log "========================================="

    test_directory_structure

    log "=== Test Summary ==="
    log "Tests Passed: $TESTS_PASSED"
    log "Tests Failed: $TESTS_FAILED"
    log "Warnings: $TESTS_WARNINGS"
    log "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

    if [ "$TESTS_FAILED" -eq 0 ]; then
        log "Overall Status: ${GREEN}ALL TESTS PASSED${NC}"
        return 0
    else
        log "Overall Status: ${RED}SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Run main
main
exit $?