# Enumeration Types

Defined enumeration values used throughout the ELF API system.

## 🏥 Health Status Values

### Component Health Status
Values for component health status indicators.

**Valid Values:**
- `healthy` - Component is functioning normally
- `degraded` - Component has minor issues but is still operational
- `unhealthy` - Component has major issues and may not be functional
- `unknown` - Unable to determine component health

**Usage:**
```json
{
  "status": "healthy"
}
```

### System Health Status
Values for overall system health status.

**Valid Values:**
- `healthy` - System is functioning normally
- `degraded` - System has minor issues but is still operational
- `unhealthy` - System has major issues and may not be functional

**Usage:**
```json
{
  "status": "healthy"
}
```

## 🚀 Mission Status Values

### Mission Execution Status
Values for mission execution status.

**Valid Values:**
- `submitted` - Mission has been submitted but not yet started
- `running` - Mission is currently being executed
- `completed` - Mission has finished successfully
- `failed` - Mission encountered an error and failed
- `cancelled` - Mission was cancelled before completion

**Usage:**
```json
{
  "status": "running"
}
```

## 👥 Agent Status Values

### Agent Availability Status
Values for agent availability status.

**Valid Values:**
- `available` - Agent is ready to accept missions
- `busy` - Agent is currently executing a mission
- `offline` - Agent is not responding or unavailable
- `error` - Agent is in an error state

**Usage:**
```json
{
  "status": "available"
}
```

## 🎯 Priority Levels

### Request Priority
Integer values from 1-10 indicating request priority.

**Value Ranges:**
- `1-3` - Low priority
- `4-7` - Medium priority
- `8-10` - High priority

**Usage:**
```json
{
  "priority": 5
}
```

## 📡 Request Types

### Orchestrator Request Types
Values for orchestrator request types.

**Valid Values:**
- `decision` - General decision requests
- `coordination` - Component coordination requests
- `health_check` - Health status requests
- `mission_submission` - Mission submission requests
- `sentinel_coordination` - Sentinel coordination requests
- `pattern_coordination` - Pattern coordination requests
- `sentinel_analysis` - Sentinel analysis requests

**Usage:**
```json
{
  "request_type": "coordination"
}
```

## 💬 Response Types

### Orchestrator Response Types
Values for orchestrator response types.

**Valid Values:**
- `decision` - General decision responses
- `coordination_result` - Coordination results
- `health_status` - Health status responses
- `mission_triage` - Mission triage results
- `sentinel_coordination` - Sentinel coordination responses
- `pattern_coordination` - Pattern coordination responses

**Usage:**
```json
{
  "response_type": "coordination_result"
}
```

## 🛠️ Component Names

### System Components
Valid component names used in health checks and status requests.

**Valid Values:**
- `event_bridge` - Event processing system
- `orchestrator` - Service management system
- `dashboard` - Web interface
- `learning_processor` - AI learning system
- `sentinel` - Monitoring agent
- `ceo` - Executive decision maker
- `mission_bridge` - Mission processing system
- `sentinel_monitor` - Sentinel monitoring system

**Usage:**
```json
{
  "component": "event_bridge"
}
```

## 📊 Event Types

### System Event Types
Common event types processed by the system.

**Valid Values:**
- `tool` - Tool execution events
- `message` - Message events
- `message.part.updated` - Message part updates
- `error` - Error events
- `failure` - Failure events
- `service` - Service events
- `health` - Health check events
- `server.heartbeat` - Server heartbeat events

**Usage:**
```json
{
  "event_type": "tool"
}
```

## 🔧 Agent Types

### System Agent Types
Valid agent types available in the system.

**Valid Values:**
- `researcher` - Research and information gathering
- `writer` - Content creation and documentation
- `analyst` - Data analysis and interpretation
- `developer` - Code generation and debugging
- `tester` - Quality assurance and testing
- `coordinator` - System coordination and management
- `sentinel` - Monitoring and alerting
- `ceo` - Executive decision making

**Usage:**
```json
{
  "agent_type": "researcher"
}
```

## 📈 Confidence Levels

### Confidence Values
Floating-point values from 0.0-1.0 indicating confidence levels.

**Value Ranges:**
- `0.0-0.3` - Low confidence
- `0.4-0.6` - Medium confidence
- `0.7-1.0` - High confidence

**Usage:**
```json
{
  "confidence": 0.95
}
```

## 📅 Timestamp Formats

### ISO 8601 Format
Standard timestamp format used throughout the API.

**Format:** `YYYY-MM-DDTHH:MM:SSZ`

**Examples:**
- `2026-02-12T10:30:15Z`
- `2026-02-12T10:30:15.123Z`

**Usage:**
```json
{
  "timestamp": "2026-02-12T10:30:15Z"
}
```

## 📊 Status Indicators

### System Status Indicators
Formatted status indicators for display purposes.

**Valid Values:**
- `🟢 Running` - System is running normally
- `🟡 Degraded` - System is running with issues
- `🔴 Stopped` - System is not running
- `🔵 Starting` - System is starting up
- `🟣 Stopping` - System is shutting down

**Usage:**
```json
{
  "status": "🟢 Running"
}
```

## 📚 Related Schemas

- [Common Objects](common-objects.md)
- [Request Schemas](requests.md)
- [Response Schemas](responses.md)

## 📖 Further Reading

- [API Overview](../overview.md)
- [OpenAPI Specifications](../openapi/)
- [Endpoint Documentation](../endpoints/)