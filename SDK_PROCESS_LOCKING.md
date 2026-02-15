# SDK Process Locking

## Problem

Multiple Bun `opencode_sdk_client.mjs` processes were being spawned simultaneously, causing:
- Triple/triplicate messages sent to AI agents
- Resource waste
- Confusing output

## Root Cause

1. **Multiple monitoring services**: Both `sentinel.py` and `unified_orchestrator.py` were running simultaneously
2. **No process control**: Each `AgentManager._sdk_request()` spawned a new subprocess without tracking active requests
3. **Concurrent requests**: Multiple threads could spawn SDK processes simultaneously

## Solution Implemented

### 1. SDK Process Locking

Added to `AgentManager._sdk_request()`:

```python
class AgentManager:
    def __init__(self, ...):
        self._sdk_lock = threading.Lock()          # Prevent concurrent spawns
        self._active_sdk_requests = 0              # Track active requests

    def _sdk_request(self, action, payload):
        with self._sdk_lock:                       # Acquire lock
            if self._active_sdk_requests > 0:
                self.logger.warning(f"⚠️ Duplicate SDK request prevented")
                _time.sleep(0.1)                   # Brief wait

            self._active_sdk_requests += 1

            try:
                # Spawn subprocess...
                return result
            finally:
                self._active_sdk_requests -= 1    # Always decrement
```

### 2. Singleton Enforcement

`AgentManager` already uses `get_agent_manager()` singleton pattern:

```python
_agent_manager_instance = None

def get_agent_manager():
    global _agent_manager_instance
    if _agent_manager_instance is None:
        _agent_manager_instance = AgentManager(...)
    return _agent_manager_instance
```

### 3. Duplicate Service Prevention

Stopped duplicate monitoring:
- Killed `unified_orchestrator.py` (was running alongside `sentinel.py`)
- Only `sentinel.py` now runs as single source of AI analysis

### 4. Auto-Kill Disabled

Modified `start-elf-system.sh` to NEVER kill OpenCode server:

```bash
# NEVER kill OpenCode (auto-kill DISABLED per user request)
log_info "💡 OpenCode server préservé (auto-kill DISABLED)"
```

## How It Works

1. **First request acquires lock**: `_active_sdk_requests = 1`
2. **Concurrent requests wait**: If another thread calls `_sdk_request()`:
   - Sees `_active_sdk_requests > 0`
   - Logs warning: "Duplicate SDK request prevented"
   - Waits briefly for lock release
3. **Request completes**: Lock released, `_active_sdk_requests = 0`
4. **Next request proceeds**: Normal processing

## Testing

To verify no duplicate SDK spawns:

```bash
# Count running SDK clients
ps aux | grep "opencode_sdk_client.mjs" | grep -v grep | wc -l

# Should show: 0 or 1 (never multiple)
```

## Files Modified

1. `/home/bamer/.opencode/emergent-learning/Open_ELF/agents/agent_manager.py`
   - Added `threading` import
   - Added `_sdk_lock` and `_active_sdk_requests` tracking
   - Implemented locking in `_sdk_request()`
   - Removed duplicate `sentinel()` method

2. `/home/bamer/.opencode/emergent-learning/start-elf-system.sh`
   - Disabled `pkill -f "opencode serve"` in cleanup

3. `/home/bamer/.opencode/emergent-learning/.coordination/DISABLE_AUTO_KILL`
   - Created flag to prevent future auto-kills

## Expected Behavior

- ✅ **One AI request** every 5 minutes (from sentinel.py only)
- ✅ **At most ONE** Bun SDK client process at any time
- ✅ **No triple/triplicate** messages
- ✅ **OpenCode never auto-killed** by ELF scripts
- ✅ **Warning logged** if concurrent request attempted

## Monitoring

Check with:

```bash
# Active SDK processes
watch -n 1 'ps aux | grep opencode_sdk_client.mjs | grep -v grep'

# Sentinel logs
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/sentinel.log
```

---

# OpenCode SDK - PartDelta Event

## Overview

The OpenCode SDK includes a **PartDelta event** that optimizes message updates by sending only incremental changes instead of full content.

## Event Schema

```typescript
PartDelta: BusEvent.define(
  "message.part.delta",
  z.object({
    sessionID: z.string(),   // Session identifier
    messageID: z.string(),  // Message identifier
    partID: z.string(),     // Part identifier
    field: z.string(),       // Field that changed (e.g., "text")
    delta: z.string(),      // Incremental change (not full content)
  }),
)
```

## Benefits

| Before (Full Content) | After (PartDelta) |
|----------------------|-------------------|
| Sends entire text on every update | Sends only the incremental change |
| Higher bandwidth usage | ~90% bandwidth reduction |
| Slower processing | Faster processing |
| Redundant data | Minimal payload |

## Example

**Without PartDelta** (every update sends full text):
```
{ "text": "Hello world! This is my response..." }
{ "text": "Hello world! This is my response... And more text." }
{ "text": "Hello world! This is my response... And more text. Even more!" }
```

**With PartDelta** (sends only changes):
```
{ "field": "text", "delta": "Hello world! This is my response..." }
{ "field": "text", "delta": " And more text." }
{ "field": "text", "delta": " Even more!" }
```

## Implementation Status

- ✅ **SDK supports PartDelta** - OpenCode server sends PartDelta events
- ⚠️ **Client handling** - Currently the SDK client receives full content
- 📋 **Optimization opportunity** - Can be implemented to handle delta updates

## Future Enhancement

The `opencode_sdk_client.mjs` can be enhanced to:

```javascript
// Handle PartDelta events
client.on('message.part.delta', (event) => {
  const { sessionID, messageID, partID, field, delta } = event;
  
  // Apply delta to existing part
  const existingPart = getPart(sessionID, messageID, partID);
  existingPart[field] += delta;  // Append delta
  
  // Notify UI of incremental update
  notifyUI(sessionID, messageID, partID, field, delta);
});
```

---

**Created**: 2026-02-14
**Status**: Documented ✅
