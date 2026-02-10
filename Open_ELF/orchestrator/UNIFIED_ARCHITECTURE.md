# Unified OpenCode Orchestrator Architecture

## Overview

The Unified OpenCode Orchestrator replaces the separate Event Bridge and traditional Orchestrator systems with a single, intelligent system that serves as the central brain of the ELF ecosystem.

## Key Benefits

1. **Single Point of Control**: One system to monitor and control all OpenCode activities
2. **Intelligent Decision Making**: AI-driven engine for handling escalations and system issues
3. **Autonomous Operation**: Reduced need for human intervention through smart automation
4. **Consolidated Monitoring**: Unified view of all system events and activities
5. **Better Coordination**: Eliminates synchronization issues between separate systems

## Architecture Components

### 1. Event Processing Layer
- Listens to OpenCode SSE events in real-time
- Monitors file system changes (CEO inbox, sentinel events)
- Watches database health and system metrics
- Converts all inputs to standardized internal events

### 2. Decision Engine
- AI-driven system for analyzing events and determining appropriate actions
- Autonomous resolution of common issues
- Intelligent escalation to CEO only when necessary
- Learning from past events to improve future decisions

### 3. Action Executor
- Executes missions using persistent OpenCode sessions
- Manages task lifecycle and reporting
- Handles system recovery and restart procedures
- Interfaces with external services when needed

### 4. Status Reporting
- HTTP status endpoint for monitoring
- Detailed logging for debugging
- Dashboard integration for visualization

## Event Types Handled

1. **Tool Failures**: Automatic restart or escalation
2. **System Errors**: Recovery attempts or CEO notification
3. **System Health**: Monitoring and maintenance triggers
4. **CEO Escalations**: Database recording and autonomous resolution attempts
5. **Watcher Alerts**: Monitoring system notifications
6. **Missions**: Traditional orchestrator mission processing

## Intelligence Features

### Autonomous Resolution
- Attempts to fix issues before escalating to humans
- Tracks success/failure of resolution attempts
- Learns from outcomes to improve future decisions

### Smart Escalation
- Only escalates critical issues that require human attention
- Provides context-rich information to CEO
- Records escalations in database for dashboard visibility

### Adaptive Monitoring
- Adjusts monitoring frequency based on system stability
- Prioritizes critical events over informational ones
- Throttles non-essential notifications

## API Endpoints

### Status
```
GET http://localhost:9999/status
```

### Control (via Dashboard)
```
POST /api/v1/orchestrator/control
POST /api/v1/event-bridge/control
```

## Deployment

### Starting the System
```bash
# Preferred method
./start_unified_orchestrator.sh

# Direct method
python3 unified_orchestrator.py start
```

### Stopping the System
```bash
pkill -f unified_orchestrator.py
```

## Migration from Old Systems

### What's Replaced
- `event_bridge.py` - Now part of unified orchestrator
- `orchestrator.py` - Replaced by unified orchestrator
- Separate monitoring scripts - Consolidated into single system

### Backward Compatibility
- Existing dashboard endpoints continue to work
- Control commands redirect to unified system
- No changes needed for existing mission files

## Future Enhancements

1. **Machine Learning**: Train models on event patterns for better predictions
2. **Advanced Analytics**: More sophisticated pattern recognition
3. **Multi-System Coordination**: Extend to control other ELF components
4. **Predictive Maintenance**: Anticipate issues before they occur

## Monitoring Integration

The unified orchestrator integrates with:
- Dashboard backend for status reporting
- Database for escalation recording
- File system for CEO inbox monitoring
- Event chronicle for historical analysis

This creates a comprehensive monitoring ecosystem that provides better visibility and control than the previous fragmented approach.