# Unified Orchestrator Launch Guide

## Overview

The Unified Orchestrator is the central brain of the ELF ecosystem, combining event processing, intelligent decision making, and mission orchestration into a single system.

## Prerequisites

Before launching, ensure:
1. OpenCode server is running (or simulation is acceptable)
2. Required directories exist:
   - `~/.opencode/tasks/`
   - `~/.opencode/emergent-learning/.coordination/`
   - `~/.opencode/emergent-learning/ceo-inbox/`
3. Python 3.8+ is installed
4. Required dependencies are available

## Launch Methods

### Method 1: Using Launch Script (Recommended)
```bash
# Navigate to orchestrator directory
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator

# Launch the unified orchestrator
./start_unified_orchestrator.sh
```

This method:
- Ensures directories exist
- Checks OpenCode connectivity
- Stops any existing orchestrator processes
- Starts the unified orchestrator in background
- Verifies successful startup

### Method 2: Direct Python Execution
```bash
# Navigate to orchestrator directory
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator

# Start the orchestrator
python3 unified_orchestrator.py start
```

### Method 3: Systemd Service (Production)
```bash
# Copy service file to systemd directory
sudo cp unified-orchestrator.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable unified-orchestrator

# Start service
sudo systemctl start unified-orchestrator

# Check status
sudo systemctl status unified-orchestrator
```

## Key Capabilities

### 1. Real-time Event Processing
The orchestrator listens to multiple event sources:
- **OpenCode SSE Stream**: Tools, errors, messages, sessions
- **CEO Inbox Directory**: Manual escalations and decisions
- **System Health Monitoring**: Database and infrastructure status
- **Watcher Events**: System monitoring alerts
- **Mission Requests**: Assigned tasks for execution

Example event processing:
```
🔧 Tool failure detected: bash execution failed
🧠 Analyzing failure pattern...
🔄 Attempting autonomous resolution...
✅ Service restarted successfully
📊 Recording resolution in database...
```

### 2. Intelligent Decision Making
AI-driven decision engine evaluates events and determines appropriate actions:
- **Autonomous Resolution**: Fix common issues automatically
- **Smart Escalation**: Only escalate when human intervention needed
- **Database Recording**: Log all critical events for dashboard visibility
- **Learning Integration**: Extract insights using [LEARNED:] markers

Decision matrix example:
```
Event: Database connection error (Severity: CRITICAL)
Analysis: Connection pool exhausted
Action: Restart database service + CEO escalation
Record: Database event_chronicle table
Learn: [LEARNED:database] Connection pooling requires monitoring
```

### 3. Mission Orchestration
Execute complex missions using persistent OpenCode sessions:
- **Mission Assignment**: Via file system or API
- **Persistent Sessions**: Single session reused for efficiency
- **Progress Tracking**: Real-time status updates
- **Error Handling**: Automatic retry and recovery

Mission execution example:
```bash
# Create mission file in .coordination/missions/
echo '{
  "taskId": "mission-001",
  "role": "researcher",
  "description": "Analyze system performance bottlenecks"
}' > /home/bamer/.opencode/emergent-learning/.coordination/missions/mission-001.json
```

The orchestrator automatically picks up and executes the mission.

### 4. System Monitoring
Comprehensive monitoring capabilities:
- **Health Checks**: Database, OpenCode, file system
- **Performance Metrics**: CPU, memory, response times
- **Alert Management**: Threshold-based notifications
- **Status Reporting**: HTTP endpoint for dashboard integration

## API Endpoints

### Status Endpoint
```
GET http://localhost:9999/status

Response:
{
  "running": true,
  "events_processed": 127,
  "missions_count": 3,
  "processing_count": 0,
  "queue_size": 0,
  "events_in_queue": 0,
  "missions": [...],
  "recent_events": [...]
}
```

### Dashboard Integration
The orchestrator integrates with the ELF dashboard through:
- `/api/v1/orchestrator/status` - Get orchestrator status
- `/api/v1/orchestrator/control` - Start/stop/restart orchestrator
- `/api/v1/event-bridge/control` - Event bridge control (redirected to orchestrator)

## Example Use Cases

### 1. Automatic Tool Failure Recovery
```
Event: bash tool failed with "permission denied"
Action: Restart service and retry operation
Result: Success - issue resolved automatically
Learning: [LEARNED:bash] Permission issues often resolve with service restart
```

### 2. Critical System Alert
```
Event: Database connection pool exhaustion (CRITICAL)
Action: 
  1. Restart database service
  2. Record escalation in database
  3. Create CEO inbox item
  4. Notify dashboard
Result: CEO notified, issue logged, recovery attempted
```

### 3. Mission Execution
```
Mission: "Refactor logging system for better performance"
Process:
  1. @researcher - Analyze current logging implementation
  2. @architect - Design improved logging architecture
  3. @coder - Implement new logging system
  4. @tester - Validate performance improvements
Result: 40% logging performance improvement
Learning: [LEARNED:performance] Asynchronous logging reduces overhead
```

### 4. Watcher System Alert
```
Event: High CPU usage detected (WARNING)
Action:
  1. Increase monitoring frequency
  2. Run diagnostic procedures
  3. Identify resource-intensive processes
Result: Issue monitored, no escalation needed
```

## Monitoring and Troubleshooting

### Check Logs
```bash
# View orchestrator logs
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/unified_orchestrator.log

# Check systemd service logs (if using service)
sudo journalctl -u unified-orchestrator -f
```

### Verify Status
```bash
# Check if orchestrator is running
pgrep -f unified_orchestrator.py

# Check HTTP status endpoint
curl http://localhost:9999/status
```

### Common Issues

1. **OpenCode Connection Failed**
   - Ensure OpenCode server is running on localhost:4096
   - Check network connectivity
   - Verify server health endpoint

2. **Permission Denied Errors**
   - Check file/directory permissions
   - Ensure user has write access to required directories
   - Verify Python script execution permissions

3. **Database Connection Issues**
   - Verify database file exists and is accessible
   - Check database health and integrity
   - Ensure required tables are created

## Best Practices

### For Maximum Effectiveness
1. **Keep Running**: The orchestrator learns from continuous operation
2. **Monitor Logs**: Regular log review identifies improvement opportunities
3. **Update Configuration**: Customize event processing rules as needed
4. **Review Escalations**: Analyze CEO escalations for pattern identification
5. **Capture Learnings**: Use [LEARNED:] markers liberally for knowledge building

### Performance Optimization
1. **Resource Management**: Monitor CPU/memory usage
2. **Event Throttling**: Configure appropriate event processing rates
3. **Database Optimization**: Ensure efficient database queries
4. **Network Efficiency**: Minimize external service calls
5. **Caching Strategy**: Cache frequently accessed data

## Integration with Other Systems

### Dashboard Integration
The orchestrator seamlessly integrates with the ELF dashboard:
- Provides real-time status updates
- Records escalations for visibility
- Updates mission tracking
- Sends health metrics

### Database Integration
All critical events and escalations are recorded in the database:
- Enables dashboard visibility
- Provides historical analysis
- Supports pattern recognition
- Facilitates reporting

### File System Integration
Monitors key directories for system changes:
- CEO inbox for manual escalations
- Mission directory for assigned tasks
- Event chronicle for watcher alerts
- Configuration files for updates

## Extending Capabilities

### Adding New Event Types
1. Modify the `_process_sse_line` method to handle new event formats
2. Add corresponding event type handling in the decision engine
3. Update the event processing workflow
4. Test with sample events

### Custom Decision Logic
1. Extend the `DecisionEngine` class with new handling methods
2. Add severity determination logic for new event types
3. Implement custom resolution procedures
4. Update escalation criteria as needed

### Mission Extensions
1. Add new mission types to the mission processing queue
2. Implement specialized mission handlers
3. Create mission templates for common tasks
4. Add progress reporting for long-running missions

## Security Considerations

### Access Controls
- Limit file system access to required directories only
- Restrict bash command execution with permission system
- Protect sensitive configuration files
- Monitor unauthorized access attempts

### Data Protection
- Encrypt sensitive data in transit and at rest
- Sanitize inputs to prevent injection attacks
- Validate all external data sources
- Implement proper error handling to prevent information leakage

## Maintenance and Updates

### Regular Maintenance
1. **Log Rotation**: Prevent excessive log file growth
2. **Database Cleanup**: Remove old event records periodically
3. **Performance Tuning**: Optimize based on usage patterns
4. **Security Updates**: Keep dependencies current
5. **Backup Procedures**: Regular backup of critical data

### Update Process
1. **Backup**: Save current configuration and data
2. **Test Environment**: Deploy updates to test system first
3. **Gradual Rollout**: Deploy to production incrementally
4. **Monitoring**: Watch for issues post-update
5. **Rollback Plan**: Prepare for quick rollback if needed

## Conclusion

The Unified Orchestrator provides a powerful, intelligent system for managing the ELF ecosystem. By combining event processing, decision making, and mission orchestration into a single system, it eliminates the complexity and synchronization issues of separate components while providing enhanced intelligence and automation capabilities.

With proper configuration and monitoring, the orchestrator will significantly improve system reliability, reduce manual intervention, and accelerate the learning process through continuous autonomous operation.