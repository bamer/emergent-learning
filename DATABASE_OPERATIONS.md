# Database Operations Guide

This document covers database operations, maintenance, and emergency procedures for the ELF system.

## Table of Contents

1. [Database Overview](#database-overview)
2. [Retention Policy](#retention-policy)
3. [Monitoring](#monitoring)
4. [Emergency Procedures](#emergency-procedures)
5. [Troubleshooting](#troubleshooting)

---

## Database Overview

### Location
- **Path**: `/home/bamer/.opencode/emergent-learning/memory/index.db`
- **Type**: SQLite3

### Key Tables

| Table | Description | Growth Rate |
|-------|-------------|-------------|
| `learnings` | Captured learnings from operations | Low (~10/day) |
| `heuristics` | Processed heuristics | Low (~1/day) |
| `golden_rules` | Elevated heuristics | Very low |
| `trails` | Activity trails | Medium (~1000/day) |
| `pheromone_trails` | Reinforced trails | Low (~10/day) |
| `metrics` | Event and performance metrics | **HIGH** (see below) |
| `event_chronicle` | Event history | Medium |

### Known Issues

#### Metrics Table Explosion (RESOLVED)

**Problem**: The `metrics` table accumulated 95,808 records in 1.5 days, growing from 179 MB to 643 MB.

**Root Cause**:
- High-frequency event logging: `message.part.updated` (20,485 records)
- No retention policy in place
- SQLite auto-vacuum not triggered

**Resolution Date**: 2026-02-12

---

## Retention Policy

### Implemented Policy

#### 1. Event Filtering (Source Control)

The EventBridge v2 filters high-frequency, low-value events before they are logged:

```python
# In core/event_bridge_v2.py
_FILTERED_EVENTS = {
    "message.part.updated",  # Internal UI updates - no analytical value
    "file.watcher.updated",  # Filesystem noise
}
```

**Filtered Events**:
- `message.part.updated`: Internal message part updates (20,485 records in 1.5 days)
- `file.watcher.updated`: Filesystem watcher events

#### 2. Automatic Cleanup (Retention Period)

Event metrics older than 6 hours are automatically deleted:

```python
def _cleanup_old_metrics(self):
    """Delete event metrics older than 6 hours."""
    DELETE FROM metrics WHERE metric_type = 'event' 
    AND timestamp < datetime('now', '-6 hours')
```

**Cleanup Details**:
- Runs every 5 minutes during session polling
- Automatically reclaims disk space
- Prevents unbounded growth

### Future Improvements

Consider implementing:
- Different retention periods for different metric types
- Archive-to-CSV before deletion for historical analysis
- Size-based triggers (e.g., vacuum at 100 MB)

---

## Monitoring

### Database Size

```bash
# Check current database size
ls -lh /home/bamer/.opencode/emergent-learning/memory/index.db

# Expected size: 50-100 MB (with retention policy)
```

### Growth Rate

Monitor for abnormal growth:
- Normal: < 1 MB/day
- Warning: > 10 MB/day
- Critical: > 100 MB/hour

### Table Sizes

```sql
-- Check largest tables
SELECT name, SUM(pgsize) as size_bytes 
FROM dbstat 
GROUP BY name 
ORDER BY size_bytes DESC 
LIMIT 10;
```

---

## Emergency Procedures

### Crisis: Database Growing Uncontrollably

#### Symptoms
- Database size doubling every few hours
- Disk space warning (less than 20% available)
- Slow system performance

#### Immediate Actions

**Step 1: Stop Services**
```bash
# Kill services holding database locks
pkill -f event_bridge_v2.py
pkill -f unified_orchestrator.py
pkill -f sentinel.py
sleep 2
```

**Step 2: Analyze Growth**
```bash
# Identify largest tables
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db \
  "SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY size_bytes DESC LIMIT 5;"
```

**Step 3: Emergency Cleanup**
```bash
# Delete all event metrics (safest option)
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db \
  "DELETE FROM metrics WHERE metric_type='event';"
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "VACUUM;"
```

**Step 4: Verify Space**
```bash
ls -lh /home/bamer/.opencode/emergent-learning/memory/index.db
# Should show significant reduction
```

**Step 5: Restart Services**
```bash
cd /home/bamer/.opencode/emergent-learning
python3 core/event_bridge_v2.py start &
python3 Open_ELF/orchestrator/unified_orchestrator.py start &
python3 core/sentinel.py &
```

### Check Disk Space

```bash
# Check available disk space
df -h /home/bamer/.opencode/emergent-learning

# Alert thresholds:
# Warning: < 20% free
# Critical: < 10% free
# Emergency: < 5% free
```

---

## Troubleshooting

### Database Locked

**Error**: `database is locked (5)`

**Cause**: Another process has an active connection

**Solution**:
```bash
# Find processes with open connections
lsof /home/bamer/.opencode/emergent-learning/memory/index.db

# Kill the processes
pkill -f event_bridge_v2.py
pkill -f unified_orchestrator.py
```

### Vacuum Not Reclaiming Space

**Cause**: Active connections preventing vacuum

**Solution**:
1. Stop all services
2. Run vacuum
3. Restart services

### Slow Queries

**Solution**:
```sql
-- Check for missing indexes
SELECT name FROM sqlite_master WHERE type='index';

-- Analyze query performance
EXPLAIN QUERY PLAN SELECT * FROM metrics WHERE metric_type='event';
```

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [COMMANDS.md](COMMANDS.md) - CLI commands
- [memory/heuristics/databaseoperations.md](memory/heuristics/databaseoperations.md) - Learned patterns

---

## Version

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Author**: CEO Agent (Level 3)
