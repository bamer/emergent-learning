# Orchestrator Service Management

This document describes the service management architecture of the Unified Orchestrator.

## Overview

The Unified Orchestrator (`Open_ELF/orchestrator/unified_orchestrator.py`) is responsible for:
1. Connecting to EventBridge for event processing
2. Managing essential ELF services (auto-start, health monitoring, restart)
3. Processing escalations from Sentinel
4. Running autonomous system checks

## Essential Services

The following services are managed by the Unified Orchestrator:

| Service | Script | Purpose | Auto-Start |
|---------|--------|---------|------------|
| **EventBridge** | `core/event_bridge_v2.py` | Event routing and monitoring | ✅ Yes |
| **Learning Capture** | `scripts/background-learning-capture.py` | Auto-capture learnings and heuristics | ✅ Yes |
| **Sentinel** | `core/sentinel.py` | System monitoring and escalation | ✅ Yes |

## Service Auto-Start Architecture

### `_ensure_services_started()` Method

This method is called during Orchestrator initialization to ensure all essential services are running:

```python
def _ensure_services_started(self):
    """Ensure essential services are running on Orchestrator startup.
    
    Starts Learning Capture and Sentinel if not already running.
    No external dependencies (no crontab, no systemd).
    """
```

### Startup Order

1. **EventBridge** (Critical dependency)
   - Must be running for orchestrator to function
   - Started first to ensure availability

2. **Learning Capture**
   - Auto-captures learnings from system activity
   - Checks every 60 seconds for new heuristics

3. **Sentinel**
   - Monitors system health
   - Escalates issues to Orchestrator

### Process

```
Orchestrator Start
    ↓
_ensure_services_started()
    ↓
For each service:
    1. Check if process is running (pgrep)
    2. If not running → Start it
    3. If running → Log PID and continue
    ↓
All Services Running ✓
```

## Self-Healing

The Orchestrator also monitors service health and can restart failed services:

### Health Check Cycle

- Runs every 100 seconds (10 ticks × 10 seconds)
- Checks all essential services
- If service is down → automatically restarts it

### Restart Logic

```python
if service.status in ["down", "inactive", "stopped", "failed"]:
    logger.info(f"🔄 Attempting to restart {service.name}...")
    self._restart_{service_name}()
```

## Starting the Orchestrator

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF
python3 orchestrator/unified_orchestrator.py start
```

### What Happens on Startup

1. Connects to existing EventBridge (port 9998)
2. Calls `_ensure_services_started()` to start essential services
3. Registers as listener with EventBridge
4. Starts event processor
5. Starts escalation file sentinel
6. Starts autonomous system checks (every 15 minutes)
7. Enters main loop (ticks every 10 seconds)

## Service Status

Check service status via the Dashboard API:

```bash
curl http://localhost:8888/api/v1/system/services
```

Response includes:
- `running`: Whether service process is active
- `health`: healthy/degraded/unhealthy
- `pid`: Process ID
- `last_heartbeat`: Last heartbeat timestamp

## No External Dependencies

This architecture intentionally avoids:
- **No crontab**: Services are managed by Orchestrator itself
- **No systemd**: Pure Python subprocess management
- **No init scripts**: Self-contained startup logic

This ensures the system can be started from any context where Python is available.

## Troubleshooting

### Services Not Starting

Check orchestrator logs:
```bash
tail -50 /tmp/orch_new.log
```

Look for:
- `🔧 Ensuring essential services are started...`
- `✅ Learning Capture started`
- `✅ Sentinel started`
- Error messages

### Service Keeps Crashing

1. Check individual service logs:
   - Learning Capture: `Open_ELF/logs/learning-capture.log`
   - Sentinel: Check dashboard or coordination logs

2. Run service manually to see errors:
   ```bash
   cd /home/bamer/.opencode/emergent-learning
   python3 scripts/background-learning-capture.py
   ```

### Port Conflicts

EventBridge requires port 9998. Check if port is in use:
```bash
lsof -i :9998
```

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - Database maintenance

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Author**: CEO Agent (Level 3)
