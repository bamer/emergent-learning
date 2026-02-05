#!/bin/bash
# Minimal test script with colors

set -e

BASE_DIR="."
MEMORY_DIR="$BASE_DIR/memory"
SCRIPT_DIR="$BASE_DIR/scripts"
LOGS_DIR="$BASE_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

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

# Test function
test_directory_structure() {
    echo "=== Test 1: Directory Structure ==="
    
    local required_dirs=(
        "$MEMORY_DIR"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            pass "Directory exists: $dir"
        else
            echo "FAIL: Missing directory: $dir"
        fi
    done
    
    echo "Test function completed"
}

# Main execution
echo "========================================="
echo "Minimal Test with Colors"
echo "Started: $(date)"
echo "========================================="

test_directory_structure

echo "Script completed"