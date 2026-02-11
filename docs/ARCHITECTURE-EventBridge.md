# EventBridge Architecture

## Overview

The **EventBridge** is the central event processing system for the Emergent Learning Framework (ELF). It connects the OpenCode agent execution environment with the ELF learning and monitoring systems.

**Key Function:** Capture agent activities (tool usage, messages, sessions) and trigger learning hooks to record heuristics, trails, and pheromones.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenCode Environment                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Agent 1    │  │   Agent 2    │  │   Agent N    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                    ┌──────▼──────┐                         │
│                    │ OpenCode    │                         │
│                    │ API Server  │                         │
│                    │ :4096       │                         │
│                    └──────┬──────┘                         │
└───────────────────────────┼─────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │   SSE Stream │ │   Sessions   │ │   Messages   │
   │   /event     │ │   /session   │ │   /message   │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
               ┌───────────▼───────────┐
               │     EventBridge       │
               │   event_bridge.py     │
               │                       │
               │  ┌─────────────────┐  │
               │  │  HookManager    │  │
               │  │  - PreToolUse   │  │
               │  │  - PostToolUse  │  │
               │  └─────────────────┘  │
               └───────────┬───────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │ Heuristics   │ │   Trails     │ │ Pheromones   │
   │   Engine     │ │   System     │ │   System     │
   └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Event Sources

### SSE Stream (Primary & Only)

**Endpoint:** `http://localhost:4096/event`

**Event Types Captured:**
- `message` - Agent messages
- `message.part.updated` - Message content updates
- `session.updated` - Session state changes
- `server.heartbeat` - Server health
- `session.status` - Session status changes

**Architecture:** SSE-only connection (polling removed due to excessive connections causing system failures)

### Timeout Guidelines (MANDATORY)

**IMPORTANT:** All async operations MUST use relaxed timeout settings:

- **Minimum timeout:** 20 seconds
- **Maximum timeout:** 10 minutes
- **Recommended for long-running tools:** 2-5 minutes
- **Recommended for database operations:** 30-60 seconds
- **Recommended for API calls:** 60-120 seconds

**Example:**
```python
# Good - relaxed timeout
async def process_tool(tool_name, input_data):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        async with session.post(url, json=input_data) as response:
            return await response.json()

# Bad - aggressive timeout (causes failures)
async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
    # This will timeout frequently
```

### Async/Await Pattern (MANDATORY)

**IMPORTANT:** All newly developed components MUST use async/await pattern:

```python
# Correct pattern
async def process_event(event_data):
    # Database operations
    await store_event_async(event_data)

    # API calls
    await send_notification_async(event_data)

    # File operations
    await write_log_async(event_data)

# Blocking pattern (NOT ALLOWED in new code)
def process_event_blocking(event_data):
    # This blocks the event loop
    store_event(event_data)  # ❌ Blocking
    send_notification(event_data)  # ❌ Blocking
```

**Benefits:**
- Non-blocking I/O operations
- Better resource utilization
- Handles slow operations gracefully
- Prevents system failures under load

---

## Hook System

### Hook Types

#### PreToolUse
**Triggered:** Before tool execution
**Purpose:** Prepare context, load semantic memory
**Script:** `hooks/PreToolUse/semantic-memory.py`

#### PostToolUse
**Triggered:** After tool execution completes
**Purpose:** Record heuristics, trails, pheromones
**Scripts:**
- `hooks/learning-loop/post_tool_learning.py` - Heuristics
- `hooks/learning-loop/record_pheromone.py` - Pheromones
- `hooks/post_tool_use/sync-golden-rules.py` - Golden rules

### Hook Data Format

```json
{
  "event_type": "PostToolUse",
  "tool_name": "read_file",
  "tool_input": {"file_path": "/path/to/file"},
  "tool_output": {"content": "..."},
  "success": true,
  "session_id": "session-uuid",
  "timestamp": "2026-02-06T08:30:00Z",
  "user_message": "Original user request",
  "tools_used": [...]
}
```

---

## Configuration

### EventBridge Config File

**Location:** `Open_ELF/orchestrator/event_bridge_config.json`

```json
{
  "logging": {
    "throttle_seconds": 5,
    "important_events": ["message", "tool", "error", "session"],
    "summary_interval": 10,
    "max_details_length": 100
  },
  "status_server": {
    "default_port": 9998,
    "fallback_port": 9999
  }
}
```

### Hook Directories

- `~/.opencode/hooks/PostToolUse/` - Post-tool execution hooks
- `~/.opencode/hooks/learning-loop/` - Learning system hooks
- `~/.opencode/hooks/PreToolUse/` - Pre-tool execution hooks

---

## Monitoring & Health

### Heartbeat File

**Location:** `.coordination/event-bridge-heartbeat.json`

**Content:**
```json
{
  "started_at": "2026-02-06T07:19:03",
  "last_event_time": "2026-02-06T08:50:41",
  "events_processed": 15990,
  "running": true,
  "health": "healthy",
  "event_stats": {
    "total_types": 10,
    "top_events": {
      "message.part.updated": 15059,
      "message.updated": 335
    }
  }
}
```

### Logs

**Location:** `Open_ELF/logs/event_bridge.log`

**Key Log Messages:**
- `📡 SSE event received: {event_type}` - Event captured via SSE
- `🔧 Tool detected: {tool_name}` - Tool captured
- `✅ Events processed: {count}` - Event summary
- `❌ SSE connection error: {error}` - Connection issues

### Health Check

**HTTP Status Server:**
- **Default Port:** 9998 (fallback to 9999)
- **Endpoint:** `http://localhost:9998`

**Available Endpoints:**
- `GET /` - Main status page (HTML)
- `GET /health` - Overall health check (JSON)
- `GET /health/event_bridge` - EventBridge instance health
- `GET /health/mission_bridge` - Mission bridge health with hooks_executed counter
- `GET /health/sentinel_monitor` - Sentinel monitor health with events_monitored counter

**Response Examples:**

Mission Bridge:
```json
{
  "status": "healthy",
  "service": "mission_bridge",
  "running": true,
  "hooks_executed": 63345,
  "last_heartbeat": "2026-02-07T06:06:32.018314"
}
```

Sentinel Monitor:
```json
{
  "status": "healthy",
  "service": "sentinel_monitor",
  "running": true,
  "events_monitored": 28311,
  "last_check": "2026-02-07T06:06:31.893360"
}
```

**Diagnostic Script:**
```bash
python3 scripts/diagnose_event_pipeline.py
```

---

## Usage

### Starting EventBridge

```bash
# Start the bridge
python3 Open_ELF/orchestrator/event_bridge.py start

# Check status
python3 Open_ELF/orchestrator/event_bridge.py status

# Stop the bridge
pkill -f event_bridge.py
```

### Monitoring Real-time

```bash
# Watch logs
tail -f Open_ELF/logs/event_bridge.log

# Watch for tool detection
grep "Tool detected" Open_ELF/logs/event_bridge.log

# Check heartbeat
cat .coordination/event-bridge-heartbeat.json
```

---

## Troubleshooting

### No Tool Events Captured

**Symptoms:**
- Dashboard shows no heuristics
- No trails created
- No pheromones deposited

**Diagnosis:**
```bash
# 1. Check if EventBridge is running
cat .coordination/event-bridge-heartbeat.json

# 2. Check logs for errors
tail -50 Open_ELF/logs/event_bridge.log

# 3. Run diagnostic
python3 scripts/diagnose_event_pipeline.py
```

**Solutions:**
1. **Restart EventBridge:**
   ```bash
   pkill -f event_bridge.py
   python3 Open_ELF/orchestrator/event_bridge.py start
   ```

2. **Verify OpenCode API:**
   ```bash
   curl http://localhost:4096/session
   ```

3. **Check hook permissions:**
   ```bash
   ls -la ~/.opencode/hooks/learning-loop/
   ```

### High Latency

**Issue:** Tools detected with delay or events missed

**Cause:** SSE connection timeout too aggressive

**Fix:** Update timeout settings to be >= 20 seconds:
```python
# In SSE client initialization
async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
    async with session.get(sse_url) as response:
        # Process SSE stream
        pass
```

### Memory Issues

**Issue:** EventBridge consuming too much memory

**Solution:** The `seen_messages` tracker can grow large. Restart periodically:
```bash
# Add to crontab for daily restart
0 0 * * * pkill -f event_bridge.py && python3 /path/to/event_bridge.py start
```

---

## Architecture History

### Previous Architecture (DEPRECATED)

**Plugin-based approach:**
```
OpenCode → ELF_superpowers.js → Direct Python hooks
```

**Issues:**
- Required manual plugin installation
- Version compatibility problems
- Complex configuration

### Current Architecture (ACTIVE)

**SSE-only API-based approach:**
```
OpenCode → SSE Stream → EventBridge → Hooks
```

**Advantages:**
- No plugin installation required
- Works with any OpenCode version
- More reliable and maintainable
- Better observability
- Real-time event delivery
- Reduced connection overhead (no polling)

**SSE-Only Benefits:**
- Single persistent connection
- Lower system resource usage
- No risk of connection storms from polling
- Better for system stability

---

## Future Improvements

1. **WebSocket Support:** Real-time bidirectional communication
2. **Database Direct Logging:** Bypass hooks for critical events
3. **Event Replay:** Store raw events for debugging
4. **Auto-recovery:** Restart on failure detection
5. **Metrics Export:** Prometheus/Grafana integration

---

## References

- **EventBridge Code:** `Open_ELF/orchestrator/event_bridge.py`
- **Hook Manager:** `Open_ELF/orchestrator/event_bridge.py:94` (HookManager class)
- **Diagnostic Script:** `scripts/diagnose_event_pipeline.py`
- **Incident Report:** `docs/INCIDENT-event-pipeline-failure-2026-02-06.md`
