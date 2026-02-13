# ELF API Documentation

Welcome to the Emergent Learning Framework (ELF) API documentation. This comprehensive guide provides everything you need to integrate with and utilize the ELF system.

## 🚀 Quick Start (5 Minutes to First API Call)

### Prerequisites
- ELF system running locally
- OpenCode server running on port 4096
- EventBridge running on port 9998

### Making Your First API Call

```bash
# Check if EventBridge is running
curl http://localhost:9998/status

# Expected response:
# {
#   "running": true,
#   "events_processed": 1247,
#   "opencode_server": "http://localhost:4096",
#   "started_at": "2026-02-12T10:30:15",
#   "uptime_seconds": 3600,
#   "last_event_time": "2026-02-12T11:30:15"
# }
```

## 🏗️ System Overview

The ELF system consists of several interconnected components:

1. **EventBridge** (Port 9998) - Central event processing system
2. **UnifiedOrchestrator** - Service management and coordination
3. **Dashboard** (Port 8888) - Web interface for monitoring and control
4. **LearningProcessor** - AI learning and heuristic generation

## 🔌 Base URLs

- **EventBridge API**: `http://localhost:9998`
- **Dashboard API**: `http://localhost:8888/api/v1`
- **Monitoring API**: `http://localhost:9997`

## 🔐 Authentication

Most ELF APIs do not require authentication as they are designed for local system use. However, external integrations should implement appropriate security measures.

## 📦 Response Format

All API responses follow a consistent JSON format:

```json
{
  "status": "success|error",
  "data": {},
  "message": "Description of the response"
}
```

## ⚠️ Error Handling

Errors follow standard HTTP status codes with detailed error messages:

```json
{
  "status": "error",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {}
  }
}
```

## 📚 Documentation Sections

- [API Overview](overview.md) - Detailed architecture and design principles
- [Authentication](authentication.md) - Security and authentication mechanisms
- [Error Handling](error-handling.md) - Standard error response formats
- [Rate Limiting](rate-limiting.md) - API usage limits and policies
- [Changelog](changelog.md) - API version history and changes
- [OpenAPI Specifications](openapi/) - Complete API specifications
- [Endpoints](endpoints/) - Detailed endpoint documentation
- [Schemas](schemas/) - Request/response data schemas
- [Examples](examples/) - Code examples in multiple languages

## 🛠️ SDKs and Libraries

Currently available SDKs:
- Python client library (included in ELF)
- JavaScript/TypeScript client library (coming soon)

## 🤝 Getting Help

For support, please check:
- [GitHub Issues](https://github.com/elf-framework/issues)
- [Community Forum](https://community.elf-framework.com)
- Contact: support@elf-framework.com