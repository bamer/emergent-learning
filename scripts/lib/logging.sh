#!/bin/bash
# Logging library for observability

declare -g LOG_INIT_DONE=0
declare -g SCRIPT_NAME=""
declare -g LOG_DIR=""
declare -g CORRELATION_ID=""

log_init() {
    SCRIPT_NAME="$1"
    LOG_DIR="${2:-.}"
    
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || return 1
    fi
    
    LOG_INIT_DONE=1
    return 0
}

log_get_correlation_id() {
    if [ -z "$CORRELATION_ID" ]; then
        CORRELATION_ID="${SCRIPT_NAME}_$(date +%s)_$$"
    fi
    echo "$CORRELATION_ID"
}

log_timer_start() {
    local timer_name="$1"
    eval "TIMER_${timer_name}_START=$(date +%s%N)"
}

log_timer_end() {
    local timer_name="$1"
    local start_var="TIMER_${timer_name}_START"
    local start_time="${!start_var}"
    
    if [ -z "$start_time" ]; then
        echo "0"
        return 1
    fi
    
    local end_time=$(date +%s%N)
    local duration=$((($end_time - $start_time) / 1000000))
    echo "$duration"
}

return 0
