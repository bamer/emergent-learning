# Common Object Schemas

Reusable data structures used across multiple ELF API endpoints.

## 📦 Base Response Objects

### Success Response
Standard format for successful API responses.

```json
{
  "status": "success",
  "data": {},
  "message": "Optional descriptive message"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Always "success" for successful responses |
| `data` | object | Yes | Response data payload |
| `message` | string | No | Optional human-readable message |

### Error Response
Standard format for API error responses.

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

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Always "error" for error responses |
| `error` | object | Yes | Error details object |
| `error.code` | string | Yes | Machine-readable error code |
| `error.message` | string | Yes | Human-readable error description |
| `error.details` | object | No | Additional error context |

## 🏥 Health Check Objects

### Component Health
Health status for individual system components.

```json
{
  "component": "event_bridge",
  "status": "healthy",
  "details": {},
  "confidence": 0.95,
  "recommendation": "continue"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component name |
| `status` | string | Yes | Health status (healthy, degraded, unhealthy) |
| `details` | object | No | Additional health details |
| `confidence` | number | No | Confidence level (0.0-1.0) |
| `recommendation` | string | No | Recommended action |

### System Health
Overall system health status.

```json
{
  "status": "healthy",
  "components": {
    "event_bridge": "healthy",
    "learning_processor": "healthy"
  },
  "timestamp": "2026-02-12T10:30:15Z"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Overall system health |
| `components` | object | Yes | Component health map |
| `timestamp` | string | Yes | Health check timestamp (ISO 8601) |

## 🎯 Status Objects

### Mission Status
Current status of a mission.

```json
{
  "mission_id": "mission_20260212_103015_12345",
  "status": "running",
  "estimated_time": 300,
  "priority": 3,
  "confidence": 0.95
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mission_id` | string | Yes | Unique mission identifier |
| `status` | string | Yes | Current mission status |
| `estimated_time` | integer | No | Estimated completion time (seconds) |
| `priority` | integer | No | Mission priority (1-10) |
| `confidence` | number | No | Confidence level (0.0-1.0) |

## 🕒 Timestamp Objects

### ISO 8601 Timestamp
Standard timestamp format used throughout the API.

**Format:** `YYYY-MM-DDTHH:MM:SSZ`

**Examples:**
- `2026-02-12T10:30:15Z`
- `2026-02-12T10:30:15.123Z`

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string | Yes | ISO 8601 formatted timestamp |

## 📊 Statistics Objects

### Event Statistics
Event processing metrics.

```json
{
  "per_minute": 15.5,
  "recent": [
    {
      "event_type": "tool",
      "count": 234,
      "last_seen": "2026-02-12T10:30:15Z"
    }
  ]
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `per_minute` | number | No | Events processed per minute |
| `recent` | array | No | Recent event statistics |

### Learning Statistics
Machine learning metrics.

```json
{
  "heuristics": 247,
  "golden_rules": 12,
  "trails": 1542,
  "pheromone_trails": 89,
  "learnings": 67
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `heuristics` | integer | No | Number of heuristics |
| `golden_rules` | integer | No | Number of golden rules |
| `trails` | integer | No | Number of trails |
| `pheromone_trails` | integer | No | Number of pheromone trails |
| `learnings` | integer | No | Number of learnings |

## 🛠️ Utility Objects

### Database Info
Database connection and size information.

```json
{
  "path": "/home/bamer/.opencode/emergent-learning/memory/index.db",
  "size_kb": 2560
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Database file path |
| `size_kb` | integer | Yes | Database size in kilobytes |

### Architecture Info
System architecture information.

```json
{
  "event_bridge": {
    "name": "EventBridge v2.0",
    "port": 9998,
    "status": "running"
  },
  "learning_processor": {
    "name": "Learning Processor",
    "status": "running"
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_bridge` | object | Yes | EventBridge information |
| `learning_processor` | object | Yes | Learning processor information |
| `agents` | object | Yes | Agent information |

## 📚 Related Schemas

- [Request Schemas](requests.md)
- [Response Schemas](responses.md)
- [Enumeration Types](enums.md)

## 📖 Further Reading

- [API Overview](../overview.md)
- [OpenAPI Specifications](../openapi/)
- [Endpoint Documentation](../endpoints/)