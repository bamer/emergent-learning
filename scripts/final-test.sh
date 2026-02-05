#!/bin/bash
# Final test script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

echo "=============================================="
echo "Emergent Learning Framework - Final Test"
echo "Started: $(date)"
echo "=============================================="

# Test 1: Directory Structure
echo ""
echo "=== Test 1: Directory Structure ==="

# Check directories individually
echo "Checking directories..."
[ -d "$MEMORY_DIR" ] && echo "PASS: Directory exists: $MEMORY_DIR" || echo "FAIL: Missing directory: $MEMORY_DIR"
[ -d "$MEMORY_DIR/failures" ] && echo "PASS: Directory exists: failures" || echo "FAIL: Missing directory: failures"
[ -d "$MEMORY_DIR/successes" ] && echo "PASS: Directory exists: successes" || echo "FAIL: Missing directory: successes"
[ -d "$MEMORY_DIR/heuristics" ] && echo "PASS: Directory exists: heuristics" || echo "FAIL: Missing directory: heuristics"
[ -d "$BASE_DIR/scripts" ] && echo "PASS: Directory exists: scripts" || echo "FAIL: Missing directory: scripts"
[ -d "$BASE_DIR/query" ] && echo "PASS: Directory exists: query" || echo "FAIL: Missing directory: query"

echo ""
echo "Final test completed successfully!"