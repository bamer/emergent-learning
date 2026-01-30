#!/bin/bash
# Enable WAL mode on ELF SQLite databases for better concurrent access
# WAL (Write-Ahead Logging) allows readers and writers to coexist

set -e

ELF_HOME="${HOME}/.opencode/emergent-learning"
DB_PATH="$ELF_HOME/memory/index.db"

echo "🔧 Enabling WAL mode on ELF database..."
echo "   Database: $DB_PATH"
echo ""

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Enable WAL mode
sqlite3 "$DB_PATH" "PRAGMA journal_mode=WAL;"

# Set busy timeout to 30 seconds (30000 milliseconds)
sqlite3 "$DB_PATH" "PRAGMA busy_timeout=30000;"

# Optimize WAL settings for our use case
sqlite3 "$DB_PATH" "PRAGMA wal_autocheckpoint=1000;"
sqlite3 "$DB_PATH" "PRAGMA synchronous=NORMAL;"

echo ""
echo "✅ WAL mode enabled successfully!"
echo ""
echo "Benefits:"
echo "  - Readers don't block writers"
echo "  - Writers don't block readers"
echo "  - Better concurrency for multi-process access"
echo "  - 30-second busy timeout for retries"
echo ""
echo "To verify: sqlite3 $DB_PATH 'PRAGMA journal_mode;'"
