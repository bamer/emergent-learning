#!/bin/bash
# Simple OpenCode Terminal Launcher for GNOME
# Uses gnome-terminal to open OpenCode in a new window

echo "🚀 Launching OpenCode in new terminal window..."

# Check if gnome-terminal is available
if command -v gnome-terminal >/dev/null 2>&1; then
    echo "🖥  Using gnome-terminal..."
    gnome-terminal --title="OpenCode Server" --geometry=100x30 -- bash -c '
        echo "🌐 OpenCode Server Starting..."
        echo "📍 Port: 4096"
        echo "🔗 URL: http://localhost:4096"
        echo ""
        echo "⏹️  Press Ctrl+C to stop the server"
        echo ""
        opencode serve --port 4096
        echo ""
        echo "✅ OpenCode Server Stopped"
        read
    '
elif command -v tmux >/dev/null 2>&1; then
    echo "🖥  Using tmux..."
    tmux new-session -d -s opencode "opencode serve --port 4096"
    echo "✅ Started in tmux session 'opencode'"
    echo "   Attach with: tmux attach -t opencode"
else
    echo "🖥  No suitable terminal found, starting in background..."
    opencode serve --port 4096 &
fi

# Wait a moment for terminal to appear
sleep 2

echo ""
echo "📋 OpenCode Information:"
echo "   🌐 Server URL: http://localhost:4096"
echo "   📊 Health Check: http://localhost:4096/global/health"
echo "   🤖 Agents: http://localhost:4096/agents"
echo ""