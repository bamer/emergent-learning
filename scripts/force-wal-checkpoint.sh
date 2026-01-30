#!/bin/bash
# Force WAL checkpoint and release locks for ELF database
# Use this when database is locked by long-running processes

set -e

DB_PATH="${HOME}/.opencode/emergent-learning/memory/index.db"

echo "🔓 Forcing WAL checkpoint to release locks..."
echo "   Database: $DB_PATH"
echo ""

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Check current WAL status
echo "Current WAL status:"
sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);" 2>&1 || true
echo ""

# Get WAL info
echo "WAL file size:"
ls -lh "${DB_PATH}-wal" 2>/dev/null || echo "  No WAL file (already checkpointed)"
echo ""

# Force checkpoint to truncate WAL
echo "Executing TRUNCATE checkpoint..."
sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);" 2>&1
echo ""

# Verify
echo "✅ Checkpoint completed!"
echo ""
echo "WAL file size after checkpoint:"
ls -lh "${DB_PATH}-wal" 2>/dev/null || echo "  WAL file truncated successfully"
