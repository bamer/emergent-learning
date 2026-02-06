# 🔴 CRITICAL ISSUE: Event Pipeline Failure

## Status: **ACTIVE INCIDENT**
**Date:** 2026-02-06
**Impact:** Complete loss of event capture, heuristics, trails, and pheromones
**Severity:** HIGH

---

## Problem Summary

The monitoring system has stopped recording ALL agent activities. Despite 8 agents actively working:
- ❌ No tool events captured
- ❌ No heuristics recorded
- ❌ No trails created
- ❌ No pheromones deposited
- ❌ No learning occurring

---

## Root Cause Analysis

### 1. **Missing Tool Events from OpenCode SSE Stream**

The EventBridge (`event_bridge.py`) listens to OpenCode's SSE endpoint at `http://localhost:4096/event`.

**Expected events:**
- `message.part.updated` ✅ (15,059 events - WORKING)
- `message.updated` ✅ (335 events - WORKING)
- `server.heartbeat` ✅ (183 events - WORKING)
- `session.updated` ✅ (174 events - WORKING)
- **`tool`** ❌ (0 events - **MISSING!**)

**Evidence:**
```json
{
  "events_processed": 15990,
  "event_stats": {
    "message.part.updated": 15059,
    "message.updated": 335,
    "server.heartbeat": 183,
    "session.updated": 174,
    "session.status": 138
    // NO TOOL EVENTS!
  }
}
```

### 2. **EventBridge Polling Not Detecting Tools**

The `_poll_sessions()` method (line 392) polls sessions every 30 seconds to detect tools via message parts.

**Current behavior:**
- Polls `/session` endpoint
- Checks message parts for `type: "tool_use"`
- Should trigger `PostToolUse` hooks

**Problem:** Not detecting tools in production despite logic being correct.

### 3. **No Direct Plugin Integration**

The previous `ELF_superpowers.js` plugin that directly hooked into OpenCode's tool execution has been removed.

**Previous architecture (DEPRECATED):**
```
OpenCode Plugin → Direct hooks → Python scripts
```

**Current architecture (BROKEN):**
```
OpenCode SSE → EventBridge → HookManager
                        ↓
              (No tool events received)
```

---

## Impact Assessment

| System | Status | Impact |
|--------|--------|--------|
| EventBridge | 🟡 Running | Receives non-tool events only |
| HookManager | 🔴 Non-functional | Never triggered for tools |
| Heuristics | 🔴 Not recording | No learning occurring |
| Trails | 🔴 Not creating | No pheromone trails |
| Golden Rules | 🔴 Not syncing | Rules outdated |
| Dashboard | 🟡 Displaying | Showing stale data |

---

## Files Involved

### Core Event System
- `/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge.py` - Main event processor
- `/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator/event_bridge_config.json` - Configuration
- `/home/bamer/.opencode/emergent-learning/.coordination/event-bridge-heartbeat.json` - Status file

### Hook Processing
- `/home/bamer/.opencode/emergent-learning/hooks/learning-loop/post_tool_learning.py` - Records heuristics
- `/home/bamer/.opencode/emergent-learning/hooks/learning-loop/record_pheromone.py` - Records pheromones
- `/home/bamer/.opencode/emergent-learning/hooks/PreToolUse/semantic-memory.py` - Pre-tool processing
- `/home/bamer/.opencode/hooks/PostToolUse/post_tool_learning.py` - Runtime hook

### Monitoring
- `/home/bamer/.opencode/emergent-learning/Open_ELF/agents/sentinel_monitor.py` - Dashboard sentinel
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/backend/routers/monitoring.py` - API

---

## Immediate Actions Required

### Option 1: Fix SSE Event Types (RECOMMENDED)

**Problem:** OpenCode doesn't emit `tool` type events in SSE stream.

**Investigate:**
1. Check OpenCode version and configuration
2. Verify if tool events are logged to SSE
3. Check if there's a different event type for tools
4. Look for `tool.execute.before` or `tool.execute.after` in SSE

### Option 2: Enhance Polling Mechanism

**Current:** 30-second polling interval

**Proposed changes:**
```python
# In event_bridge.py, line 463
time.sleep(5)  # Reduce from 30 to 5 seconds

# Add better logging in _poll_sessions
def _poll_sessions(self):
    _log_info("🔄 Starting session polling (interval: 5s)...")
    # ... existing code with enhanced logging
```

### Option 3: Restore Direct Hook Integration

Create a minimal hook system that doesn't rely on SSE:

```python
# New file: direct_tool_monitor.py
"""
Direct tool monitoring via OpenCode API polling.
Bypasses SSE limitations by checking active sessions directly.
"""

import requests
import time
from datetime import datetime

class DirectToolMonitor:
    def __init__(self, api_base="http://localhost:4096"):
        self.api_base = api_base
        self.last_check = datetime.now()
        
    def check_for_new_tools(self):
        """Check sessions for new tool executions."""
        response = requests.get(f"{self.api_base}/session")
        sessions = response.json()
        
        for session in sessions:
            session_id = session.get("id")
            messages = requests.get(
                f"{self.api_base}/session/{session_id}/message"
            ).json()
            
            for msg in messages:
                created_at = msg.get("info", {}).get("created_at")
                if created_at and created_at > self.last_check:
                    # New message - check for tools
                    parts = msg.get("parts", [])
                    for part in parts:
                        if part.get("type") == "tool_use":
                            self._trigger_hooks(part, session_id)
                            
        self.last_check = datetime.now()
```

### Option 4: Database-Level Logging

Add direct database logging in EventBridge:

```python
# In event_bridge.py, modify _handle_tool_event()
def _handle_tool_event(self, event):
    # ... existing code ...
    
    # Direct database logging
    if EVENT_LOGGER_AVAILABLE:
        log_event(
            event_type="tool_execution",
            tool_name=tool_name,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            success=success
        )
```

---

## Verification Steps

After applying fixes, verify with:

```bash
# 1. Check EventBridge status
cat .coordination/event-bridge-heartbeat.json

# 2. Monitor logs in real-time
tail -f Open_ELF/logs/event_bridge.log

# 3. Check for tool events
grep "Tool detected" Open_ELF/logs/event_bridge.log

# 4. Verify hooks are running
ps aux | grep post_tool_learning

# 5. Check database for new records
sqlite3 memory/index.db "SELECT COUNT(*) FROM trails WHERE created_at > datetime('now', '-1 hour');"
```

---

## Long-term Solutions

1. **Implement dual event capture:**
   - SSE for real-time events
   - API polling for tool detection
   - Database triggers as fallback

2. **Add health checks:**
   - Monitor event count per minute
   - Alert if no tool events for 5 minutes
   - Auto-restart EventBridge if stalled

3. **Create event backup:**
   - Log all raw SSE events to file
   - Enable replay for debugging
   - Store in memory/index.db

---

## Notes

- **Last known working:** Unknown (issue discovered 2026-02-06)
- **Agents affected:** All 8 active agents
- **Data loss:** All events since failure began
- **Recovery:** Manual intervention required

**Next Action:** Implement Option 2 (enhanced polling) as immediate fix, then investigate Option 1 (SSE event types) for long-term solution.
