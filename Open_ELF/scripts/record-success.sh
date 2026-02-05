#!/bin/bash
# Record a success in the Emergent Learning Framework
#
# Usage (interactive): ./record-success.sh
# Usage (non-interactive):
#   SUCCESS_TITLE="title" SUCCESS_DOMAIN="domain" SUCCESS_SUMMARY="summary" ./record-success.sh
#   Or: ./record-success.sh --title "title" --domain "domain" --summary "summary"
#   Optional: --impact high --tags "tag1,tag2"

set -e

# SECURITY FIX: Restrictive umask for all file operations
umask 0077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
MEMORY_DIR="$BASE_DIR/memory"
DB_PATH="$MEMORY_DIR/index.db"
SUCCESSES_DIR="$MEMORY_DIR/successes"
LOGS_DIR="$BASE_DIR/logs"

# Capture date once at script start for consistency
EXECUTION_DATE=$(date +%Y%m%d)

# Setup logging
LOG_FILE="$LOGS_DIR/${EXECUTION_DATE}.log"
mkdir -p "$LOGS_DIR"

log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] [record-success] $*" >> "$LOG_FILE"
    if [ "$level" = "ERROR" ]; then
        echo "ERROR: $*" >&2
    fi
}

# SQLite retry function with WAL mode support and IMMEDIATE transaction
sqlite_with_retry() {
    local max_attempts=20
    local attempt=1
    local timeout_ms=5000  # 5 seconds per attempt
    
    while [ $attempt -le $max_attempts ]; do
        # Try with busy timeout set and IMMEDIATE mode for write priority
        if sqlite3 "$DB_PATH" "PRAGMA busy_timeout=$timeout_ms; PRAGMA journal_mode=WAL; BEGIN IMMEDIATE; $@; COMMIT;" 2>/dev/null; then
            return 0
        fi
        
        log "WARN" "SQLite busy (WAL mode), retry $attempt/$max_attempts..."
        echo "SQLite busy, retry $attempt/$max_attempts..." >&2
        sleep 0.$((RANDOM % 3 + 1))
        ((attempt++))
    done
    
    log "ERROR" "SQLite failed after $max_attempts attempts"
    echo "SQLite failed after $max_attempts attempts" >&2
    return 1
}

# Pre-flight validation
preflight_check() {
    log "INFO" "Starting pre-flight checks"

    if [ ! -f "$DB_PATH" ]; then
        log "ERROR" "Database not found: $DB_PATH"
        exit 1
    fi

    if ! command -v sqlite3 &> /dev/null; then
        log "ERROR" "sqlite3 command not found"
        exit 1
    fi

    # Database integrity check
    if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check" 2>/dev/null | grep -q "ok"; then
        log "ERROR" "Database integrity check failed"
        exit 1
    fi

    log "INFO" "Pre-flight checks passed"
}

preflight_check

# Ensure successes directory exists
mkdir -p "$SUCCESSES_DIR"

log "INFO" "Script started"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --title) title="$2"; shift 2 ;;
        --domain) domain="$2"; shift 2 ;;
        --impact) impact="$2"; shift 2 ;;
        --tags) tags="$2"; shift 2 ;;
        --summary) summary="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Check for environment variables (override empty values)
title="${title:-$SUCCESS_TITLE}"
domain="${domain:-$SUCCESS_DOMAIN}"
impact="${impact:-$SUCCESS_IMPACT}"
tags="${tags:-$SUCCESS_TAGS}"
summary="${summary:-$SUCCESS_SUMMARY}"

# Non-interactive mode: if we have title and domain, skip prompts
if [ -n "$title" ] && [ -n "$domain" ]; then
    log "INFO" "Running in non-interactive mode"
    # Validate impact is valid
    case "$impact" in
        low|medium|high|critical) ;; # valid
        *) impact="medium" ;; # default
    esac
    tags="${tags:-}"
    summary="${summary:-No summary provided}"
    echo "=== Record Success (non-interactive) ==="
else
    # Interactive mode
    log "INFO" "Running in interactive mode"
    echo "=== Record Success ==="
    echo ""

    read -p "Title: " title
    if [ -z "$title" ]; then
        log "ERROR" "Title cannot be empty"
        exit 1
    fi

    read -p "Domain (coordination/architecture/debugging/etc): " domain
    if [ -z "$domain" ]; then
        log "ERROR" "Domain cannot be empty"
        exit 1
    fi

    read -p "Impact (low/medium/high/critical) [medium]: " impact
    if [ -z "$impact" ]; then
        impact="medium"
    fi

    read -p "Tags (comma-separated): " tags

    echo "Summary (press Enter twice when done):"
    summary=""
    while IFS= read -r line; do
        [ -z "$line" ] && break
        summary="${summary}${line}\n"
    done
fi

log "INFO" "Recording success: $title (domain: $domain, impact: $impact)"

# Input length validation
MAX_TITLE_LENGTH=500
MAX_DOMAIN_LENGTH=100
MAX_SUMMARY_LENGTH=50000

if [ ${#title} -gt $MAX_TITLE_LENGTH ]; then
    log "ERROR" "Title exceeds maximum length ($MAX_TITLE_LENGTH characters)"
    echo "ERROR: Title too long (max $MAX_TITLE_LENGTH characters)" >&2
    exit 1
fi

if [ ${#domain} -gt $MAX_DOMAIN_LENGTH ]; then
    log "ERROR" "Domain exceeds maximum length ($MAX_DOMAIN_LENGTH characters)"
    echo "ERROR: Domain too long (max $MAX_DOMAIN_LENGTH characters)" >&2
    exit 1
fi

if [ ${#summary} -gt $MAX_SUMMARY_LENGTH ]; then
    log "ERROR" "Summary exceeds maximum length"
    echo "ERROR: Summary too long (max $MAX_SUMMARY_LENGTH characters)" >&2
    exit 1
fi

# Trim leading/trailing whitespace
title=$(echo "$title" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
domain=$(echo "$domain" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

# Re-validate after trimming
if [ -z "$title" ]; then
    log "ERROR" "Title cannot be empty (or whitespace-only)"
    echo "ERROR: Title cannot be empty" >&2
    exit 1
fi

if [ -z "$domain" ]; then
    log "ERROR" "Domain cannot be empty (or whitespace-only)"
    echo "ERROR: Domain cannot be empty" >&2
    exit 1
fi

# Generate filename
date_prefix="${EXECUTION_DATE}"
filename_title=$(echo "$title" | tr ':[:upper:]:' ':[:lower:]:' | tr ' ' '-' | tr -cd ':[:alnum:]-' | cut -c1-100)
filename="${date_prefix}_${filename_title}.md"
filepath="$SUCCESSES_DIR/$filename"
relative_path="memory/successes/$filename"

# Create markdown file
cat > "$filepath" <<EOF
# $title

**Domain**: $domain
**Impact**: $impact
**Tags**: $tags
**Date**: ${date_prefix:0:4}-${date_prefix:4:2}-${date_prefix:6:2}

## Summary

$summary

## What Worked

[Describe the success in detail]

## Key Factors

[What made this successful?]

## Impact

[What were the positive outcomes?]

## Replicability

[How can this success be replicated?]

## Related

- **Experiments**:
- **Heuristics**:
- **Similar Successes**:
EOF

echo "Created: $filepath"
log "INFO" "Created markdown file: $filepath"

# Sanitize input: strip ANSI escapes, control chars, CRLF
sanitize_input() {
    local input="$1"
    # Remove ANSI escape sequences
    input=$(printf '%s' "$input" | sed 's/\x1b\[[0-9;]*[mGKHF]//g')
    # Remove control characters except newline/tab
    input=$(printf '%s' "$input" | tr -d '\000-\010\013-\037\177')
    # Convert CRLF to space
    input=$(printf '%s' "$input" | tr '\r\n' '  ')
    printf '%s' "$input"
}

# Escape single quotes for SQL injection protection
escape_sql() {
    echo "${1//\'/\'\'}"
}

# SECURITY: Sanitize ALL user inputs before processing
title=$(sanitize_input "$title")
domain=$(sanitize_input "$domain")
summary=$(sanitize_input "$summary")
tags=$(sanitize_input "$tags")

# Prepare data for database
now=$(date '+%Y-%m-%d %H:%M:%S')

# Try to write directly or queue if database is locked
queue_script="$SCRIPT_DIR/db-queue.py"

if [ -f "$queue_script" ]; then
    # Use Python queue system
    data=$(python3 -c "
import json
data = {
    'type': 'success',
    'filepath': '$relative_path',
    'title': '''$title''',
    'summary': '''$(echo -e "$summary" | head -n 1)''',
    'tags': '$tags',
    'domain': '$domain',
    'severity': '$impact',
    'created_at': '$now'
}
print(json.dumps(data))
")
    
    if python3 "$queue_script" --try-write "$data" 2>/dev/null; then
        echo "✅ Database record created (via direct write or queue)"
        log "INFO" "Success recorded: $title"
    else
        # Fallback: try direct insert with retry
        title_escaped=$(escape_sql "$title")
        summary_escaped=$(escape_sql "$(echo -e "$summary" | head -n 1)")
        tags_escaped=$(escape_sql "$tags")
        domain_escaped=$(escape_sql "$domain")
        
        if ! LAST_ID=$(sqlite_with_retry "$DB_PATH" <<SQL
INSERT INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at)
VALUES (
    'success',
    '$relative_path',
    '$title_escaped',
    '$summary_escaped',
    '$tags_escaped',
    '$domain_escaped',
    '$impact',
    '$now'
);
SELECT last_insert_rowid();
SQL
); then
            log "ERROR" "Failed to insert into database - write queued for later processing"
            echo "⚠️  Database locked - success recorded to file only"
            echo "   Run 'python3 scripts/db-queue.py --process-queue' to sync later"
        else
            echo "Database record created (ID: $LAST_ID)"
            log "INFO" "Database record created (ID: $LAST_ID)"
        fi
    fi
else
    # Fallback: direct insert only
    title_escaped=$(escape_sql "$title")
    summary_escaped=$(escape_sql "$(echo -e "$summary" | head -n 1)")
    tags_escaped=$(escape_sql "$tags")
    domain_escaped=$(escape_sql "$domain")
    
    if ! LAST_ID=$(sqlite_with_retry "$DB_PATH" <<SQL
INSERT INTO learnings (type, filepath, title, summary, tags, domain, severity, created_at)
VALUES (
    'success',
    '$relative_path',
    '$title_escaped',
    '$summary_escaped',
    '$tags_escaped',
    '$domain_escaped',
    '$impact',
    '$now'
);
SELECT last_insert_rowid();
SQL
); then
        log "ERROR" "Failed to insert into database"
        exit 1
    fi
    
    echo "Database record created (ID: $LAST_ID)"
    log "INFO" "Database record created (ID: $LAST_ID)"
fi

log "INFO" "Success recorded successfully: $title"
echo ""
echo "Success recorded successfully!"
echo "Edit the full details at: $filepath"
