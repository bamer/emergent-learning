# cURL Orchestrator Examples

Command-line examples for interacting with the ELF Orchestrator API using cURL.

## 🚀 Quick Start

### Check Orchestrator Status
```bash
curl -X GET http://localhost:9998/status
```

### Submit a Mission
```bash
curl -X POST http://localhost:9998/api/v1/mission \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "mission": "Research the latest developments in artificial intelligence"
  }'
```

## 📋 Detailed Examples

### Ask Orchestrator for Coordination
```bash
curl -X POST http://localhost:9998/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "component": "dashboard",
    "request_type": "coordination",
    "data": {
      "action": "list_agents"
    },
    "priority": 5
  }'
```

### Get Mission Details
```bash
curl -X GET http://localhost:9998/api/v1/mission/mission_20260212_103015_12345
```

### Update Mission Status
```bash
curl -X POST http://localhost:9998/api/v1/mission/mission_20260212_103015_12345/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "progress": 25.0
  }'
```

### List Active Missions
```bash
curl -X GET http://localhost:9998/api/v1/missions
```

### Check Component Health
```bash
curl -X GET http://localhost:9998/api/v1/health/event_bridge
```

### List Available Agents
```bash
curl -X GET http://localhost:9998/api/v1/agents
```

### Run a Specific Agent
```bash
curl -X POST http://localhost:9998/api/v1/agents/researcher/run \
  -H "Content-Type: application/json" \
  -d '{
    "mission": "Analyze market trends for renewable energy"
  }'
```

## ⚠️ Error Handling Examples

### Handle HTTP Errors
```bash
# Check HTTP status code
response=$(curl -s -w "%{http_code}" -X GET http://localhost:9998/status)
status_code="${response: -3}"
body="${response%???}"

if [ "$status_code" -eq 200 ]; then
  echo "Success: $body"
elif [ "$status_code" -eq 404 ]; then
  echo "Not found"
elif [ "$status_code" -eq 500 ]; then
  echo "Server error"
else
  echo "Unexpected status: $status_code"
fi
```

### Parse JSON Error Responses
```bash
# Get error details from JSON response
response=$(curl -s -X GET http://localhost:9998/api/v1/mission/nonexistent)
error_code=$(echo "$response" | jq -r '.error.code')
error_message=$(echo "$response" | jq -r '.error.message')

if [ "$error_code" != "null" ]; then
  echo "Error ($error_code): $error_message"
fi
```

## 🛠️ Advanced Examples

### Batch Mission Submission
```bash
#!/bin/bash

# Submit multiple missions
missions=(
  '{"agent_type": "researcher", "mission": "Research AI ethics"}'
  '{"agent_type": "writer", "mission": "Write technical documentation"}'
  '{"agent_type": "analyst", "mission": "Analyze performance metrics"}'
)

for mission in "${missions[@]}"; do
  response=$(curl -s -X POST http://localhost:9998/api/v1/mission \
    -H "Content-Type: application/json" \
    -d "$mission")
  
  mission_id=$(echo "$response" | jq -r '.data.mission_id')
  echo "Submitted mission: $mission_id"
done
```

### Monitor Mission Progress
```bash
#!/bin/bash

MISSION_ID="mission_20260212_103015_12345"

while true; do
  response=$(curl -s -X GET http://localhost:9998/api/v1/mission/$MISSION_ID)
  status=$(echo "$response" | jq -r '.data.status')
  progress=$(echo "$response" | jq -r '.data.progress')
  
  echo "Mission $MISSION_ID: $status ($progress%)"
  
  if [[ "$status" == "completed" || "$status" == "failed" ]]; then
    break
  fi
  
  sleep 10
done
```

### Health Check with Alerting
```bash
#!/bin/bash

COMPONENT="event_bridge"
response=$(curl -s -X GET http://localhost:9998/api/v1/health/$COMPONENT)
health_status=$(echo "$response" | jq -r '.data.status')

if [ "$health_status" != "healthy" ]; then
  echo "ALERT: $COMPONENT is $health_status" | mail -s "ELF Component Alert" admin@example.com
  echo "Alert sent for $COMPONENT health issue"
else
  echo "$COMPONENT is healthy"
fi
```

## 📦 Utility Scripts

### Format JSON Output
```bash
# Pretty print JSON responses
curl -X GET http://localhost:9998/status | jq '.'
```

### Extract Specific Fields
```bash
# Get just the events processed count
curl -s -X GET http://localhost:9998/status | jq '.data.events_processed'
```

### Save Response to File
```bash
# Save response for later analysis
curl -X GET http://localhost:9998/api/v1/missions \
  -H "Content-Type: application/json" \
  -o missions.json
```

## 🛡️ Security Examples

### Using API Keys (Future Feature)
```bash
# Example of API key usage (when implemented)
curl -X GET http://localhost:9998/status \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

### Using Authentication Tokens (Future Feature)
```bash
# Example of token-based authentication (when implemented)
curl -X GET http://localhost:9998/status \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

## 📚 Related Examples

- [EventBridge cURL Examples](eventbridge-examples.md)
- [Python Orchestrator Examples](../python/orchestrator-client.md)
- [JavaScript Orchestrator Examples](../javascript/orchestrator-client.md)

## 📖 Further Reading

- [Orchestrator API Documentation](../../endpoints/orchestrator/)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/)