# Pheromone Trails Integration Guide

## Overview

The ELF system uses **two complementary trail systems** to track file access patterns:

1. **`trails`** - Transient, per-access tracking (🕸️)
2. **`pheromone_trails`** - Aggregated, per-file statistics (🐜)

## Trail System Comparison

### 🕸️ `trails` Table (Transient)

**Purpose:** Track individual file operations with metadata

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `run_id` | Links to workflow execution |
| `location` | File path, function, or concept |
| `location_type` | Type: file, function, class, concept, tag |
| `scent` | Discovery, warning, blocker, hot, cold |
| `strength` | 0.0-1.0, indicates trail intensity |
| `agent_id` | Which agent created the trail |
| `node_id` | Which workflow node |
| `message` | Optional description |
| `tags` | Comma-separated metadata |
| `created_at` | When trail was created |
| `expires_at` | When trail should expire |

**Usage:**
- Records each file access individually
- Tracks outcomes (success/failure/warning)
- Used for collaborative hotspot analysis
- Transient - trails can decay or expire

### 🐜 `pheromone_trails` Table (Persistent)

**Purpose:** Aggregate statistics per file over time

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `file_path` | Unique file identifier |
| `tool_name` | Tool type: Read, Edit, Bash, Grep, etc. |
| `access_count` | Total number of accesses |
| `first_access` | When file was first accessed |
| `last_access` | Most recent access timestamp |
| `total_weight` | Cumulative weight (access_count) |

**Usage:**
- Aggregates access counts per file
- Persistent statistics
- Identifies hotspots by access frequency
- Used for adaptive caching, prioritization

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ELF_superpowers.js                   │
│                  Post-tool hook trigger                 │
└──────────────┬────────────────────────┬─────────────────┘
               │                        │
               ▼                        ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ post_tool_learning.py│  │record_pheromone.py   │
    │                      │  │                      │
    │ ──► lay_trails()     │  │ ──► record_trail()   │
    │      (transient)     │  │      (aggregated)    │
    └──────────┬───────────┘  └──────────┬───────────┘
               │                        │
               ▼                        ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │      trails table    │  │   pheromone_trails   │
    │   (47 records)       │  │    (6 records)       │
    └──────────────────────┘  └──────────────────────┘
```

## Data Flow

### For each tool execution:

1. **superpowers.js** fires `tool.execute.after` hook
2. **Two parallel processes**:
   - `post_tool_learning.py` → `lay_trails()` → `trails` table
   - `record_pheromone.py` → `record_trail()` → `pheromone_trails` table

### Payload Structure (from ELF_superpowers.js):

```json
{
  "input": {
    "tool": "Read",
    "file_path": "/path/to/file.txt"
  },
  "output": {
    "content": "..."
  },
  "tool_name": "Read"
}
```

## Recent Fixes (Feb 9, 2026)

### Problem
`record_pheromone.py` was failing silently because:
1. Expected `tool_input` key, but received `input` from superpowers.js
2. Only handled string inputs, but superpowers.js sends dict objects
3. No error logging for debugging

### Solution

**1. Fixed payload handling:**
```python
# Before
tool_input = context.get("tool_input", "")

# After  
tool_input_data = context.get("input") or context.get("tool_input", {})
```

**2. Updated path extraction:**
```python
# Now handles both dict and string inputs
def extract_file_paths(tool_name: str, tool_input) -> list:
    if isinstance(tool_input, dict):
        # Extract from superpowers.js dict format
        if tool_name in ["Read", "read"]:
            path_str = tool_input.get("file_path", "")
        elif tool_name in ["Edit", "edit", "Write", "write"]:
            path_str = tool_input.get("file_path") or tool_input.get("filePath", "")
        # ...
```

**3. Added debug logging:**
```python
sys.stderr.write(f"[PHEROMONE] 🚀 Processing: {tool_name}\n")
sys.stderr.write(f"[PHEROMONE] 📋 Extracted {len(file_paths)} file paths\n")
sys.stderr.write(f"[PHEROMONE] 📊 Recorded {recorded_count}/{len(file_paths)} trails\n")
```

## Monitoring Tools

### Live monitoring:

```bash
bash /home/bamer/.opencode/emergent-learning/scripts/monitor-trails.sh
```

### Query trails directly:

```sql
-- Recent pheromone trails
SELECT file_path, tool_name, access_count, last_access
FROM pheromone_trails
ORDER BY last_access DESC
LIMIT 10;

-- Top hotspots
SELECT file_path, tool_name, access_count
FROM pheromone_trails
ORDER BY access_count DESC
LIMIT 10;

-- Usage by tool
SELECT tool_name, COUNT(*) as files, SUM(access_count) as total
FROM pheromone_trails
GROUP BY tool_name
ORDER BY total DESC;
```

## Use Cases

### Hotspot Analysis
```python
# Find files accessed 10+ times
sql = """
SELECT file_path, access_count
FROM pheromone_trails
WHERE access_count >= 10
ORDER BY access_count DESC
"""
```

### Adaptive Caching
```python
# Prioritize heavily accessed files
if access_count > threshold:
    cache_file(file_path)
```

### Collaboration Patterns
```python
# Find files touched by multiple tools
sql = """
SELECT file_path, COUNT(DISTINCT tool_name) as tool_variety
FROM pheromone_trails
GROUP BY file_path
HAVING tool_variety > 2
ORDER BY access_count DESC
"""
```

### Recent Interest Tracking
```python
# Find files accessed in last hour
sql = """
SELECT file_path, tool_name, last_access
FROM pheromone_trails
WHERE last_access > datetime('now', '-1 hour')
"""
```

## Testing

### Manual test:

```bash
cd /home/bamer/.opencode/emergent-learning/hooks/learning-loop

# Test Read operation
python3 -c "
import json, subprocess
payload = {
    'tool_name': 'Read',
    'input': {'file_path': '/home/bamer/.opencode/emergent-learning/README.md'}
}
subprocess.run(['python3', 'record_pheromone.py', json.dumps(payload)],
             capture_output=True)
"
```

### Integration test:

```bash
bash /tmp/verify_pheromone_integration.sh
```

## Debug Logging

When pheromone recording is active, you'll see logs like:

```
[PHEROMONE] 🚀 Processing: Read
[PHEROMONE] Input type: dict
[PHEROMONE] 📋 Extracted 1 file paths
[PHEROMONE] ✅ Recorded: /path/to/file.txt (Read)
[PHEROMONE] 📊 Recorded 1/1 trails
```

## Troubleshooting

### No trails being recorded?

1. Check if script is being called:
   ```bash
   # Look for pheromone logs
   grep "PHEROMONE" /tmp/*.log
   ```

2. Verify database connectivity:
   ```bash
   sqlite3 memory/index.db "SELECT COUNT(*) FROM pheromone_trails;"
   ```

3. Test script directly:
   ```bash
   cd hooks/learning-loop
   python3 record_pheromone.py '{"tool_name":"Read","input":{"file_path":"/test.txt"}}'
   ```

### Silent failures?

The script now logs all errors to stderr:
```
[PHEROMONE] ❌ Failed to record /path/to/file: Database locked
```

## Future Enhancements

1. **Trail Decay:** Implement time-based weight decay for `trails` table
2. **Correlation:** Link `trails` and `pheromone_trails` via file path
3. **Visualization:** Dashboard charts showing access patterns
4. **Predictive:** ML model for predicting future file access
5. **Optimization:** Use pheromone data for caching strategies

## Summary

- **`trails`** = Detailed, transient, per-access (🕸️)
- **`pheromone_trails`** = Aggregated, persistent, per-file (🐜)
- Both serve different purposes and complement each other
- Integration fixed on Feb 9, 2026
- Use `monitor-trails.sh` for real-time monitoring
