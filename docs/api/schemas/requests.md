# Request Schemas

Data structures for API request bodies used in the ELF system.

## 🎯 Orchestrator Requests

### Orchestrator Request
Request sent to the orchestrator for decision-making or coordination.

```json
{
  "component": "dashboard",
  "request_type": "coordination",
  "data": {
    "action": "list_agents"
  },
  "priority": 5
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component making the request |
| `request_type` | string | Yes | Type of request |
| `data` | object | Yes | Request-specific data |
| `priority` | integer | No | Request priority (1-10, default: 1) |

**Valid `request_type` values:**
- `decision` - General decision requests
- `coordination` - Component coordination
- `health_check` - Health status requests
- `mission_submission` - Mission submission
- `sentinel_coordination` - Sentinel coordination
- `pattern_coordination` - Pattern coordination
- `sentinel_analysis` - Sentinel analysis

## 🚀 Mission Requests

### Mission Submission
Request to submit a new mission for execution.

```json
{
  "agent_type": "researcher",
  "mission": "Research the latest developments in artificial intelligence",
  "task_id": "task_12345",
  "source": "dashboard"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_type` | string | Yes | Type of agent to execute the mission |
| `mission` | string | Yes | Mission description |
| `task_id` | string | No | Optional task identifier |
| `source` | string | No | Source of the mission request (default: "dashboard") |

### Mission Status Update
Request to update the status of an existing mission.

```json
{
  "status": "running",
  "progress": 25.0,
  "details": {
    "current_step": "data_collection"
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New mission status |
| `progress` | number | No | Mission progress percentage (0-100) |
| `details` | object | No | Additional status details |

## 👥 Agent Requests

### Agent Execution
Request to run a specific agent with a mission.

```json
{
  "agent_type": "researcher",
  "mission": "Research the latest developments in artificial intelligence",
  "task_id": "task_12345",
  "source": "dashboard"
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_type` | string | Yes | Type of agent to execute |
| `mission` | string | Yes | Mission for the agent |
| `task_id` | string | No | Optional task identifier |
| `source` | string | No | Source of the request (default: "dashboard") |

## 🔍 Health Requests

### Component Health Check
Request to check the health of a specific component.

```json
{
  "component": "event_bridge",
  "details": true
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component` | string | Yes | Component to check |
| `details` | boolean | No | Whether to include detailed information |

## 📊 Analysis Requests

### Data Analysis
Request for data analysis or pattern recognition.

```json
{
  "analysis_type": "trend_analysis",
  "data_source": "metrics_table",
  "parameters": {
    "time_range": "last_24_hours",
    "metrics": ["events_per_minute", "tool_usage"]
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `analysis_type` | string | Yes | Type of analysis to perform |
| `data_source` | string | Yes | Source of data for analysis |
| `parameters` | object | No | Analysis-specific parameters |

## 🛠️ Utility Requests

### Configuration Update
Request to update system configuration.

```json
{
  "config_section": "event_bridge",
  "settings": {
    "log_level": "DEBUG",
    "max_events_per_minute": 1000
  }
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config_section` | string | Yes | Configuration section to update |
| `settings` | object | Yes | New configuration settings |

### Diagnostic Request
Request to run system diagnostics.

```json
{
  "diagnostic_type": "comprehensive",
  "components": ["event_bridge", "orchestrator"],
  "verbose": true
}
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `diagnostic_type` | string | Yes | Type of diagnostic to run |
| `components` | array | No | Specific components to diagnose |
| `verbose` | boolean | No | Whether to include detailed output |

## 📋 Field Constraints

### Priority Levels
Integer values from 1-10:
- 1-3: Low priority
- 4-7: Medium priority
- 8-10: High priority

### Progress Percentage
Number value from 0.0-100.0 representing completion percentage.

### Component Names
Valid component names:
- `event_bridge`
- `orchestrator`
- `dashboard`
- `learning_processor`
- `sentinel`
- `ceo`

## 📚 Related Schemas

- [Common Objects](common-objects.md)
- [Response Schemas](responses.md)
- [Enumeration Types](enums.md)

## 📖 Further Reading

- [API Overview](../overview.md)
- [OpenAPI Specifications](../openapi/)
- [Endpoint Documentation](../endpoints/)