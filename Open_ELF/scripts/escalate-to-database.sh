#!/bin/bash
################################################################################
# Escalate Critical System Failures to Database (ceo_reviews table)
# Makes escalations visible in dashboard CEO inbox
################################################################################

set -e

ELF_DIR="/home/bamer/.opencode/emergent-learning"
DB_PATH="$ELF_DIR/memory/index.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Escalate failures to database ceo_reviews table
escalate_to_database() {
    echo -e "${BLUE}🔍 Escalating critical failures to database CEO reviews${NC}"
    
    # Query database for critical failures and self-test failures (without timestamp filter)
    # Format: id|title|filepath|severity
    critical_failures=$(sqlite3 "$DB_PATH" "
        SELECT id, title, filepath, severity
        FROM learnings 
        WHERE type = 'failure' 
        AND (severity >= 3 OR title LIKE '%self-test%' OR title LIKE '%system issue%')
        ORDER BY severity DESC, id DESC
        LIMIT 15;
    ")
    
    if [ -z "$critical_failures" ]; then
        echo -e "${GREEN}✅ No critical failures to escalate to database${NC}"
        return 0
    fi
    
    # Counter for escalated failures
    escalated_count=0
    
    # Process each critical failure
    echo "$critical_failures" | while IFS='|' read -r id title filepath severity; do
        # Check if already escalated to database (by checking if a review with this learning ID exists)
        existing_review=$(sqlite3 "$DB_PATH" "
            SELECT COUNT(*) 
            FROM ceo_reviews 
            WHERE title LIKE '%$title%' AND context LIKE '%learning_id: $id%';
        ")
        
        if [ "$existing_review" -eq 0 ]; then
            echo -e "${YELLOW}⚡ Escalating critical failure #$id to database CEO reviews${NC}"
            
            # Insert into ceo_reviews table
            sqlite3 "$DB_PATH" "
                INSERT INTO ceo_reviews (
                    title, 
                    context, 
                    recommendation, 
                    status, 
                    created_at
                ) VALUES (
                    '🚨 Critical System Failure: $title',
                    'Learning ID: $id\nSeverity: $severity/5\nFile: $filepath\n\nThis failure was automatically detected and escalated by the Unified ELF Monitoring System.\n\nContext: System self-test has detected critical issues that require immediate attention.',
                    'Review this critical system failure and determine appropriate action. Consider running system diagnostics and checking logs for root cause.',
                    'pending',
                    datetime('now')
                );
            "
            
            escalated_count=$((escalated_count + 1))
            echo -e "${GREEN}✅ Escalated failure #$id to database CEO reviews${NC}"
        else
            echo -e "${BLUE}ℹ️  Failure #$id already escalated to database${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Escalation to database complete${NC}"
}

# Main execution
case "${1:-escalate}" in
    escalate)
        escalate_to_database
        ;;
    *)
        echo "Usage: $0 [escalate]"
        echo "  escalate    Escalate critical failures to database CEO reviews"
        ;;
esac