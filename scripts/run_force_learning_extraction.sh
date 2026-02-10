#!/usr/bin/env bash
# run_force_learning_extraction.sh - Force a learning extraction cycle
# Called by watchdog when recent_learnings == 0

set -euo pipefail

# Use the internal API to enqueue a mission that triggers learning capture
AUTH="elan"
URL="http://localhost:9998/api/v1/mission"

payload=$(cat <<EOF
{
  "title": "Force Learning Extraction",
  "description": "Trigger immediate learning processor run to break recent_learnings == 0",
  "tags": ["force_extraction", "learning"]
}
EOF
)

curl -s -X POST "$URL" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $AUTH" \
     -d "$payload"

# Optionally wait briefly and check recent_learnings
sleep 5
curl -s "http://localhost:9998/api/v1/health" | grep -i recent_learnings || true