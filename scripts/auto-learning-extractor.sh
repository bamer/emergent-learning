#!/bin/bash
# Auto Learning Extractor
# Periodically checks for unprocessed session logs and triggers learning extraction

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SESSIONS_LOGS_DIR="$BASE_DIR/sessions/logs"
PROCESSED_MARKER="$BASE_DIR/sessions/.processed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_info() {
    log "${GREEN}INFO${NC}: $*"
}

log_warn() {
    log "${YELLOW}WARN${NC}: $*"
}

log_error() {
    log "${RED}ERROR${NC}: $*"
}

# Check if required directories exist
if [ ! -d "$SESSIONS_LOGS_DIR" ]; then
    log_info "Sessions logs directory not found, creating: $SESSIONS_LOGS_DIR"
    mkdir -p "$SESSIONS_LOGS_DIR"
fi

# Get list of unprocessed log files
get_unprocessed_files() {
    local unprocessed=()
    
    # If processed marker doesn't exist, all files are unprocessed
    if [ ! -f "$PROCESSED_MARKER" ]; then
        # Find all session log files
        while IFS= read -r -d '' file; do
            unprocessed+=("$file")
        done < <(find "$SESSIONS_LOGS_DIR" -name "*_session.jsonl" -print0 2>/dev/null || true)
    else
        # Load processed files list
        if [ -f "$PROCESSED_MARKER" ]; then
            processed_files=$(jq -r '.processed_files[]' "$PROCESSED_MARKER" 2>/dev/null || echo "")
        else
            processed_files=""
        fi
        
        # Find all session log files and filter out processed ones
        while IFS= read -r -d '' file; do
            filename=$(basename "$file")
            if ! echo "$processed_files" | grep -q "^${filename}$"; then
                unprocessed+=("$file")
            fi
        done < <(find "$SESSIONS_LOGS_DIR" -name "*_session.jsonl" -print0 2>/dev/null || true)
    fi
    
    # Return the array
    printf '%s\0' "${unprocessed[@]}"
}

# Main processing function
process_logs() {
    log_info "Checking for unprocessed session logs..."
    
    # Get unprocessed files
    local unprocessed_files=()
    while IFS= read -r -d '' file; do
        unprocessed_files+=("$file")
    done < <(get_unprocessed_files)
    
    if [ ${#unprocessed_files[@]} -eq 0 ]; then
        log_info "No unprocessed session logs found"
        return 0
    fi
    
    log_info "Found ${#unprocessed_files[@]} unprocessed log file(s)"
    
    # Trigger learning extractor
    local extractor_script="$BASE_DIR/agents/learning-extractor/run_extractor.py"
    if [ ! -f "$extractor_script" ]; then
        log_error "Learning extractor script not found: $extractor_script"
        return 1
    fi
    
    log_info "Triggering learning extractor for ${#unprocessed_files[@]} file(s)..."
    
    # Build command with all unprocessed files
    local cmd=("python3" "$extractor_script")
    for file in "${unprocessed_files[@]}"; do
        cmd+=("$file")
    done
    
    # Run extractor in background
    if "${cmd[@]}" >/dev/null 2>&1 & then
        log_info "Learning extractor started successfully (PID: $!)"
        return 0
    else
        log_error "Failed to start learning extractor"
        return 1
    fi
}

# Run once
process_logs