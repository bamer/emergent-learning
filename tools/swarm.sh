#!/bin/bash
#
# Swarm Task Wrapper - Easy CLI interface for swarm coordination
# 
# Usage:
#   ./swarm.sh ultrathink <target> [context]
#   ./swarm.sh focused <target> [context] 
#   ./swarm.sh quick <target> [context]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWARM_COORDINATOR="${SCRIPT_DIR}/swarm_coordinator.py"

# Check prerequisites
if [ ! -f "$SWARM_COORDINATOR" ]; then
    echo "❌ Swarm coordinator not found: $SWARM_COORDINATOR"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Parse arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <mode> <target> [context]"
    echo "  mode: ultrathink|focused|quick"
    echo "  target: file or directory to analyze"
    echo "  context: optional context description"
    exit 1
fi

MODE="$1"
TARGET="$2"
CONTEXT="${3:-}"

# Validate mode
case "$MODE" in
    ultrathink|focused|quick)
        echo "🚀 SWARM TASK - $MODE mode"
        ;;
    *)
        echo "❌ Invalid mode: $MODE"
        echo "   Use: ultrathink, focused, quick"
        exit 1
        ;;
esac

# Check target exists
if [ ! -e "$TARGET" ]; then
    echo "❌ Target not found: $TARGET"
    exit 1
fi

# Execute swarm coordinator
echo "Target: $TARGET"
if [ -n "$CONTEXT" ]; then
    echo "Context: $CONTEXT"
fi
echo ""

python3 "$SWARM_COORDINATOR" "$TARGET" --mode "$MODE" --context "$CONTEXT"
