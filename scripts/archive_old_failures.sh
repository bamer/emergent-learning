#!/bin/bash
# =====================================================================
# Database Maintenance: Archive Old Failure Embeddings
# =====================================================================
# Purpose: Archive failure embeddings older than 15 days
# Schedule: Run weekly via cron
# =====================================================================

set -e

# Configuration
ELF_DIR="/home/bamer/.opencode/emergent-learning"
DB_PATH="$ELF_DIR/memory/index.db"
ARCHIVE_DIR="$ELF_DIR/archives/failure_embeddings"
BACKUP_RETENTION_DAYS=90

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$ELF_DIR/.coordination/maintenance.log"
DATE_15_DAYS_AGO=$(date -d "15 days ago" "+%Y-%m-%d %H:%M:%S")

# Create archive directory if needed
mkdir -p "$ARCHIVE_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting failure embedding archive maintenance..."

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    log "❌ Database not found: $DB_PATH"
    exit 1
fi

# Count failures older than 15 days
OLD_FAILURES=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*)
    FROM embeddings
    WHERE source_type = 'failure'
    AND created_at < datetime('$DATE_15_DAYS_AGO')
")

log "📊 Old failures found (>15 days): $OLD_FAILURES"

if [ "$OLD_FAILURES" -eq 0 ]; then
    log "✅ No old failures to archive"
    exit 0
fi

# Create backup before archival
BACKUP_PATH="$ELF_DIR/memory/index_backup_before_archive_$TIMESTAMP.db"
sqlite3 "$DB_PATH" ".backup '$BACKUP_PATH'"
log "💾 Backup created: $BACKUP_PATH"

# Export old failures to CSV
ARCHIVE_CSV="$ARCHIVE_DIR/failures_before_${TIMESTAMP}.csv"
sqlite3 "$DB_PATH" "
.mode csv
.headers on
.output '$ARCHIVE_CSV'
SELECT id, source_id, source_type, text_content, metadata, created_at
FROM embeddings
WHERE source_type = 'failure'
AND created_at < datetime('$DATE_15_DAYS_AGO');
.output stdout
.log off
"

log "📄 Archived $OLD_FAILURES failures to: $ARCHIVE_CSV"

# Remove old failures from database
sqlite3 "$DB_PATH" "
BEGIN TRANSACTION;
DELETE FROM embeddings
WHERE source_type = 'failure'
AND created_at < datetime('$DATE_15_DAYS_AGO');
COMMIT;
"

# Verify deletion
REMAINING_OLD=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*)
    FROM embeddings
    WHERE source_type = 'failure'
    AND created_at < datetime('$DATE_15_DAYS_AGO')
")

if [ "$REMAINING_OLD" -gt 0 ]; then
    log "❌ Archive failed: $REMAINING_OLD old failures remain"
    exit 1
fi

log "✅ Successfully archived $OLD_FAILURES old failures"

# Get current database stats
CURRENT_FAILURES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM embeddings WHERE source_type = 'failure'")
TOTAL_EMBEDDINGS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM embeddings")

log "📈 Current database state:"
log "   - Total embeddings: $TOTAL_EMBEDDINGS"
log "   - Current failures: $CURRENT_FAILURES"
log "   - Archived records: $OLD_FAILURES"

# Cleanup old backups (older than BACKUP_RETENTION_DAYS)
find "$ELF_DIR/memory" -name "index_backup_before_archive_*.db" -mtime +$BACKUP_RETENTION_DAYS -delete
log "🗑️  Cleaned up backups older than $BACKUP_RETENTION_DAYS days"

# Compress old CSV archives (older than 30 days)
find "$ARCHIVE_DIR" -name "failures_before_*.csv" -mtime +30 -exec gzip {} \;
log "📦 Compressed old CSV archives"

log "✨ Maintenance complete!"

# Summary
echo ""
echo "═════════════════════════════════════════════"
echo "FAILURE EMBEDDING ARCHIVE SUMMARY"
echo "═════════════════════════════════════════════"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Archived: $OLD_FAILURES failures (>15 days old)"
echo "Archive: $ARCHIVE_CSV"
echo "Backup: $BACKUP_PATH"
echo "Current failures: $CURRENT_FAILURES"
echo "Total embeddings: $TOTAL_EMBEDDINGS"
echo "═════════════════════════════════════════════"

exit 0
