#!/bin/bash
# Experiment Monitor - Tracks and manages active experiments
#
# Usage:
#   ./scripts/experiment-monitor.sh              # Show status
#   ./scripts/experiment-monitor.sh --mark-old   # Mark stale as pending review
#   ./scripts/experiment-monitor.sh --archive    # Archive old completed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF_DIR="$(dirname "$SCRIPT_DIR")"
MANAGER="$SCRIPT_DIR/lib/experiment_manager.py"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
echo_ok() { echo -e "${GREEN}[✓]${NC} $*"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
echo_err() { echo -e "${RED}[ERROR]${NC} $*"; }

# Show status
show_status() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "              EXPERIMENT MONITOR STATUS"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # Stats
    stats=$(python3 "$MANAGER" stats)
    
    echo "📊 Statistics:"
    echo "$stats" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Timestamp: {data['timestamp']}\")
print()
print(f\"  By Status:\")
for status, info in data['by_status'].items():
    print(f\"    {status.upper():12} : {info['count']:3} experiments (avg {info['avg_cycles']:.1f} cycles)\")
print()
if data['oldest_active']:
    oa = data['oldest_active']
    print(f\"  Oldest Active: \\\"{oa['name']}\\\" (ID: {oa['id']}, {oa['days_running']} days)\")
print()
print(f\"  Total Completed: {data['total_completed']}\")
print(f\"  Total Cycles Run: {data['total_cycles']}\")
"
    
    # Active experiments
    echo ""
    echo "📋 Active Experiments:"
    active=$(python3 "$MANAGER" list active)
    echo "$active" | python3 -c "
import sys, json
from datetime import datetime
data = json.load(sys.stdin)
if not data:
    print('  (none)')
else:
    for exp in data:
        created = datetime.fromisoformat(exp['created_at'])
        days = (datetime.now() - created).days
        print(f\"  ID {exp['id']:3} | {days:3} days | {exp['name'][:40]}\")
        print(f\"           Cycles: {exp.get('cycles_run', 0)}, Status: {exp['status']}\")
"
    
    # Stale experiments (30+ days without update)
    echo ""
    echo "⏱️  Stale Experiments (>30 days inactive):"
    stale=$(python3 "$MANAGER" stale 30)
    echo "$stale" | python3 -c "
import sys, json
from datetime import datetime
data = json.load(sys.stdin)
if not data:
    print('  (none)')
else:
    for exp in data:
        created = datetime.fromisoformat(exp['created_at'])
        days = (datetime.now() - created).days
        print(f\"  ID {exp['id']:3} | {days:3} days | {exp['name'][:40]}\")
"
    
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# Mark stale experiments for review
mark_old_for_review() {
    echo_info "Checking for stale experiments..."
    
    stale=$(python3 "$MANAGER" stale 30)
    count=$(echo "$stale" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    
    if [ "$count" -eq 0 ]; then
        echo_ok "No stale experiments found"
        return 0
    fi
    
    echo_warn "Found $count stale experiment(s):"
    echo "$stale" | python3 -c "
import sys, json
from datetime import datetime
data = json.load(sys.stdin)
for exp in data:
    created = datetime.fromisoformat(exp['created_at'])
    days = (datetime.now() - created).days
    print(f\"  - Exp {exp['id']}: '{exp['name']}' ({days} days, {exp.get('cycles_run', 0)} cycles)\")
"
    
    echo ""
    echo "Options:"
    echo "  1. Mark as 'pending review'"
    echo "  2. Mark as 'on hold'"
    echo "  3. Skip"
    read -p "Choose action (default: skip): " action
    action="${action:-3}"
    
    case "$action" in
        1|2)
            status="pending_review"
            echo_info "Would mark as pending review (implement manual update)"
            ;;
        *)
            echo_ok "Skipped"
            ;;
    esac
}

# Archive old completed experiments
archive_old() {
    days="${1:-90}"
    echo_info "Archiving experiments completed >$days days ago..."
    
    python3 "$MANAGER" archive-old "$days"
    echo_ok "Done"
}

# Main
command="${1:-status}"

case "$command" in
    status|--status)
        show_status
        ;;
    mark-old|--mark-old)
        mark_old_for_review
        ;;
    archive|--archive)
        archive_old "${2:-90}"
        ;;
    *)
        echo_err "Unknown command: $command"
        echo "Usage: $0 [status|mark-old|archive [days]]"
        exit 1
        ;;
esac
