# Legacy Code Cleanup & Trail Recording Fix
**Date:** 2026-02-10
**Session:** Janitor + Error Detective collaboration

---

## Executive Summary

Comprehensive cleanup operation to remove legacy code, fix critical bugs, and enforce coding standards across the ELF codebase.

## Changes Made

### 1. Legacy Code DELETED (Permanent)

Deleted all legacy files that were shadows of the new consolidated LearningProcessor:

| File | Status | Reason |
|------|--------|--------|
| `hooks/post_tool_use/post_tool_learning.py` | ✅ DELETED | Replaced by `core.learning_processor.py` |
| `hooks/post_tool_use/record_pheromone.py` | ✅ DELETED | Replaced by `core.learning_processor.py` |
| `archived_components/` (entire directory) | ✅ DELETED | No longer needed - full cleanup |

**Decision:** User explicitly requested permanent deletion without restoration path. Old consolidated code is entirely removed from the codebase.

### 2. LearningProcessor Import Bug Fixed

**Problem:** Import in `core/event_bridge_v2.py` was failing silently

```python
# BEFORE (WRONG):
from learning_processor import LearningProcessor, ToolEvent
logger.warning(f"⚠️ LearningProcessor not available: {e}")
```

**Fix:**
```python
# AFTER (CORRECT):
from core.learning_processor import LearningProcessor, ToolEvent
logger.error(f"❌ Failed to load LearningProcessor: {e}", exc_info=True)
```

**Location:** `core/event_bridge_v2.py`, lines 81-87

### 3. All Silent Catch Blocks Fixed

**Golden Rule Enforced:** Every error MUST be logged OR raised (never silently swallowed)

**Fixes Applied:**

| File | Lines Changed | Before | After |
|------|---------------|-------|-------|
| `core/event_bridge_v2.py` | 95, 479 | `except: pass` | `logger.error(..., exc_info=True)` |
| `core/learning_processor.py` | 100, 133, 293, 314, 495, 501, 503, 637, 705, 772, 930, 1011 | `print(...)` or `except: pass` | `logger.error(..., exc_info=True)` |
| `core/watcher.py` | 113, 123 | `except: logger.debug(...)` | `logger.error(..., exc_info=True)` |
| `core/monitoring_api.py` | 82, 89, 108, 132, 192 | `except: pass` or `print()` | `logger.error(..., exc_info=True)` |

**Pattern:**
```python
# BAD - silent error
try:
    something()
except Exception:
    pass

# GOOD - log the error
try:
    something()
except Exception as e:
    logger.error(f"Failed to do something: {e}", exc_info=True)

# GOOD - raise the error (with logging)
try:
    something()
except Exception as e:
    logger.error(f"Failed to do something: {e}", exc_info=True)
    raise
```

### 4. Unified Logger Enforcement

**Golden Rule Enforced:** Always use `Open_ELF.utils.elf_logging` for ALL logging

**Replaced ALL `print()` statements:**

| File | Changes | Details |
|------|---------|---------|
| `core/event_bridge_v2.py` | 3 statements | Errors → `logger.error()`, status info → `logger.info()` |
| `core/init_golden_rules.py` | 8 statements | All `print()` → `logger.info/warning/error/debug()` |
| `core/learning_processor.py` | 9 statements | All `print(..., file=sys.stderr)` → `logger.error(exc_info=True)` |

**Exception:** CLI final user output (e.g., "Done!", status display) still uses `print()` for user-facing output.

### 5. Trail Recording Bug Fixed

**Problem:** `trails_recorded: 0` when LearningProcessor called from EventBridge

**Root Cause:** Wrong data structure path from OpenCode events

```python
# BEFORE (WRONG):
tool_input = part.get("input", {})  # Empty dict!

# AFTER (CORRECT):
tool_input = part.get("state", {}).get("input", {})
```

**Locations:**
- Line 298: `_handle_message_part_updated_event()`
- Line 365: `_poll_sessions()`

**Result:** Trails now record correctly (`trails_recorded: 2` instead of `0`)

### 6. HTTP Connection Pooling Added

**Why:** `requests.Session()` is best practice for services making many requests

**Benefits:**
- Connection pooling reuses TCP connections
- Better performance (avoids TCP handshake overhead)
- Resource efficiency (reduces open file descriptors)
- Cookie persistence for session state

**Files Modified:**

**EventBridge (`core/event_bridge_v2.py`):**
```python
# Added to __init__:
self.http_session = requests.Session()
self.http_session.headers.update({
    'User-Agent': 'EventBridge-v2 ELF'
})

# Replaced all requests.get() with self.http_session.get()

# Added cleanup method:
def stop(self):
    """Stop the EventBridge and clean up resources."""
    logger.info("🛑 Stopping EventBridge...")
    self.running = False
    if hasattr(self, 'http_session'):
        self.http_session.close()
        logger.info("✅ HTTP session closed")
    logger.info("✅ EventBridge stopped")
```

**Watcher (`core/watcher.py`):**
```python
# Added to __init__:
self.http_session = requests.Session()
self.http_session.headers.update({
    'User-Agent': 'ELF-Watcher-v3'
})

# Updated check_service_health():
response = self.http_session.get(url, timeout=timeout)
```

### 7. Two New Golden Rules Recorded

**Rule #145 (infrastructure) - PROMOTED TO GOLDEN**

> "Always use the unified ELF logger (Open_ELF.utils.elf_logging) for ALL logging. NEVER use print() or exotic loggers."

- **Explanation:** Using print() defeats unified logging. The ELF logger ensures all logs go to the same location with consistent formatting and database tracking.
- **Confidence:** 1.0
- **Validations:** 10 (promoted automatically)

**Rule #146 (error-handling) - PROMOTED TO GOLDEN**

> "NEVER silently ignore errors. Every error MUST be either logged with the unified ELF logger OR raised (or both)."

- **Explanation:** Silently swallowing errors makes debugging impossible. Follow "ça marche ou ça crash" philosophy - handle errors properly or let the system crash visibly.
- **Confidence:** 1.0
- **Validations:** 10 (promoted automatically)

---

## Verification

### Imports Working ✅
```bash
✅ EventBridge imports and instantiates successfully
HTTP session type: <class 'requests.sessions.Session'>

✅ Watcher imports and instantiates successfully
HTTP session type: <class 'requests.sessions.Session'>

✅ LearningProcessor imports and instantiates successfully
```

### Trail Recording Working ✅
```json
// OLD:
{"trails_recorded": 0, ...}

// NEW:
{"trails_recorded": 2, ...}
```

### Database Counts ✅
```sql
 trails: 48 entries
 pheromone_trails: 6 entries
```

---

## Files Modified Summary

```
Modified (6 files):
  core/event_bridge_v2.py         - Import fix + logger + Session + trail fix
  core/learning_processor.py      - Logger fixes + error fixes
  core/watcher.py                 - Logger fix + Session
  core/monitoring_api.py          - Logger fixes
  core/init_golden_rules.py       - Logger fixes
  CHANGELOG.md                    - Documented changes

Deleted (3 files/dirs):
  hooks/post_tool_use/post_tool_learning.py
  hooks/post_tool_use/record_pheromone.py
  archived_components/ (entire directory)
```

---

## Related Documentation

- **CHANGELOG.md:** Full changelog entry for v0.5.7
- **memory/heuristics/infrastructure.md:** New golden rule #145
- **memory/heuristics/error-handling.md:** New golden rule #146
- **ARCHITECTURE.md:** Should reflect updated components

---

## Next Steps

None - all requested changes completed successfully.

The ELF codebase now:
- ✅ Has no legacy code
- ✅ Enforces unified logging everywhere
- ✅ Never ignores errors silently
- ✅ Records trails correctly
- ✅ Uses HTTP connection pooling for performance

---

*Generated by collaborative session: Janitor Agent + Error Detective*
