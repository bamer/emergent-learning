#!/bin/bash
# Minimal test to isolate the hanging issue

# Remove set -e to see if that's causing issues
# set -e

SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
LOGS_DIR="$BASE_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

# Logging setup
LOG_FILE="$LOGS_DIR/minimal-test-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$LOGS_DIR"

echo "Starting minimal test, LOG_FILE=$LOG_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $*" | tee -a "$LOG_FILE"
    ((TESTS_PASSED++))
}

# Test 1: Directory Structure
test_directory_structure() {
    log "=== Test 1: Directory Structure ==="
    
    local required_dirs=(
        "$MEMORY_DIR"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "About to call pass function"
            pass "Directory exists: $dir"
            echo "Finished pass function"
        else
            echo "Directory missing: $dir"
        fi
    done
}

# Main execution
main() {
    log "========================================="
    log "Minimal Test"
    log "Started: $(date)"
    log "========================================="
    
    test_directory_structure
    
    log "=== Test Summary ==="
    log "Tests Passed: $TESTS_PASSED"
    log "Tests Failed: $TESTS_FAILED"
    log "Warnings: $TESTS_WARNINGS"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        log "Overall Status: ${GREEN}ALL TESTS PASSED${NC}"
        return 0
    else
        log "Overall Status: ${RED}SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Run main
echo "About to call main"
main
echo "Script completed"