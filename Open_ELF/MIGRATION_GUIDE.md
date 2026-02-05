# Migration Guide: Enhanced Event Bridge as Central Orchestrator

## Overview

This guide explains how to migrate existing components to work with the enhanced event bridge as the central orchestrator. The event bridge becomes the central nervous system that everything works with and for.

## Key Changes

### 1. New Architecture

**Before:** Separate event_bridge.py and orchestrator.py systems
**After:** Enhanced event bridge serves as central orchestrator

### 2. Centralized Decision Making

Components no longer make independent decisions. Instead, they:
- Ask the orchestrator for answers
- Submit missions to the orchestrator
- Report health to the orchestrator
- Coordinate through the orchestrator

### 3. API-Based Communication

All communication happens through the orchestrator's API:
- HTTP endpoints for external components
- Python API for internal components
- Standardized request/response format

## Migration Steps

### Step 1: Update Core Modules

First, ensure your component uses the new core modules:

```python
# Old way
import logging
import sqlite3
import json

# New way
from core.openelf_logging import get_logger, setup_logger
from core.database import get_connection, execute_query
from core.config import get_config
from core.central_orchestrator import ask_orchestrator
```

### Step 2: Replace Independent Decisions with Orchestrator Queries

**Before:** Component makes its own decisions

```python
# Old way - independent decision making
if system_load > 0.8:
    scale_down_operations()
elif available_memory < 0.1:
    escalate_to_ceo()
else:
    continue_operations()
```

**After:** Ask orchestrator for decisions

```python
# New way - coordinated decision making
response = await ask_orchestrator(
    component="health_monitor",
    request_type="decision",
    data={
        "context": {
            "system_load": system_load,
            "available_memory": available_memory
        },
        "options": ["scale_down", "continue", "escalate"]
    }
)

if response.response_type == "decision":
    if response.data["decision"] == "scale_down":
        scale_down_operations()
    elif response.data["decision"] == "escalate":
        escalate_to_ceo()
```

### Step 3: Submit Missions Through Orchestrator

**Before:** Direct mission execution

```python
# Old way - direct mission execution
mission_id = execute_mission(agent_type, mission_description)
```

**After:** Submit mission to orchestrator

```python
# New way - orchestrator coordinates missions
response = await ask_orchestrator(
    component="mission_submitter",
    request_type="mission_submission",
    data={
        "agent_type": agent_type,
        "mission": mission_description,
        "priority": priority_level
    }
)

if response.response_type == "mission_accepted":
    mission_id = response.data["mission_id"]
    # Monitor mission status through orchestrator
```

### Step 4: Report Health to Orchestrator

**Before:** Independent health monitoring

```python
# Old way - independent health checks
if check_database_health() == "unhealthy":
    log_error("Database unhealthy")
```

**After:** Report health to orchestrator

```python
# New way - orchestrator monitors system health
response = await ask_orchestrator(
    component="database_monitor",
    request_type="health_check",
    data={
        "component": "database",
        "status": "healthy",
        "details": {"connection_time": "15ms", "query_count": 123}
    }
)
```

### Step 5: Use Orchestrator API for External Communication

For components that need to communicate externally:

```python
import requests

# Check orchestrator health
response = requests.get("http://localhost:9998/status")
print(response.json())

# Ask orchestrator a question
question = {
    "component": "external_component",
    "request_type": "decision",
    "data": {
        "context": {"user_query": "What should I do?"},
        "options": ["option1", "option2", "option3"]
    }
}

response = requests.post("http://localhost:9998/api/v1/ask", json=question)
print(response.json())
```

## Component-Specific Migration

### For Mission Processors

```python
# Before: Direct mission processing
class MissionProcessor:
    def process_mission(self, mission):
        # Direct processing logic
        result = self.execute_mission(mission)
        return result

# After: Orchestrator-coordinated processing
class EnhancedMissionProcessor:
    async def process_mission(self, mission):
        # Submit mission to orchestrator
        response = await ask_orchestrator(
            component="mission_processor",
            request_type="mission_submission",
            data={"mission": mission}
        )
        
        if response.response_type == "mission_accepted":
            # Orchestrator will handle execution
            return response.data["mission_id"]
        else:
            raise Exception(f"Mission rejected: {response.data['reason']}")
```

### For Health Monitors

```python
# Before: Independent health monitoring
class HealthMonitor:
    def check_system(self):
        if self.check_database() == "unhealthy":
            self.restart_database()

# After: Orchestrator-coordinated health monitoring
class EnhancedHealthMonitor:
    async def check_system(self):
        # Report health to orchestrator
        response = await ask_orchestrator(
            component="health_monitor",
            request_type="health_check",
            data={
                "component": "database",
                "status": self.check_database(),
                "details": self.get_database_details()
            }
        )
        
        # Follow orchestrator's recommendation
        if response.data.get("recommendation") == "restart":
            self.restart_database()
```

### For Event Handlers

```python
# Before: Direct event handling
class EventHandler:
    def handle_event(self, event):
        if event["type"] == "error":
            self.handle_error(event)

# After: Orchestrator-coordinated event handling
class EnhancedEventHandler:
    async def handle_event(self, event):
        # Ask orchestrator how to handle this event
        response = await ask_orchestrator(
            component="event_handler",
            request_type="decision",
            data={
                "event_type": event["type"],
                "event_data": event,
                "context": "event_handling"
            }
        )
        
        # Execute orchestrator's decision
        if response.response_type == "decision":
            self.execute_decision(response.data["decision"], event)
```

## API Reference

### HTTP Endpoints

#### GET /status
Returns orchestrator status
```json
{
  "service": "enhanced_event_bridge",
  "status": "running",
  "timestamp": "2025-02-05T20:30:45.123456",
  "events_processed": 1234,
  "version": "1.0.0"
}
```

#### GET /api/v1/health/{component}
Check health of a specific component
```json
{
  "request_id": "req_20250205_203045_123456",
  "response_type": "health_status",
  "data": {
    "component": "database",
    "status": "healthy",
    "details": {"connection_time": "15ms"},
    "recommendation": "continue"
  },
  "timestamp": "2025-02-05T20:30:45.123456",
  "confidence": 0.95
}
```

#### POST /api/v1/ask
Ask orchestrator for a decision
```json
Request:
{
  "component": "mission_processor",
  "request_type": "decision",
  "data": {
    "context": {"system_load": 0.7},
    "options": ["scale_down", "continue"]
  },
  "priority": 3
}

Response:
{
  "request_id": "req_20250205_203045_123456",
  "response_type": "decision",
  "data": {
    "decision": "continue",
    "reason": "System load acceptable"
  },
  "timestamp": "2025-02-05T20:30:45.123456",
  "confidence": 0.8
}
```

#### POST /api/v1/mission
Submit a mission to orchestrator
```json
Request:
{
  "agent_type": "researcher",
  "mission": "Research latest AI developments",
  "priority": 5
}

Response:
{
  "request_id": "req_20250205_203045_123456",
  "response_type": "mission_accepted",
  "data": {
    "mission_id": "mission_20250205_203045_123456",
    "agent_type": "researcher",
    "estimated_time": 300,
    "priority": 5
  },
  "timestamp": "2025-02-05T20:30:45.123456",
  "confidence": 0.9
}
```

### Python API

#### ask_orchestrator(component, request_type, data, priority=1)
Main function to ask orchestrator for answers

```python
response = await ask_orchestrator(
    component="my_component",
    request_type="decision",
    data={"question": "What should I do?"},
    priority=5
)
```

#### get_central_orchestrator()
Get the orchestrator instance for advanced usage

```python
orchestrator = get_central_orchestrator()
response = await orchestrator.ask_orchestrator(request)
```

## Migration Checklist

- [ ] Update imports to use core modules
- [ ] Replace independent decisions with orchestrator queries
- [ ] Submit missions through orchestrator instead of direct execution
- [ ] Report health to orchestrator instead of independent monitoring
- [ ] Use orchestrator API for external communication
- [ ] Test component integration with enhanced event bridge
- [ ] Update documentation to reflect new architecture

## Testing Migration

### Test Orchestrator Connectivity

```python
# Test basic connectivity
import requests

try:
    response = requests.get("http://localhost:9998/status")
    print("Orchestrator is running:", response.json())
except:
    print("Orchestrator is not accessible")
```

### Test Decision Making

```python
# Test decision making
import asyncio
from core.central_orchestrator import ask_orchestrator

async def test_decision():
    response = await ask_orchestrator(
        component="test_component",
        request_type="decision",
        data={"test": "simple_decision"}
    )
    print("Decision response:", response)

asyncio.run(test_decision())
```

## Benefits of Migration

1. **Centralized Control**: Single point of coordination
2. **Intelligent Decisions**: AI-driven decision making
3. **Better Coordination**: Components work together seamlessly
4. **Scalability**: Easy to add new components
5. **Maintainability**: Centralized logic reduces duplication
6. **Observability**: Unified monitoring and logging

## Troubleshooting

### Orchestrator Not Accessible
- Check if enhanced event bridge is running
- Verify port 9998 is not blocked
- Check event bridge logs for errors

### API Requests Failing
- Verify request format matches specification
- Check component name is valid
- Ensure data format is correct

### Performance Issues
- Monitor orchestrator load
- Consider batching requests
- Adjust logging levels if too verbose

## Next Steps

After migrating components:
1. Monitor system performance
2. Gather feedback on new architecture
3. Optimize orchestrator decision logic
4. Add more intelligent features
5. Expand API capabilities

## Support

For migration assistance:
- Check the enhanced_event_bridge.py source code
- Review core module documentation
- Test with simple components first
- Contact system administrators for complex migrations