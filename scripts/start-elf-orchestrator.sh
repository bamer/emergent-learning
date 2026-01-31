#!/bin/bash
#
# Unified startup script for ELF Agent Orchestrator
# Ensures all agents use the same orchestration system
#
# Usage: ./start-elf-orchestrator.sh [start|status]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"
ORCHESTRATOR_DIR="$ELF_DIR/Open_ELF/orchestrator"
ORCHESTRATOR_SCRIPT="$ORCHESTRATOR_DIR/orchestrator.py"
LOGS_DIR="$ELF_DIR/Open_ELF/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log_error "Python not found. Install from https://python.org"
    exit 1
fi

# Check if orchestrator exists
if [ ! -f "$ORCHESTRATOR_SCRIPT" ]; then
    log_error "Orchestrator script not found at $ORCHESTRATOR_SCRIPT"
    exit 1
fi

# Check if opencode CLI is available
if ! command -v opencode &> /dev/null; then
    log_error "opencode CLI not found"
    log_error "Install with: npm install -g opencode"
    log_error "Or: npx opencode (to run directly)"
    exit 1
fi

# Check if OpenCode server is running
log "Checking if OpenCode server is running..."
if ! curl -s http://localhost:4096/health &> /dev/null; then
    log_warning "OpenCode server doesn't seem to be running on port 4096"
    log "Please start it with: opencode serve --port 4096"
    log ""
    
    # In non-interactive mode, try to start automatically
    if [ -t 0 ]; then
        read -p "Do you want to start the server now? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Starting OpenCode server in background..."
            nohup opencode serve --port 4096 > "$LOGS_DIR/opencode-server.log" 2>&1 &
            SERVER_PID=$!
            log "OpenCode server started with PID: $SERVER_PID"
            log "Waiting 5 seconds for server to initialize..."
            sleep 5
        else
            log_error "Exiting. Please start OpenCode server manually."
            exit 1
        fi
    else
        log "Non-interactive mode: attempting to start server..."
        nohup opencode serve --port 4096 > "$LOGS_DIR/opencode-server.log" 2>&1 &
        sleep 5
    fi
fi

# Verify server is now running
if curl -s http://localhost:4096/health &> /dev/null; then
    log_success "OpenCode server is running"
else
    log_error "OpenCode server failed to start. Check logs: $LOGS_DIR/opencode-server.log"
    exit 1
fi

# Change to ELF directory
cd "$ELF_DIR"

# Check if orchestrator is already running
if pgrep -f "orchestrator.py" > /dev/null; then
    log_warning "Orchestrator is already running"
    log "Use './stop-elf-orchestrator.sh' to stop it first"
    exit 1
fi

# Start orchestrator
log "Starting ELF Unified Orchestrator..."
log "Log directory: $LOGS_DIR"
log "Press Ctrl+C to stop"
log ""

# Start the orchestrator
exec $PYTHON_CMD "$ORCHESTRATOR_SCRIPT" start
