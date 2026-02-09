# Event Bridge Hook Integration

## Overview

The ELF learning loop hooks are now integrated with the **event_bridge** system, which listens to OpenCode SSE (Server-Sent Events) and triggers hooks automatically.

## Architecture

### Event Flow

```
┌─────────────────────────────────────────────────────────┐
│                     OpenCode AI                         │
│                 (User executes tool)                    │
└───────────────────┬─────────────────────────────────────┘
                    │ SSE Event
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Event Bridge (event_bridge.py)              │
│            • Listens on SSE port (4096)                 │
│            • Parses tool completion events              │
│            • Triggers hooks via HookManager             │
└───────────────────┬─────────────────────────────────────┘
                    │ run_hook("PostToolUse", data)
                    ▼
┌─────────────────────────────────────────────────────────┐
│           HookManager (finds hooks to execute)          │
│  1. hooks/PostToolUse/                                  │
│  2. hooks/posttooluse/                                   │
│  3. hooks/post_tool_use/ ← Found! ✅                    │
└───────────────────┬─────────────────────────────────────┘
                    │ Executes all *.py with data via stdin
                    ▼
┌─────────────────────────────────────────────────────────┐
│      hooks/post_tool_use/*.py (all scripts run)          │
│  • record_pheromone.py → pheromone_trails table        │
│  • post_tool_learning.py → trails table                │
│  • sync-golden-rules.py → golden rule sync             │
│  • trail_helper.py → helper functions                  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Database (memory/index.db)                 │
│  • trails (transient, per-access)                      │
│  • pheromone_trails (aggregated, per-file)             │
└─────────────────────────────────────────────────────────┘
```

## Hook Discovery

The `HookManager.run_hook()` method automatically discovers hooks in this order:

1. **Exact match**: `hooks/PostToolUse/`
2. **Lowercase**: `hooks/posttooluse/`
3. **Snake_case**: `hooks/post_tool_use/` ← **FOUND!**

This means hooks should be placed in `/home/bamer/.opencode/emergent-learning/hooks/post_tool_use/` for automatic discovery.

## Payload Format

### Event Bridge (current active system)

```json
{
  "event_type": "PostToolUse",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/path/to/file.txt"
  },
  "tool_output": {
    "content": "file content"
  },
  "success": true,
  "session_id": "session_abc123",
  "timestamp": "2026-02-09T13:00:00"
}
```

**Key differences:**
- Payload key: `tool_input` (not `input`)
- Delivered via: **stdin** (not command-line args)
- Additional fields: `session_id`, `success`

### ELF_superpowers.js (legacy, deactivated)

```json
{
  "input": {
    "file_path": "/path/to/file.txt"
  },
  "output": {
    "content": "file content"
  },
  "tool_name": "Read"
}
```

## Input Method Compatibility

Hooks support both input methods for backward compatibility:

```python
def get_hook_input() -> dict:
    """Read hook input from stdin or command-line argument."""

    # Try stdin first (event_bridge)
    context = None
    try:
        if not sys.stdin.isatty():
            context_str = sys.stdin.read()
            if context_str:
                context = json.loads(context_str)
    except (json.JSONDecodeError, IOError):
        pass

    # Fallback to command-line argument (superpowers.js compatibility)
    if context is None and len(sys.argv) >= 2:
        try:
            context = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            return {}

    return context if context else {}
```

## Hook Files

### Primary Active Hooks

Location: `/home/bamer/.opencode/emergent-learning/hooks/post_tool_use/`

| File | Purpose | Database Table |
|------|---------|----------------|
| `record_pheromone.py` | Aggregated file access tracking | `pheromone_trails` |
| `post_tool_learning.py` | Transient trail recording | `trails` |
| `trail_helper.py` | Helper functions for trails | N/A |
| `sync-golden-rules.py` | Sync golden rules | `heuristics` |

### Secondary/Legacy Directories

- `/home/bamer/.opencode/emergent-learning/hooks/learning-loop/` (archived)
- `/home/bamer/.opencode/hooks/PostToolUse/` (backup)

## Creating New Hooks

### Step 1: Create Hook File

```bash
# Create in the hooks/post_tool_use/ directory
cat > hooks/post_tool_use/my_custom_hook.py << 'HOOK'
#!/usr/bin/env python3
"""Custom hook for..."""
import json
import sys
from pathlib import Path

def main():
    # Read input from stdin (event_bridge) or CLI args (legacy)
    if not sys.stdin.isatty():
        context = json.loads(sys.stdin.read())
    elif len(sys.argv) >= 2:
        context = json.loads(sys.argv[1])
    else:
        return 0

    tool_name = context.get("tool_name", "")
    tool_input = context.get("tool_input") or context.get("input", {})

    # Your custom logic here
    print(f"Hook executed for tool: {tool_name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
HOOK

# Make executable
chmod +x hooks/post_tool_use/my_custom_hook.py
```

### Step 2: Test Hook

```bash
# Test with stdin (event_bridge format)
echo '{"tool_name":"Read","tool_input":{"file_path":"/test.txt"}}' | \
  python3 hooks/post_tool_use/my_custom_hook.py

# Test with CLI args (legacy format)
python3 hooks/post_tool_use/my_custom_hook.py \
  '{"input":{"file_path":"/test.txt"},"tool_name":"Read"}'
```

### Step 3: Deploy

- No additional steps needed!
- The HookManager will automatically discover and run all `.py` files in `post_tool_use/`

## Testing Hooks

### Manual Test

```bash
# Simulate event_bridge payload
cat > test_hook.py << 'PY'
import subprocess, json

payload = {
    "event_type": "PostToolUse",
    "tool_name": "Read",
    "tool_input": {"file_path": "/home/bamer/emergent-learning/README.md"},
    "tool_output": {"content": "..."},
    "success": True,
    "session_id": "test",
    "timestamp": "2026-02-09T13:00:00"
}

result = subprocess.run(
    ["python3", "hooks/post_tool_use/record_pheromone.py"],
    input=json.dumps(payload),
    capture_output=True,
    text=True
)

print(result.stderr)
PY

python3 test_hook.py
```

### Integration Test

The hooks are automatically tested every time you execute a tool in OpenCode. Check the database to verify results:

```bash
sqlite3 memory/index.db "SELECT * FROM pheromone_trails ORDER BY last_access DESC LIMIT 10;"
```

## Monitoring Tools

### Live Monitoring

```bash
# Check both trail systems
bash /home/bamer/.opencode/emergent-learning/scripts/monitor-trails.sh
```

### Event Bridge Logs

```bash
# Check event_bridge status
tail -100 /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log

# Check if hooks are being called
grep -i "hook\|pheromone" /home/bamer/.opencode/emergent-learning/Open_ELF/logs/event_bridge.log
```

### Direct Database Queries

```bash
# Pheromone hotspots
sqlite3 memory/index.db << 'SQL'
.mode box
SELECT 
  substr(file_path, -30) as file,
  tool_name,
  access_count,
  datetime(last_access) as last
FROM pheromone_trails
ORDER BY access_count DESC
LIMIT 10;
SQL

# Recent trails
sqlite3 memory/index.db << 'SQL'
.mode box
SELECT 
  substr(location, -35) as file,
  scent,
  strength,
  created_at
FROM trails
ORDER BY created_at DESC
LIMIT 10;
SQL
```

## Troubleshooting

### Hook Not Running?

1. **Check file location:**
   ```bash
   ls -la hooks/post_tool_use/
   # Hook files must be in this directory
   ```

2. **Check file permissions:**
   ```bash
   chmod +x hooks/post_tool_use/your_hook.py
   ```

3. **Check hook syntax:**
   ```bash
   python3 -m py_compile hooks/post_tool_use/your_hook.py
   ```

4. **Test directly:**
   ```bash
   echo '{"tool_name":"test"}' | python3 hooks/post_tool_use/your_hook.py
   ```

### Database Not Updating?

1. **Check database exists:**
   ```bash
   ls -la memory/index.db
   ```

2. **Check database integrity:**
   ```bash
   sqlite3 memory/index.db "PRAGMA integrity_check;"
   ```

3. **Check hook stderr output:**
   ```bash
   # Test and capture stderr
   echo '{"tool_name":"Read"}' | python3 hooks/post_tool_use/record_pheromone.py 2>&1
   ```

### Event Bridge Issues?

1. **Check if event_bridge is running:**
   ```bash
   ps aux | grep event_bridge | grep -v grep
   ```

2. **Check event_bridge status:**
   ```bash
   curl -s http://localhost:9998/status | jq .
   ```

3. **Restart event_bridge:**
   ```bash
   cd /home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator
   # Kill existing and restart
   pkill -f event_bridge.py
   python3 event_bridge.py start > logs/event_bridge.log 2>&1 &
   ```

## Migration from ELF_superpowers.js

### What Changed

| Aspect | ELF_superpowers.js (Old) | Event Bridge (New) |
|--------|------------------------|-------------------|
| **Activation** | Plugin system | SSE listener |
| **Hook Location** | `hooks/learning-loop/` | `hooks/post_tool_use/` |
| **Input Delivery** | Command-line args | stdin |
| **Payload Key** | `input` | `tool_input` |
| **Hook Discovery** | Explicit calls | Automatic `*.py` discovery |

### Migration Checklist

- [x] Copy hooks to `hooks/post_tool_use/`
- [x] Update input reading to support stdin
- [x] Support both `tool_input` and `input` keys
- [x] Test with event_bridge payload format
- [x] Verify database recording
- [x] Update documentation

### Code Changes Required

Only for hook creation, not for existing working hooks:

```python
# Before (superpowers.js only)
context = json.loads(sys.argv[1])
tool_input = context.get("input", {})

# After (compatible with both)
if not sys.stdin.isatty():
    context = json.loads(sys.stdin.read())
elif len(sys.argv) >= 2:
    context = json.loads(sys.argv[1])

tool_input = context.get("tool_input") or context.get("input", {})
```

## Current Status

✅ **Production Ready**

- Event bridge: Running and processing events
- Hooks: Discovered and executing automatically
- Database: Recording to both trail systems
- Compatibility: Backward compatible with legacy format

**Last Updated:** Feb 9, 2026
**Architecture:** Event Bridge + HookManager
**Active Hooks:** 4 scripts in `hooks/post_tool_use/`
