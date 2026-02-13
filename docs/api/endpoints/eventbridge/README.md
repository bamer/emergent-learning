# EventBridge API Endpoints

The EventBridge is the central event processing system for the Emergent Learning Framework (ELF). It connects the OpenCode agent execution environment with the ELF learning and monitoring systems.

## 📋 Endpoint Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| [`GET /status`](status.md) | GET | Get EventBridge system status |
| [`GET /api/v1/health`](health.md) | GET | Get overall system health |
| [`GET /api/v1/health/{component}`](health.md) | GET | Get specific component health |

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

- [EventBridge OpenAPI Specification](../../openapi/eventbridge.yaml)
- [Schema Definitions](../../schemas/)
- [Code Examples](../../examples/)
- [EventBridge Architecture](../../../ARCHITECTURE-EventBridge.md)