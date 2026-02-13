# Ask Orchestrator Endpoint

Submit a request to the orchestrator for coordination or decision-making.

## 🔧 Endpoint

```
POST /api/v1/ask
```

## 📥 Request Body

```json
{
  "component": "string",
  "request_type": "string",
  "data": {},
  "priority": 1
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component making the request |
| `request_type` | string | Yes | Type of request (decision, coordination, health_check, mission_submission, sentinel_coordination, pattern_coordination, sentinel_analysis) |
| `data` | object | Yes | Request data |
| `priority` | integer | No | Request priority (1-10, default: 1) |

## 📤 Response

### Success Response

```json
{
  "status": "success",
  "data": {
    "request_id": "string",
    "response_type": "string",
    "data": {},
    "timestamp": "2026-02-12T10:30:15Z",
    "confidence": 0.95
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid request parameters",
    "details": {}
  }
}
```

## 📝 Example Request

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

## 📝 Example Response

```json
{
  "status": "success",
  "data": {
    "request_id": "req_20260212_103015_123456",
    "response_type": "coordination_result",
    "data": {
      "agents": [
        {"name": "researcher", "type": "analysis", "status": "available"},
        {"name": "writer", "type": "content", "status": "busy"}
      ],
      "recommendation": "proceed",
      "confidence": 0.9
    },
    "timestamp": "2026-02-12T10:30:15Z",
    "confidence": 0.9
  }
}
```

## 🐍 Python Example

```python
import requests
import json

def ask_orchestrator(component, request_type, data, priority=1):
    url = "http://localhost:9998/api/v1/ask"
    
    payload = {
        "component": component,
        "request_type": request_type,
        "data": data,
        "priority": priority
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
result = ask_orchestrator(
    component="dashboard",
    request_type="coordination",
    data={"action": "list_agents"},
    priority=5
)

print(json.dumps(result, indent=2))
```

## 📄 JavaScript Example

```javascript
async function askOrchestrator(component, requestType, data, priority = 1) {
    const url = 'http://localhost:9998/api/v1/ask';
    
    const payload = {
        component: component,
        request_type: requestType,
        data: data,
        priority: priority
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error asking orchestrator:', error);
        throw error;
    }
}

// Example usage
askOrchestrator('dashboard', 'coordination', {action: 'list_agents'}, 5)
    .then(result => console.log(JSON.stringify(result, null, 2)))
    .catch(error => console.error('Error:', error));
```

## 📋 Request Types

| Type | Description | Typical Use Case |
|------|-------------|------------------|
| `decision` | General decision requests | Choosing between options |
| `coordination` | Component coordination | Synchronizing actions |
| `health_check` | Health status requests | Checking component status |
| `mission_submission` | Mission submission | Creating new tasks |
| `sentinel_coordination` | Sentinel coordination | Monitoring system |
| `pattern_coordination` | Pattern coordination | Analyzing trends |
| `sentinel_analysis` | Sentinel analysis | AI-powered analysis |

## ⚠️ Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Invalid request parameters |
| `INVALID_INPUT` | 400 | Malformed request body |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## 📚 Related Endpoints

- [Submit Mission](mission.md)
- [Get Component Health](health.md)
- [List Agents](agents.md)

## 📖 Further Reading

- [Orchestrator API Overview](README.md)
- [OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/requests.md)