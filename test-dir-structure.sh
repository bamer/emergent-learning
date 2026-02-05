#!/bin/bash

SCRIPT_DIR="/home/bamer/.opencode/emergent-learning/scripts"
BASE_DIR="/home/bamer/.opencode/emergent-learning"
MEMORY_DIR="$BASE_DIR/memory"
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
LOG_FILE="$LOGS_DIR/self-test-debug.log"

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
            echo "FAIL: Missing directory: $dir"
        fi
    done
}

test_directory_structure
echo "Test completed"