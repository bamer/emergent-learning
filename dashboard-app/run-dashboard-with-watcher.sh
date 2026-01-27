#!/bin/bash
# Emergent Learning Dashboard Launcher with Watcher
# Launches backend, frontend, and watcher in one command
# Run from dashboard-app/ directory or double-click

# Find the ELF directory (handles both running from dashboard-app/ or elsewhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Install from https://python.org"
    exit 1
fi

# Function to setup Python virtual environment for backend
setup_backend_venv() {
    local VENV_PATH="$BACKEND_PATH/venv"
    local REQUIREMENTS="$BACKEND_PATH/requirements.txt"

    # Check if venv exists
    if [ ! -d "$VENV_PATH" ]; then
        echo "[Setup] Creating Python virtual environment..."
        $PYTHON_CMD -m venv "$VENV_PATH"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to create virtual environment"
            echo "Try: sudo apt install python3-venv (Ubuntu/Debian)"
            return 1
        fi
    fi

    # Check if dependencies are installed (look for uvicorn)
    if ! "$VENV_PATH/bin/python" -c "import uvicorn" 2>/dev/null; then
        echo "[Setup] Installing backend dependencies..."
        "$VENV_PATH/bin/pip" install -q -r "$REQUIREMENTS"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install backend dependencies"
            return 1
        fi
    fi

    # Return the venv python path
    echo "$VENV_PATH/bin/python"
    return 0
}

BACKEND_PORT=8888
FRONTEND_PORT=3001
BACKEND_PATH="$SCRIPT_DIR/backend"
FRONTEND_PATH="$SCRIPT_DIR/frontend"

echo "========================================================"
echo "        EMERGENT LEARNING DASHBOARD WITH WATCHER        "
echo "        Agent Intelligence System + Monitoring          "
echo "========================================================"
echo ""

# Track if we started any servers
STARTED_SERVERS=false
WATCHER_PID=""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "========================================================"
    echo "Shutting down..."
    
    # Kill all background jobs
    if [ -n "$WATCHER_PID" ]; then
        echo "[Stopping] Watcher (PID $WATCHER_PID)..."
        kill $WATCHER_PID 2>/dev/null || true
    fi
    
    # Kill all remaining background jobs from this script
    kill 0 2>/dev/null || true
    
    echo "========================================================"
}

trap cleanup EXIT

# Check if backend already running
if curl -s "http://localhost:$BACKEND_PORT/api/stats" >/dev/null 2>&1; then
    echo "[OK] Backend already running on port $BACKEND_PORT"
else
    # Setup venv and get python path
    VENV_PYTHON=$(setup_backend_venv)
    if [ $? -ne 0 ]; then
        echo "Error: Backend setup failed"
        exit 1
    fi

    echo "[Starting] Backend API server..."
    cd "$BACKEND_PATH" && "$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
    STARTED_SERVERS=true

    # Wait for backend to be ready (polls until healthy, max 60s)
    echo -n "[Waiting] Backend initializing"
    for i in {1..60}; do
        if curl -s "http://localhost:$BACKEND_PORT/api/stats" >/dev/null 2>&1; then
            echo " ready!"
            break
        fi
        echo -n "."
        sleep 1
        if [ $i -eq 60 ]; then
            echo " timeout (continuing anyway)"
        fi
    done
fi

# Detect package manager
if command -v bun &> /dev/null; then
    PKG_MGR="bun"
elif command -v npm &> /dev/null; then
    PKG_MGR="npm"
else
    echo "Error: Neither bun nor npm found. Install from https://bun.sh or https://nodejs.org"
    exit 1
fi

# Check if frontend already running
if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
    echo "[OK] Frontend already running on port $FRONTEND_PORT"
else
    # Auto-install dependencies if node_modules missing
    if [ ! -d "$FRONTEND_PATH/node_modules" ]; then
        echo "[Installing] Frontend dependencies (node_modules not found)..."
        cd "$FRONTEND_PATH" && $PKG_MGR install
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install frontend dependencies"
            exit 1
        fi
    fi
    echo "[Starting] Frontend dev server (using $PKG_MGR)..."
    cd "$FRONTEND_PATH" && $PKG_MGR run dev &
    STARTED_SERVERS=true
    sleep 2
fi

# START WATCHER (NEW: Automated watcher startup)
echo ""
echo "[Starting] ELF Watcher (big-pickle 2-tier monitoring)..."
cd "$ELF_DIR" && ./scripts/start-watcher-bigpickle.sh --background &
WATCHER_PID=$!

if [ $? -eq 0 ]; then
    echo "[OK] Watcher started (PID $WATCHER_PID)"
    echo "[Monitoring] Watcher will automatically:"
    echo "   • Detect issues (Tier 1 with big-pickle)"
    echo "   • Make decisions (Tier 2 with big-pickle)"
    echo "   • Record events to event_chronicle"
    echo "   • Log to .coordination/watcher-log.md"
else
    echo "[Warning] Failed to start watcher - dashboard will continue"
fi

# Start TalkinHead overlay (cross-platform)
TALKINHEAD_PATH="$SCRIPT_DIR/TalkinHead"
TALKINHEAD_LOCK="$HOME/.elf-talkinhead.lock"

# Check if TalkinHead already running via lockfile
TALKINHEAD_RUNNING=false
if [ -f "$TALKINHEAD_LOCK" ]; then
    TALKINHEAD_PID=$(cat "$TALKINHEAD_LOCK" 2>/dev/null)
    if [ -n "$TALKINHEAD_PID" ]; then
        if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]] || [[ -n "$MSYSTEM" ]]; then
            # Windows: use tasklist
            if tasklist //FI "PID eq $TALKINHEAD_PID" 2>/dev/null | grep -q "$TALKINHEAD_PID"; then
                TALKINHEAD_RUNNING=true
            fi
        else
            # Linux/macOS: use kill -0
            if kill -0 "$TALKINHEAD_PID" 2>/dev/null; then
                TALKINHEAD_RUNNING=true
            fi
        fi
    fi
fi

if [ "$TALKINHEAD_RUNNING" = false ]; then
    if [ -f "$TALKINHEAD_PATH/main.py" ]; then
        echo "[Starting] TalkinHead overlay..."
        # Write dashboard PID file for orphan detection
        echo $$ > ~/.elf-dashboard.pid
        if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]] || [[ -n "$MSYSTEM" ]]; then
            # Windows: use pythonw for no console (check for PyQt5 first)
            if $PYTHON_CMD -c "import PyQt5" 2>/dev/null; then
                cd "$TALKINHEAD_PATH" && pythonw main.py &
            else
                echo "[Skip] TalkinHead (PyQt5 not installed - run: pip install PyQt5)"
            fi
        else
            # Linux/macOS: use venv launcher (handles numpy/Qt compatibility)
            if [ -f "$TALKINHEAD_PATH/run-talkinhead.sh" ]; then
                "$TALKINHEAD_PATH/run-talkinhead.sh" &
            else
                # Fallback to direct python if no launcher script
                cd "$TALKINHEAD_PATH" && $PYTHON_CMD main.py &
            fi
        fi
        STARTED_SERVERS=true
    fi
else
    echo "[OK] TalkinHead already running (PID $TALKINHEAD_PID)"
fi

# Open browser
echo "[Opening] Browser..."
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$FRONTEND_PORT"
elif command -v open >/dev/null 2>&1; then
    open "http://localhost:$FRONTEND_PORT"
else
    start "http://localhost:$FRONTEND_PORT" 2>/dev/null || echo "Open http://localhost:$FRONTEND_PORT in your browser"
fi

echo ""
echo "========================================================"
echo "  Dashboard is running with Watcher!"
echo ""
echo "  Frontend:      http://localhost:$FRONTEND_PORT"
echo "  Backend:       http://localhost:$BACKEND_PORT"
echo "  API Docs:      http://localhost:$BACKEND_PORT/docs"
echo "  Events API:    http://localhost:$BACKEND_PORT/api/chronicle/events"
echo ""
echo "  Watcher Status:"
echo "    PID:         $WATCHER_PID"
echo "    Mode:        Background (2-tier monitoring)"
echo "    Log file:    .coordination/watcher-log.md"
echo "    DB table:    memory/index.db (event_chronicle)"
echo ""
echo "  Monitor watcher:"
echo "    $ tail -f .coordination/watcher-log.md"
echo "    $ curl http://localhost:8888/api/chronicle/events"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "========================================================"
echo ""

# If both servers were already running, exit cleanly
if [ "$STARTED_SERVERS" = false ]; then
    exit 0
fi

# Keep script running to allow Ctrl+C to kill background jobs
wait
