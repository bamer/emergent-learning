#!/bin/bash
echo "=== Minimal Self-Test Diagnostic ==="

echo "1. Directory Structure Test..."
ls -la memory/ > /dev/null && echo "✓ PASS: Memory directory accessible" || echo "✗ FAIL: Memory directory inaccessible"

echo "2. Database Integrity Test..."
sqlite3 memory/index.db "PRAGMA integrity_check" | grep -q "ok" && echo "✓ PASS: Database integrity check passed" || echo "✗ FAIL: Database integrity check failed"

echo "3. Required Tables Test..."
for table in learnings heuristics experiments ceo_reviews; do
    if sqlite3 memory/index.db "SELECT name FROM sqlite_master WHERE type='table' AND name='$table'" | grep -q "$table"; then
        echo "✓ PASS: Table exists: $table"
    else
        echo "✗ FAIL: Missing table: $table"
    fi
done

echo "4. Script Functionality Test..."
[ -f "scripts/record-failure.sh" ] && [ -x "scripts/record-failure.sh" ] && echo "✓ PASS: record-failure.sh exists and executable" || echo "✗ FAIL: record-failure.sh missing or not executable"
[ -f "scripts/record-heuristic.sh" ] && [ -x "scripts/record-heuristic.sh" ] && echo "✓ PASS: record-heuristic.sh exists and executable" || echo "✗ FAIL: record-heuristic.sh missing or not executable"
[ -f "query/query.py" ] && echo "✓ PASS: query.py exists" || echo "✗ FAIL: query.py missing"

python3 query/query.py --stats > /dev/null 2>&1 && echo "✓ PASS: query.py --stats executes successfully" || echo "✗ FAIL: query.py --stats failed"

echo "5. File-Database Sync Test..."
failure_files=$(find "memory/failures" -name "*.md" -type f 2>/dev/null | wc -l)
success_files=$(find "memory/successes" -name "*.md" -type f 2>/dev/null | wc -l)
db_failures=$(sqlite3 memory/index.db "SELECT COUNT(*) FROM learnings WHERE type='failure'")
db_successes=$(sqlite3 memory/index.db "SELECT COUNT(*) FROM learnings WHERE type='success'")

echo "  Failure files: $failure_files, DB records: $db_failures"
echo "  Success files: $success_files, DB records: $db_successes"

echo "=== Diagnostic Complete ==="