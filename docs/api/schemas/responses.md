# Response Schemas

Data structures for API response bodies used in the ELF system.

## 🎯 Orchestrator Responses

### Orchestrator Response
Response from the orchestrator containing decisions or coordination results.

```json
{
  "request_id": "req_20260212_103015_123456",
  "response_type": "coordination_result",
  "data": {
    "agents": [
      {"name": "researcher", "type": "analysis", "status": "available"}
    ],
    "recommendation": "proceed",
    "confidence": 0.9
  },
  "timestamp": "2026-02-12T10:30:15Z",
  "confidence": 0.9
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | Yes | Unique request identifier |
| `response_type` | string | Yes | Type of response |
| `data` | object | Yes | Response-specific data |
| `timestamp` | string | Yes | Response timestamp (ISO 8601) |
| `confidence` | number | Yes | Confidence level (0.0-1.0) |

**Valid `response_type` values:**
- `decision` - General decision response
- `coordination_result` - Coordination results
- `health_status` - Health status response
- `mission_triage` - Mission triage results
- `sentinel_coordination` - Sentinel coordination
- `pattern_coordination` - Pattern coordination results

## 🚀 Mission Responses

### Mission Submission Response
Response to a mission submission request.

```json
{
  "mission_id": "mission_20260212_103015_12345",
  "status": "submitted",
  "estimated_time": 300,
  "priority": 3,
  "confidence": 0.95
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mission_id` | string | Yes | Unique mission identifier |
| `status` | string | Yes | Mission status |
| `estimated_time` | integer | No | Estimated completion time (seconds) |
| `priority` | integer | No | Mission priority (1-10) |
| `confidence` | number | No | Confidence level (0.0-1.0) |

### Mission Details Response
Detailed information about a specific mission.

```json
{
  "mission_id": "mission_20260212_103015_12345",
  "agent_type": "researcher",
  "mission": "Research the latest developments in artificial intelligence",
  "status": "running",
  "created_at": "2026-02-12T10:30:15Z",
  "updated_at": "2026-02-12T10:32:45Z",
  "progress": 25.0
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mission_id` | string | Yes | Unique mission identifier |
| `agent_type` | string | Yes | Type of agent executing the mission |
| `mission` | string | Yes | Mission description |
| `status` | string | Yes | Current mission status |
| `created_at` | string | Yes | When mission was created (ISO 8601) |
| `updated_at` | string | Yes | When mission was last updated (ISO 8601) |
| `progress` | number | No | Mission progress percentage (0-100) |

### Mission List Response
List of missions with summary information.

```json
{
  "missions": [
    {
      "mission_id": "mission_20260212_103015_12345",
      "agent_type": "researcher",
      "mission": "Research AI developments",
      "status": "running",
      "created_at": "2026-02-12T10:30:15Z",
      "updated_at": "2026-02-12T10:32:45Z",
      "progress": 25.0
    }
  ],
  "total": 1,
  "active": 1
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `missions` | array | Yes | Array of mission objects |
| `total` | integer | Yes | Total number of missions |
| `active` | integer | Yes | Number of active missions |

## 👥 Agent Responses

### Agent List Response
List of available agents in the system.

```json
{
  "agents": [
    {
      "name": "researcher",
      "type": "analysis",
      "status": "available",
      "last_seen": "2026-02-12T10:30:15Z"
    }
  ],
  "status": "success"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agents` | array | Yes | Array of agent objects |
| `status` | string | Yes | Request status |

**Agent Object Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Agent name |
| `type` | string | Yes | Agent type |
| `status` | string | Yes | Agent status |
| `last_seen` | string | Yes | When agent was last seen (ISO 8601) |

## 🔍 Health Responses

### Component Health Response
Health status for a specific component.

```json
{
  "component": "event_bridge",
  "status": "healthy",
  "details": {
    "events_processed": 1247,
    "uptime_seconds": 3600
  },
  "confidence": 0.95,
  "recommendation": "continue"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component name |
| `status` | string | Yes | Health status |
| `details` | object | No | Additional health details |
| `confidence` | number | No | Confidence level (0.0-1.0) |
| `recommendation` | string | No | Recommended action |

### System Health Response
Overall system health status.

```json
{
  "status": "healthy",
  "components": {
    "event_bridge": "healthy",
    "learning_processor": "healthy",
    "sentinel": "healthy",
    "orchestrator": "healthy",
    "ceo": "healthy"
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

## 📊 Monitoring Responses

### Monitoring Summary Response
Quick summary of system monitoring data.

```json
{
  "status": "🟢 Running",
  "uptime": "3600s",
  "events_pm": "15.5",
  "heuristics": 247,
  "golden_rules": 12,
  "trails": 1542,
  "pheromones": 89,
  "tools_detected": 234,
  "db_size": "2560KB"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | System status indicator |
| `uptime` | string | Yes | System uptime |
| `events_pm` | string | Yes | Events per minute |
| `heuristics` | integer | Yes | Number of heuristics |
| `golden_rules` | integer | Yes | Number of golden rules |
| `trails` | integer | Yes | Number of trails |
| `pheromones` | integer | Yes | Number of pheromone trails |
| `tools_detected` | integer | Yes | Number of tools detected |
| `db_size` | string | Yes | Database size |

### Detailed Statistics Response
Comprehensive system statistics.

```json
{
  "timestamp": "2026-02-12T10:30:15Z",
  "uptime_seconds": 3600,
  "architecture": {},
  "database": {
    "path": "/home/bamer/.opencode/emergent-learning/memory/index.db",
    "size_kb": 2560
  },
  "events": {},
  "learning": {},
  "tools": {},
  "system": {
    "status": "healthy",
    "components_healthy": 5,
    "total_components": 5
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string | Yes | Statistics timestamp (ISO 8601) |
| `uptime_seconds` | integer | Yes | System uptime in seconds |
| `architecture` | object | Yes | Architecture information |
| `database` | object | Yes | Database information |
| `events` | object | Yes | Event statistics |
| `learning` | object | Yes | Learning statistics |
| `tools` | object | Yes | Tool detection statistics |
| `system` | object | Yes | System information |

## ⚠️ Error Responses

### Standard Error Response
Standard format for API error responses.

```json
{
  "status": "error",
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid request parameters",
    "details": {
      "field": "agent_type",
      "issue": "Field is required"
    }
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Always "error" |
| `error` | object | Yes | Error details |
| `error.code` | string | Yes | Machine-readable error code |
| `error.message` | string | Yes | Human-readable error message |
| `error.details` | object | No | Additional error context |

## 📋 Common Response Patterns

### Success Response Wrapper
All successful responses follow this pattern:
```json
{
  "status": "success",
  "data": {},
  "message": "Optional message"
}
```

### Error Response Wrapper
All error responses follow this pattern:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

## 📚 Related Schemas

- [Common Objects](common-objects.md)
- [Request Schemas](requests.md)
- [Enumeration Types](enums.md)

## 📖 Further Reading

- [API Overview](../overview.md)
- [OpenAPI Specifications](../openapi/)
- [Endpoint Documentation](../endpoints/)