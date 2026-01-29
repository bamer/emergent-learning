#!/bin/bash
# Error handling and utility functions library
# Provides consistent error handling, logging, and utility functions

set -o pipefail

# Exit codes
EXIT_SUCCESS=0
EXIT_VALIDATION_ERROR=1
EXIT_DB_ERROR=2
EXIT_GIT_ERROR=3
EXIT_FILESYSTEM_ERROR=4
EXIT_MISSING_DEPENDENCY=5
EXIT_LOCK_ERROR=8

export EXIT_SUCCESS EXIT_VALIDATION_ERROR EXIT_DB_ERROR EXIT_GIT_ERROR
export EXIT_FILESYSTEM_ERROR EXIT_MISSING_DEPENDENCY EXIT_LOCK_ERROR

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Array to hold cleanup functions
declare -a CLEANUP_FUNCTIONS=()

# ========================================
# Error handling
# ========================================

setup_error_trap() {
    trap 'handle_error $? $LINENO' ERR
}

handle_error() {
    local exit_code=$1
    local line_number=$2
    if [ -n "$BASH_SOURCE[1]" ]; then
        echo -e "${RED}Error in ${BASH_SOURCE[1]} at line $line_number (exit code: $exit_code)${NC}" >&2
        if [ -n "$CORRELATION_ID" ]; then
            echo "Correlation ID: $CORRELATION_ID" >&2
        fi
    fi
    run_cleanup_functions
    exit "$exit_code"
}

register_cleanup() {
    CLEANUP_FUNCTIONS+=("$1")
}

run_cleanup_functions() {
    for func in "${CLEANUP_FUNCTIONS[@]}"; do
        if declare -f "$func" > /dev/null; then
            "$func" 2>/dev/null || true
        fi
    done
}

# ========================================
# Logging functions
# ========================================

log_info() {
    local message="$1"
    echo -e "${BLUE}[INFO]${NC} $message" >&2
}

log_success() {
    local message="$1"
    echo -e "${GREEN}[✓]${NC} $message" >&2
}

log_warn() {
    local message="$1"
    echo -e "${YELLOW}[WARN]${NC} $message" >&2
}

log_error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" >&2
}

report_status() {
    local status="$1"
    local message="$2"
    case "$status" in
        success) log_success "$message" ;;
        warning) log_warn "$message" ;;
        error) log_error "$message" ;;
        info) log_info "$message" ;;
        *) echo "$message" ;;
    esac
}

# ========================================
# Validation functions
# ========================================

validate_not_empty() {
    local value="$1"
    local field_name="$2"
    
    if [ -z "$value" ]; then
        error_msg "$EXIT_VALIDATION_ERROR" \
            "Validation failed: $field_name is required" \
            "Provide a non-empty value for $field_name" \
            "fatal"
        exit "$EXIT_VALIDATION_ERROR"
    fi
}

validate_file_exists() {
    local filepath="$1"
    local description="${2:-File}"
    
    if [ ! -f "$filepath" ]; then
        error_msg "$EXIT_FILESYSTEM_ERROR" \
            "$description not found" \
            "Expected file at: $filepath" \
            "fatal"
        exit "$EXIT_FILESYSTEM_ERROR"
    fi
}

validate_db_id() {
    local id="$1"
    local entity="${2:-entity}"
    
    if [ -z "$id" ] || ! [[ "$id" =~ ^[0-9]+$ ]]; then
        error_msg "$EXIT_DB_ERROR" \
            "Invalid database ID returned for $entity" \
            "Got: $id" \
            "fatal"
        exit "$EXIT_DB_ERROR"
    fi
}

require_command() {
    local cmd="$1"
    local install_msg="$2"
    
    if ! command -v "$cmd" &> /dev/null; then
        error_msg "$EXIT_MISSING_DEPENDENCY" \
            "Required command not found: $cmd" \
            "${install_msg:-Install $cmd and try again}" \
            "fatal"
        exit "$EXIT_MISSING_DEPENDENCY"
    fi
}

require_file() {
    local filepath="$1"
    local error_msg_text="$2"
    
    if [ ! -f "$filepath" ]; then
        error_msg "$EXIT_FILESYSTEM_ERROR" \
            "${error_msg_text:-File not found: $filepath}" \
            "Check that the file exists and is readable" \
            "fatal"
        exit "$EXIT_FILESYSTEM_ERROR"
    fi
}

# ========================================
# Filesystem functions
# ========================================

safe_mkdir() {
    local dir="$1"
    local message="${2:-Creating directory}"
    
    if ! mkdir -p "$dir" 2>/dev/null; then
        error_msg "$EXIT_FILESYSTEM_ERROR" \
            "Failed to create directory: $dir" \
            "Check permissions and available disk space" \
            "fatal"
        exit "$EXIT_FILESYSTEM_ERROR"
    fi
    log_info "$message: $dir"
}

# ========================================
# Database functions
# ========================================

check_db_integrity() {
    local db_path="$1"
    
    if [ ! -f "$db_path" ]; then
        log_warn "Database file not found: $db_path"
        return 0
    fi
    
    # Try to run PRAGMA integrity_check
    if ! sqlite3 "$db_path" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        log_warn "Database integrity check failed for: $db_path"
    fi
}

escape_sql() {
    local string="$1"
    # Escape single quotes by doubling them
    printf "%s" "${string//\'/\'\'}"
}

sqlite_with_retry() {
    local db_path="$1"
    local max_retries=3
    local retry_count=0
    local output
    
    while [ $retry_count -lt $max_retries ]; do
        output=$(sqlite3 "$db_path" 2>&1)
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "$output"
            return 0
        fi
        
        if [[ "$output" == *"database is locked"* ]]; then
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                log_warn "Database locked, retrying... ($retry_count/$max_retries)"
                sleep 1
                continue
            fi
        fi
        
        log_error "Database error: $output"
        return "$exit_code"
    done
    
    return "$EXIT_DB_ERROR"
}

# ========================================
# Git functions
# ========================================

safe_git_add() {
    local path="$1"
    local message="${2:-Adding path}"
    
    if [ -d "$(git rev-parse --git-dir 2>/dev/null)" ]; then
        if ! git add "$path" 2>/dev/null; then
            log_warn "Failed to git add: $path"
            return 1
        fi
        log_info "$message: $path"
        return 0
    fi
    return 1
}

safe_git_commit() {
    local message="$1"
    local description="${2:-}"
    
    if [ -d "$(git rev-parse --git-dir 2>/dev/null)" ]; then
        if [ -n "$description" ]; then
            git commit -m "$message" -m "$description" 2>/dev/null
        else
            git commit -m "$message" 2>/dev/null
        fi
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log_success "Git commit created: $message"
            return 0
        elif [ $exit_code -eq 1 ]; then
            log_warn "No changes to commit"
            return 1
        else
            log_error "Git commit failed with exit code: $exit_code"
            return "$exit_code"
        fi
    fi
    return 1
}

acquire_git_lock() {
    local lock_file="$1"
    local timeout="${2:-30}"
    local elapsed=0
    
    while [ $elapsed -lt "$timeout" ]; do
        if mkdir "$lock_file" 2>/dev/null; then
            echo $$ > "$lock_file/pid"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    return 1
}

release_git_lock() {
    local lock_file="$1"
    
    if [ -d "$lock_file" ]; then
        rm -rf "$lock_file" 2>/dev/null || true
    fi
}

# ========================================
# Error reporting
# ========================================

error_msg() {
    local exit_code="$1"
    local title="$2"
    local details="$3"
    local severity="${4:-error}"
    
    case "$severity" in
        fatal)
            log_error "$title"
            if [ -n "$details" ]; then
                log_error "Details: $details"
            fi
            ;;
        error)
            log_error "$title"
            if [ -n "$details" ]; then
                log_error "Details: $details"
            fi
            ;;
        warning)
            log_warn "$title"
            if [ -n "$details" ]; then
                log_warn "Details: $details"
            fi
            ;;
        info)
            log_info "$title"
            if [ -n "$details" ]; then
                log_info "Details: $details"
            fi
            ;;
    esac
}

return 0
