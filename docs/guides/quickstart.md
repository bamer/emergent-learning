# ELF API Quick Start Guide

Get up and running with the ELF API in 5 minutes or less.

## 🚀 Prerequisites

Before you begin, ensure you have:

1. **ELF System Installed**
   - Clone the ELF repository
   - Install dependencies
   - Configure environment

2. **Services Running**
   - EventBridge on port 9998
   - OpenCode server on port 4096
   - Dashboard on port 8888 (optional)
   - Monitoring on port 9997 (optional)

3. **Basic Tools**
   - cURL or Postman for API testing
   - Python 3.8+ (for Python examples)
   - Node.js 14+ (for JavaScript examples)

## 🎯 Step 1: Verify System Status

First, check if the EventBridge is running:

```bash
# Check EventBridge status
curl -X GET http://localhost:9998/status
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "running": true,
    "events_processed": 1247,
    "opencode_server": "http://localhost:4096",
    "started_at": "2026-02-12T10:30:15",
    "uptime_seconds": 3600,
    "last_event_time": "2026-02-12T11:30:15"
  }
}
```

## 🎯 Step 2: Check System Health

Verify that all components are healthy:

```bash
# Check overall system health
curl -X GET http://localhost:9998/api/v1/health
```

Check individual components:
```bash
# Check EventBridge health
curl -X GET http://localhost:9998/api/v1/health/event_bridge

# Check Mission Bridge health
curl -X GET http://localhost:9998/api/v1/health/mission_bridge
```

## 🎯 Step 3: List Available Agents

See what agents are available in the system:

```bash
# List agents via orchestrator
curl -X GET http://localhost:9998/api/v1/agents
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "name": "researcher",
        "type": "analysis",
        "status": "available",
        "last_seen": "2026-02-12T10:30:15Z"
      },
      {
        "name": "writer",
        "type": "content",
        "status": "busy",
        "last_seen": "2026-02-12T10:25:30Z"
      }
    ],
    "status": "success"
  }
}
```

## 🎯 Step 4: Submit Your First Mission

Create and submit a mission for an agent to execute:

```bash
# Submit a mission to the researcher agent
curl -X POST http://localhost:9998/api/v1/mission \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "researcher",
    "mission": "Research the latest developments in artificial intelligence"
  }'
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_103015_12345",
    "status": "submitted",
    "estimated_time": 300,
    "priority": 3,
    "confidence": 0.95
  }
}
```

## 🎯 Step 5: Monitor Mission Progress

Check the status of your mission:

```bash
# Get mission details
curl -X GET http://localhost:9998/api/v1/mission/mission_20260212_103015_12345
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "mission_id": "mission_20260212_103015_12345",
    "agent_type": "researcher",
    "mission": "Research the latest developments in artificial intelligence",
    "status": "running",
    "created_at": "2026-02-12T10:30:15Z",
    "updated_at": "2026-02-12T10:32:45Z",
    "progress": 25.0
  }
}
```

## 🎯 Step 6: List Active Missions

See all active missions in the system:

```bash
# List all active missions
curl -X GET http://localhost:9998/api/v1/missions
```

## 🎯 Step 7: Run an Agent Directly

Execute an agent with a specific mission:

```bash
# Run the analyst agent directly
curl -X POST http://localhost:9998/api/v1/agents/analyst/run \
  -H "Content-Type: application/json" \
  -d '{
    "mission": "Analyze performance metrics from the last 24 hours"
  }'
```

## 🎯 Step 8: Advanced Interaction

Ask the orchestrator for coordination:

```bash
# Ask orchestrator for coordination
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

## 🐍 Python Quick Start

Using Python with the requests library:

```python
import requests

# Check EventBridge status
response = requests.get("http://localhost:9998/status")
print(response.json())

# Submit a mission
mission_data = {
    "agent_type": "researcher",
    "mission": "Research AI developments"
}
response = requests.post(
    "http://localhost:9998/api/v1/mission",
    json=mission_data
)
print(response.json())
```

## 📄 JavaScript Quick Start

Using JavaScript with the fetch API:

```javascript
// Check EventBridge status
fetch('http://localhost:9998/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Submit a mission
const missionData = {
  agent_type: "researcher",
  mission: "Research AI developments"
};

fetch('http://localhost:9998/api/v1/mission', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(missionData)
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   curl: (7) Failed to connect to localhost port 9998: Connection refused
   ```
   **Solution**: Ensure EventBridge is running on port 9998

2. **Service Unavailable**
   ```json
   {
     "status": "error",
     "error": {
       "code": "SERVICE_UNAVAILABLE",
       "message": "EventBridge service is currently unavailable"
     }
   }
   ```
   **Solution**: Check if EventBridge process is running

3. **Component Not Found**
   ```json
   {
     "status": "error",
     "error": {
       "code": "RESOURCE_NOT_FOUND",
       "message": "Component 'unknown_component' not found"
     }
   }
   ```
   **Solution**: Check component name spelling and availability

### Service Status Commands

```bash
# Check if services are running
ps aux | grep event_bridge
ps aux | grep unified_orchestrator
ps aux | grep dashboard

# Check port availability
lsof -i :9998
lsof -i :8888
lsof -i :9997
```

## 📚 Next Steps

After completing this quick start guide, explore:

1. **[Orchestrator API Documentation](../api/endpoints/orchestrator/)**
2. **[EventBridge API Documentation](../api/endpoints/eventbridge/)**
3. **[Monitoring API Documentation](../api/endpoints/monitoring/)**
4. **[Code Examples](../api/examples/)**
5. **[Schema Documentation](../api/schemas/)**

## 📖 Further Reading

- [API Overview](../api/overview.md)
- [Authentication Guide](../api/authentication.md)
- [Error Handling](../api/error-handling.md)
- [Rate Limiting](../api/rate-limiting.md)