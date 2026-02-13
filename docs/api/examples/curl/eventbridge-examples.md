# cURL EventBridge Examples

Command-line examples for interacting with the ELF EventBridge API using cURL.

## 🚀 Quick Start

### Check EventBridge Status
```bash
curl -X GET http://localhost:9998/status
```

### Check System Health
```bash
curl -X GET http://localhost:9998/api/v1/health
```

### Check Component Health
```bash
curl -X GET http://localhost:9998/api/v1/health/event_bridge
```

## 📋 Detailed Examples

### Get Detailed Status Information
```bash
curl -X GET http://localhost:9998/status | jq '.'
```

### Check Mission Bridge Health
```bash
curl -X GET http://localhost:9998/api/v1/health/mission_bridge
```

### Check Sentinel Monitor Health
```bash
curl -X GET http://localhost:9998/api/v1/health/sentinel_monitor
```

### Get Health with Specific Component
```bash
curl -X GET http://localhost:9998/api/v1/health/event_bridge | jq '.data.details'
```

## ⚠️ Error Handling Examples

### Handle Connection Errors
```bash
#!/bin/bash

# Check if EventBridge is reachable
if curl -s --connect-timeout 5 http://localhost:9998/status > /dev/null; then
  echo "EventBridge is reachable"
  response=$(curl -s -X GET http://localhost:9998/status)
  echo "Status: $(echo "$response" | jq -r '.data.running')"
else
  echo "ERROR: Cannot connect to EventBridge"
  exit 1
fi
```

### Parse Different Response Types
```bash
#!/bin/bash

# Handle both success and error responses
response=$(curl -s -X GET http://localhost:9998/status)
status=$(echo "$response" | jq -r '.status')

if [ "$status" == "success" ]; then
  running=$(echo "$response" | jq -r '.data.running')
  events=$(echo "$response" | jq -r '.data.events_processed')
  echo "EventBridge running: $running"
  echo "Events processed: $events"
elif [ "$status" == "error" ]; then
  error_code=$(echo "$response" | jq -r '.error.code')
  error_message=$(echo "$response" | jq -r '.error.message')
  echo "ERROR ($error_code): $error_message"
else
  echo "Unexpected response format"
fi
```

## 🛠️ Advanced Examples

### Monitor EventBridge Continuously
```bash
#!/bin/bash

echo "Monitoring EventBridge status (Ctrl+C to stop)..."
echo "----------------------------------------"

while true; do
  response=$(curl -s --max-time 10 http://localhost:9998/status)
  
  if [ $? -eq 0 ]; then
    running=$(echo "$response" | jq -r '.data.running')
    events=$(echo "$response" | jq -r '.data.events_processed')
    uptime=$(echo "$response" | jq -r '.data.uptime_seconds')
    
    if [ "$running" == "true" ]; then
      echo "[$(date)] 🟢 Running | Events: $events | Uptime: ${uptime}s"
    else
      echo "[$(date)] 🔴 Stopped | Events: $events"
    fi
  else
    echo "[$(date)] ❌ Connection failed"
  fi
  
  sleep 30
done
```

### Check Health of All Components
```bash
#!/bin/bash

components=("event_bridge" "mission_bridge" "sentinel_monitor")

echo "Component Health Check"
echo "======================"

for component in "${components[@]}"; do
  response=$(curl -s --max-time 5 http://localhost:9998/api/v1/health/$component)
  status=$(echo "$response" | jq -r '.status')
  
  if [ "$status" == "success" ]; then
    health=$(echo "$response" | jq -r '.data.status')
    case "$health" in
      "healthy")
        icon="🟢"
        ;;
      "degraded")
        icon="🟡"
        ;;
      "unhealthy")
        icon="🔴"
        ;;
      *)
        icon="❓"
        ;;
    esac
    echo "$icon $component: $health"
  else
    echo "❌ $component: ERROR"
  fi
done
```

### Event Processing Rate Analysis
```bash
#!/bin/bash

# Measure events per minute over a period
echo "Measuring EventBridge processing rate..."

# Take initial measurement
initial_response=$(curl -s http://localhost:9998/status)
initial_events=$(echo "$initial_response" | jq -r '.data.events_processed')

# Wait for 60 seconds
sleep 60

# Take final measurement
final_response=$(curl -s http://localhost:9998/status)
final_events=$(echo "$final_response" | jq -r '.data.events_processed')

# Calculate rate
events_processed=$((final_events - initial_events))
events_per_minute=$events_processed

echo "Events processed in 60 seconds: $events_processed"
echo "Events per minute: $events_per_minute"

# Provide analysis
if [ $events_per_minute -gt 1000 ]; then
  echo "⚠️  High event processing rate - potential overload"
elif [ $events_per_minute -lt 1 ]; then
  echo "⚠️  Low event processing rate - possible issues"
else
  echo "✅ Normal event processing rate"
fi
```

### Automated Health Reporting
```bash
#!/bin/bash

# Generate a health report
REPORT_FILE="eventbridge_health_report_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "EventBridge Health Report"
  echo "Generated: $(date)"
  echo "================================"
  
  # Overall status
  status_response=$(curl -s http://localhost:9998/status)
  if [ "$(echo "$status_response" | jq -r '.status')" == "success" ]; then
    running=$(echo "$status_response" | jq -r '.data.running')
    events=$(echo "$status_response" | jq -r '.data.events_processed')
    uptime=$(echo "$status_response" | jq -r '.data.uptime_seconds')
    
    echo "Status: $([ "$running" == "true" ] && echo "Running" || echo "Stopped")"
    echo "Events Processed: $events"
    echo "Uptime: $uptime seconds"
  else
    echo "Status: Unable to retrieve"
  fi
  
  echo ""
  echo "Component Health:"
  echo "-----------------"
  
  # Component health
  components=("event_bridge" "mission_bridge" "sentinel_monitor")
  for component in "${components[@]}"; do
    health_response=$(curl -s http://localhost:9998/api/v1/health/$component)
    if [ "$(echo "$health_response" | jq -r '.status')" == "success" ]; then
      health=$(echo "$health_response" | jq -r '.data.status')
      echo "$component: $health"
    else
      echo "$component: ERROR"
    fi
  done
  
} > "$REPORT_FILE"

echo "Health report saved to $REPORT_FILE"
```

## 📦 Utility Examples

### Format and Save Status Information
```bash
# Save formatted status to file
curl -s http://localhost:9998/status | jq '.' > eventbridge_status.json
```

### Extract Specific Metrics
```bash
# Get just the number of events processed
curl -s http://localhost:9998/status | jq '.data.events_processed'

# Get uptime in human-readable format
curl -s http://localhost:9998/status | jq '.data.uptime_seconds'
```

### Compare Status Over Time
```bash
#!/bin/bash

# Compare status at two different times
echo "Taking initial status snapshot..."
initial_status=$(curl -s http://localhost:9998/status)
echo "$initial_status" > initial_status.json

echo "Waiting 5 minutes..."
sleep 300

echo "Taking final status snapshot..."
final_status=$(curl -s http://localhost:9998/status)
echo "$final_status" > final_status.json

echo "Comparing snapshots..."
initial_events=$(echo "$initial_status" | jq '.data.events_processed')
final_events=$(echo "$final_status" | jq '.data.events_processed')
events_diff=$((final_events - initial_events))

echo "Events processed in 5 minutes: $events_diff"
```

## 🛡️ Security Examples

### Using Headers for Future Authentication
```bash
# Example with custom headers (for future authentication)
curl -X GET http://localhost:9998/status \
  -H "User-Agent: ELF-Monitor/1.0" \
  -H "Accept: application/json"
```

### Rate Limit Testing
```bash
#!/bin/bash

# Test rate limiting by making rapid requests
echo "Testing rate limits..."

for i in {1..20}; do
  response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9998/status)
  echo "Request $i: HTTP $response_code"
  
  if [ "$response_code" -eq 429 ]; then
    echo "Rate limit hit at request $i"
    break
  fi
  
  sleep 0.1
done
```

## 📚 Related Examples

- [Orchestrator cURL Examples](orchestrator-examples.md)
- [Python EventBridge Examples](../python/eventbridge-client.md)
- [JavaScript EventBridge Examples](../javascript/eventbridge-client.md)

## 📖 Further Reading

- [EventBridge API Documentation](../../endpoints/eventbridge/)
- [OpenAPI Specification](../../openapi/eventbridge.yaml)
- [Schema Definitions](../../schemas/)