# Monitoring API Endpoints

The Monitoring API provides real-time monitoring for the ELF architecture, including EventBridge, LearningProcessor, and agent hierarchy status.

## 📋 Endpoint Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| [`GET /`](summary.md) | GET | Get quick monitoring summary |
| [`GET /stats`](statistics.md) | GET | Get detailed system statistics |
| [`GET /health`](health.md) | GET | Get overall system health |
| [`GET /api/v1/summary`](summary.md) | GET | Get API summary |
| [`GET /api/v1/architecture`](architecture.md) | GET | Get architecture information |
| [`GET /api/v1/learning`](learning.md) | GET | Get learning statistics |
| [`GET /api/v1/events`](events.md) | GET | Get event statistics |

## 🔧 Base URL

```
http://localhost:9997
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

- [Monitoring OpenAPI Specification](../../openapi/monitoring.yaml)
- [Schema Definitions](../../schemas/)
- [Code Examples](../../examples/)
- [Monitoring API Implementation](../../../core/monitoring_api.py)