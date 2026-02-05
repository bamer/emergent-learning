#!/bin/bash
################################################################################
# Escalate Critical System Failures to CEO Inbox
# Part of Unified ELF Monitoring System
################################################################################

set -e

ELF_DIR="/home/bamer/.opencode/emergent-learning"
DB_PATH="$ELF_DIR/memory/index.db"
INBOX_DIR="$ELF_DIR/ceo-inbox"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check for critical failures in the last hour that haven't been escalated
check_and_escalate() {
    echo -e "${BLUE}🔍 Checking for critical failures to escalate to CEO${NC}"
    
    # Query database for critical failures and self-test failures (without timestamp filter for now)
    critical_failures=$(sqlite3 "$DB_PATH" "
        SELECT id, title, filepath, COALESCE(created_at, 'Unknown') as created_at, severity
        FROM learnings 
        WHERE type = 'failure' 
        AND (severity >= 3 OR title LIKE '%self-test%' OR title LIKE '%system issue%')
        ORDER BY severity DESC, id DESC
        LIMIT 15;
    ")
    
    if [ -z "$critical_failures" ]; then
        echo -e "${GREEN}✅ No critical failures to escalate${NC}"
        return 0
    fi
    
    # Process each critical failure
    echo "$critical_failures" | while IFS='|' read -r id title filepath created_at severity; do
        # Check if already escalated (by checking if a file with this ID exists in inbox)
        if [ ! -f "$INBOX_DIR/escalation_$id.md" ]; then
            echo -e "${YELLOW}⚡ Escalating critical failure #$id to CEO${NC}"
            
            # Create escalation file
            cat > "$INBOX_DIR/escalation_$id.md" << EOF
# 🚨 CRITICAL SYSTEM FAILURE ESCALATION

## Issue Details
- **Title**: $title
- **ID**: $id
- **Severity**: $severity/5
- **Occurred**: $created_at
- **File**: $filepath

## Urgency Level
CRITICAL - Requires immediate attention

## Action Required
Please review this system failure and determine appropriate action.

## Escalated By
Unified ELF Monitoring System
$(date)

---
*This failure was automatically escalated due to high severity level.*
EOF
            
            echo -e "${GREEN}✅ Escalated failure #$id to CEO inbox${NC}"
        else
            echo -e "${BLUE}ℹ️  Failure #$id already escalated${NC}"
        fi
    done
}

# Main execution
case "${1:-check}" in
    check)
        check_and_escalate
        ;;
    *)
        echo "Usage: $0 [check]"
        echo "  check    Check for and escalate critical failures"
        ;;
esac