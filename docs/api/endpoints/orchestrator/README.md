# Orchestrator API Endpoints

The Unified Orchestrator manages system services and processes events. It connects to the EventBridge and provides coordination capabilities for the entire ELF system.

## 📋 Endpoint Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| [`POST /api/v1/ask`](ask.md) | POST | Ask orchestrator for a decision or coordination |
| [`POST /api/v1/mission`](mission.md) | POST | Submit a new mission for execution |
| [`GET /api/v1/mission/{id}`](mission.md) | GET | Get details for a specific mission |
| [`POST /api/v1/mission/{id}/status`](mission.md) | POST | Update mission status |
| [`GET /api/v1/missions`](missions.md) | GET | List active missions |
| [`GET /api/v1/health/{component}`](health.md) | GET | Get health status for a component |
| [`GET /api/v1/agents`](agents.md) | GET | List available agents |
| [`POST /api/v1/agents/{type}/run`](agents.md) | POST | Run a specific agent |

## 🔧 Base URL

```
http://localhost:9998
```

## 🔐 Authentication

Currently, no authentication is required for local development. For production deployments, API keys will be supported in future versions.

## 📦 Request/Response Format

All requests and responses use JSON format with UTF-8 encoding.

### Request Headers
```
Content-Type: application/json
Accept: application/json
```

### Response Format
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional descriptive message"
}
```

## ⚠️ Error Handling

All errors follow standardized format:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {}
  }
}
```

See [Error Handling](../../error-handling.md) for detailed information.

## 📚 Related Documentation

- [Orchestrator OpenAPI Specification](../../openapi/orchestrator.yaml)
- [Schema Definitions](../../schemas/)
- [Code Examples](../../examples/)