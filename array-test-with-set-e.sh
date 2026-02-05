#!/bin/bash
# Test array iteration with tee and set -e

set -e

LOGS_DIR="/home/bamer/.opencode/emergent-learning/logs"
mkdir -p "$LOGS_DIR"

LOG_FILE="$LOGS_DIR/array-test-with-set-e-$(date +%Y%m%d-%H%M%S).log"

pass() {
    echo -e "PASS: $*" | tee -a "$LOG_FILE"
}

test_array_iteration() {
    local required_dirs=(
        "/home/bamer/.opencode/emergent-learning/memory"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "Processing directory: $dir"
            pass "Directory exists: $dir"
            echo "Done processing directory: $dir"
        fi
    done
}

echo "Starting array test with set -e"
test_array_iteration
echo "Array test with set -e completed"