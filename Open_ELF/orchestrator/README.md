# ELF Unified Orchestrator Architecture

## Overview

The ELF (Emergent Learning Framework) uses a unified architecture with three main components:

1. **EventBridge** - Central event system (port 9998)
2. **UnifiedOrchestrator** - Service management and event processing
3. **Dashboard** - Web interface for monitoring and control

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EventBridge (9998)                    │
│  - Listens to OpenCode SSE events                       │
│  - Creates sessions                                     │
│  - Logs events to database                              │
│  - Manages listeners (UnifiedOrchestrator)              │
└────────────────────────┬────────────────────────────────┘
                         │ events
                         ▼
┌─────────────────────────────────────────────────────────┐
│              UnifiedOrchestrator                        │
│  - Receives events via register_listener()              │
│  - Manages services (Learning Capture, Watcher)         │
│  - Autoservices failed services                         │
│  - Escalates critical issues                            │
└────────────────────────┬────────────────────────────────┘
                         │ health status
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (8888)                     │
│  - Web UI for monitoring                                │
│  - API for creating missions                            │
│  - Displays service status                              │
└─────────────────────────────────────────────────────────┘
```

## Components

### EventBridge (`event_bridge.py`)

**Purpose:** Central event listener and session manager

**Key Features:**
- Listens to OpenCode Server (port 4096) SSE events
- Creates persistent sessions (one per day: `ELF Persistent Session - YYYY-MM-DD`)
- Logs all events to database (`memory/index.db`)
- Manages registered listeners (UnifiedOrchestrator, etc.)
- Runs ELF hooks in `.opencode/hooks/`

**API:**
- `POST http://localhost:9998/message` - Send message to session
- `GET http://localhost:9998/status` - Get status

**Status Response:**
```json
{
    "running": true,
    "events_processed": 534,
    "opencode_session_id": "ses_3cda...",
    "started_at": "2026-02-06T16:48:16.893557",
    "uptime_seconds": 302,
    "last_event_time": "2026-02-06T16:53:17.512309"
}
```

### UnifiedOrchestrator (`unified_orchestrator.py`)

**Purpose:** Service management and event processing

**Key Features:**
- Connects to running EventBridge (doesn't start its own)
- Registers listener for events: `tool`, `message`, `error`, `failure`, `service`, `health`
- Monitors service health every 10 ticks (100 seconds)
- Auto-restarts failed services:
  - **Learning Capture** - Monitors database for new events
  - **Watcher** - Monitors filesystem for changes
- Escalates critical issues

**Service Recovery:**
- ✅ Learning Capture: Kills existing, starts new via `background-learning-capture.py`
- ✅ Watcher: Kills existing, starts new via `sentinel/launcher.py`
- 🔴 EventBridge: Critical - cannot auto-recover (human intervention needed)

**Usage:**
```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python unified_orchestrator.py start
```

### Dashboard (`dashboard-app/`)

**Purpose:** Web interface for monitoring and control

**Key Features:**
- Web UI (port 8888)
- API endpoints for mission creation
- Service status display
- Event monitoring

**API:**
- `POST /api/v1/agents/run` - Create and execute mission
- `GET /api/v1/orchestrator/status` - Get service status
- `GET /api/v1/orchestrator/services` - Get detailed service info

## Database Schema

Event logs are stored in `memory/index.db`:

**Table: `event_chronicle`**
```sql
CREATE TABLE event_chronicle (
    id INTEGER PRIMARY KEY,
    event_type TEXT,
    source TEXT,
    source_id TEXT,
    summary TEXT,
    status TEXT,
    data TEXT,  -- JSON
    timestamp TEXT,
    created_at DATETIME
);
```

## Startup Sequence

### 1. Start EventBridge (REQUIRED FIRST)
```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python event_bridge.py start
```

**What happens:**
- Creates connection to OpenCode Server (port 4096)
- Creates persistent session (daily)
- Starts SSE event listener
- Registers status server (port 9998)
- Starts logging events to database

### 2. Start UnifiedOrchestrator (OPTIONAL)
```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
python unified_orchestrator.py start
```

**What happens:**
- Connects to EventBridge (port 9998)
- Registers as listener for events
- Starts event processor
- Monitors services every 10 ticks
- Auto-restarts failed services

### 3. Start Dashboard (OPTIONAL)
```bash
cd /home/bamer/.opencode/emergent-learning/dashboard-app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8888
```

**What happens:**
- Starts FastAPI backend (port 8888)
- Starts React frontend
- Provides Web UI at http://localhost:8888

## Service Management

### Learning Capture

**Purpose:** Monitors database for new events

**Location:** `scripts/background-learning-capture.py`

**Logs:** `Open_ELF/logs/learning-capture.log`

**Restart:** UnifiedOrchestrator auto-restarts if down

### Watcher

**Purpose:** Monitors filesystem for changes

**Location:** `sentinel/launcher.py`

**Logs:** `Open_ELF/logs/sentinel.log` (TODO: verify)

**Restart:** UnifiedOrchestrator auto-restarts if down

### EventBridge

**Purpose:** Central event system

**Location:** `orchestrator/event_bridge.py`

**Logs:** `Open_ELF/logs/event_bridge.log`

**Restart:** Manual intervention required (critical service)

## Event Flow

```
1. OpenCode Server emits SSE event
   ↓
2. EventBridge receives event
   ↓
3. EventBridge logs event to database
   ↓
4. EventBridge notifies registered listeners
   ↓
5. UnifiedOrchestrator receives callback
   ↓
6. UnifiedOrchestrator processes event
   ↓
7. If service event: trigger recovery action
   ↓
8. If other event: route to agent or log
```

## Monitoring

### Check EventBridge Status
```bash
curl http://localhost:9998/status | jq
```

### Check Latest Database Events
```bash
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db \
  "SELECT timestamp, source, summary FROM event_chronicle ORDER BY timestamp DESC LIMIT 5;"
```

### Check Service Status via Dashboard
```bash
curl http://localhost:8888/api/v1/orchestrator/status | jq
```

## Troubleshooting

### EventBridge not starting
- Check OpenCode Server is running (port 4096): `curl http://localhost:4096/`
- Check port 9998 is free: `lsof -i :9998`
- Check logs: `tail -100 Open_ELF/logs/event_bridge.log`

### UnifiedOrchestrator not connecting to EventBridge
- Verify EventBridge is running: `curl http://localhost:9998/status`
- Check UnifiedOrchestrator logs for connection errors

### Services not auto-restarting
- Verify UnifiedOrchestrator is running
- Check service health check logs in UnifiedOrchestrator
- Verify scripts exist and are executable

### Events not appearing in database
- Check EventBridge logs for import errors
- Verify database exists: `ls -la ./memory/index.db`
- Check event_logger.py is working

## Cleanup

### Remove old archived files
```bash
rm Open_ELF/orchestrator/enhanced_*.py
rm Open_ELF/orchestrator/*event_bridge_sdk.py
rm Open_ELF/test_enhanced_*.py
```

### Stop all services
```bash
pkill -f event_bridge.py
pkill -f unified_orchestrator.py
pkill -f background-learning-capture.py
pkill -f sentinel/launcher.py
```

## Development

### Adding a new listener to EventBridge

1. Create listener class/method
2. Call `bridge.register_listener()`:

```python
from orchestrator.event_bridge import EventBridge

bridge = EventBridge()

def my_callback(event_data: Dict):
    print(f"Received: {event_data}")

bridge.register_listener(
    listener_id="my_listener",
    callback=my_callback,
    event_types=["message", "tool"]
)
```

### Adding a new service to monitor

1. Add service to `_check_services_health()`
2. Add restart logic to `_handle_service_event()`
3. Add service to `get_services_status()`

## Architecture History

### Cleaned (2026-02-06)

**Before:**
- 3 versions of EventBridge (`event_bridge.py`, `enhanced_event_bridge.py`, `event_bridge_sdk.py`)
- Duplicate functionality
- Confusing documentation
- `register_listener()` not implemented

**After:**
- 1 unified EventBridge with full functionality
- UnifiedOrchestrator connects to EventBridge via `register_listener()`
- Clean separation of concerns
- Complete documentation

**Files removed:**
- `enhanced_event_bridge.py`
- `enhanced_event_bridge_sdk.py`
- `event_bridge_sdk.py`
- `test_enhanced_event_bridge.py`
- `enhanced_event_bridge_config.json`

## TODOs

- [ ] Add CEO agent integration for critical escalation
- [ ] Add incident ticket creation for critical issues
- [ ] Implement comprehensive health dashboard
- [ ] Add service auto-scaling based on load
- [ ] Add alert notification system (email, Slack)
- [ ] Implement backup and recovery for EventBridge session
- [ ] Add metrics and performance monitoring
