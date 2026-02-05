#!/bin/bash
# Simple ELF Diagnostic

echo "=== Simple ELF Diagnostic ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"

echo "Directories:"
echo "  BASE_DIR: $BASE_DIR"
echo "  MEMORY_DIR: $MEMORY_DIR"
echo "  SCRIPT_DIR: $SCRIPT_DIR"

echo "Checking for required directories:"
required_dirs=(
    "$MEMORY_DIR"
    "$MEMORY_DIR/failures"
    "$MEMORY_DIR/successes"
    "$MEMORY_DIR/heuristics"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing"
    fi
done

echo "Checking database:"
if [ -f "$DB_PATH" ]; then
    echo "  ✓ Database file exists"
    size=$(stat -c%s "$DB_PATH" 2>/dev/null || echo "0")
    echo "  Database size: $(numfmt --to=iec $size)"
    
    echo "  Checking integrity:"
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check" 2>/dev/null | grep -q "ok"; then
        echo "  ✓ Database integrity OK"
    else
        echo "  ✗ Database integrity failed"
    fi
    
    echo "  Checking tables:"
    for table in learnings heuristics experiments; do
        if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" 2>/dev/null | grep -q "$table"; then
            echo "  ✓ Table $table exists"
        else
            echo "  ✗ Table $table missing"
        fi
    done
else
    echo "  ✗ Database file does not exist"
fi

echo "Checking query system:"
if [ -f "$BASE_DIR/query/query.py" ]; then
    echo "  ✓ Query script exists"
    if python3 "$BASE_DIR/query/query.py" --help >/dev/null 2>&1; then
        echo "  ✓ Query system responds to --help"
    else
        echo "  ✗ Query system failed --help"
    fi
else
    echo "  ✗ Query script missing"
fi

echo "Diagnostic complete."