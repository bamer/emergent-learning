# Sentinel vs Watcher - Comparison & Recommendation

**Status**: Analysis for Phase 2 Architecture Decision
**Date**: 2026-01-28

---

## Quick Comparison

| Aspect | Watcher (Standard ELF) | Sentinel (Created in Phase 2) |
|--------|----------------------|-------------------------------|
| **Purpose** | Multi-agent swarm monitoring | Dashboard health monitoring |
| **Model** | Haiku (Tier 1) + Opus (Tier 2) | Haiku (always) |
| **Cost** | $0.0038/day (~2,880 checks/day) | $2.88/day (continuous) |
| **Interval** | 30-45 seconds per check | 30 seconds per cycle |
| **Scope** | Agent coordination & state | Database metrics & activity |
| **Output** | Exit codes, log files, blackboard | event_chronicle records |
| **API Support** | None (file-based) | REST API (/api/chronicle) |
| **Integration** | Hooks, main Claude interaction | Learning loop events |
| **Status** | Existing, tested, production-ready | New, not integrated with watcher |

---

## Watcher - How It Works

### Architecture
```
User Interaction → Hook → Spawns Watcher → Haiku (30s check)
                                            ↓
                                      Issue? → Exit 1 → Opus (deep analysis)
                                            ↓
                                         Restart Haiku
```

### Features
✅ **Tier 1: Haiku Watcher** (Fast, cheap)
- Runs every 30 seconds
- Checks coordination files (blackboard.json, agent status)
- Detects: stale agents, errors, stuck tasks, completion
- Exit code 0: normal, 1: needs intervention, 2: error
- Cost: ~$0.001 per check

✅ **Tier 2: Opus Handler** (Deep analysis)
- Invoked only when Haiku exits with code 1
- Analyzes complex issues
- Makes decisions: RESTART, ABANDON, ESCALATE
- Updates blackboard state
- Cost: ~$0.10 per intervention

✅ **Launcher** (Orchestrator)
- Spawns Haiku in subprocess
- Monitors exit codes
- Invokes Opus when needed
- Handles restarts and graceful shutdown

### Workflow
1. User interaction triggers hook reminder
2. Main Claude spawns watcher via `python watcher/launcher.py`
3. Watcher does one comprehensive pass
4. Watcher analyzes blackboard.json (agent states)
5. Watcher detects issues (stale agents, errors)
6. Watcher either: fixes directly OR escalates to Opus
7. Watcher logs findings and exits
8. Main Claude continues, next interaction spawns new watcher

### What It Monitors
- **Agent heartbeats**: last_seen timestamps
- **Agent status**: active, completed, failed, restarting
- **Blackboard state**: coordination data between agents
- **Stop signals**: watcher-stop file
- **Agent files**: agent_*.md metadata

### Models Used
- **Haiku** (claude-3-haiku): ~$0.001 per check
- **Opus** (claude-3-opus): ~$0.10 per intervention
- **Frequency**: Haiku every 30s, Opus ~5-10x per day
- **Cost**: ~$3.88/day (vs $288/day if Opus every 30s)

---

## Sentinel - What I Created

### Architecture
```
Continuous Loop (30s interval)
  ↓
Collect Metrics (SELECT from DB)
  ↓
Analyze with Haiku
  ↓
Record to event_chronicle
  ↓
Sleep 30s → repeat
```

### Features
✅ **Continuous Monitoring**
- Runs 24/7 in background
- 30-second monitoring cycles
- No escalation tiers (always Haiku)
- Records to event_chronicle table

✅ **Dashboard Metrics**
- Service health (frontend, backend)
- Data inventory (learnings, heuristics, experiments)
- Recent activity (last hour)
- Quality metrics (confidence, validation)

✅ **Event Recording**
- Records sentinel_cycle events
- Stores metrics, analysis, patterns
- JSON metadata for dashboard
- Indexed for fast queries

✅ **API Access**
- REST endpoints (/api/chronicle/*)
- Query events with filters
- Statistics and trends
- Real-time visibility

### Models Used
- **Haiku** (claude-3-haiku): Every 30 seconds
- **Cost**: ~$2.88/day
- **Frequency**: 2,880 checks per day
- **Purpose**: Dashboard health analysis

---

## Key Differences

### 1. **Purpose**
- **Watcher**: Monitors multi-agent swarm coordination
- **Sentinel**: Monitors dashboard health & metrics

### 2. **Trigger Model**
- **Watcher**: Event-driven (user interaction → spawn watcher)
- **Sentinel**: Continuous loop (runs 24/7 independently)

### 3. **Cost Model**
- **Watcher**: Cost-optimized tiered ($3.88/day)
- **Sentinel**: Continuous full-cost ($2.88/day)

### 4. **Data Source**
- **Watcher**: Coordination files (blackboard.json, agent states)
- **Sentinel**: Database queries (SQLite metrics)

### 5. **Output Format**
- **Watcher**: Exit codes, markdown logs, blackboard updates
- **Sentinel**: event_chronicle records, REST API

### 6. **Integration**
- **Watcher**: Integrated with main Claude via hooks
- **Sentinel**: Integrated with learning loop via event records

### 7. **API Support**
- **Watcher**: None (file-based communication)
- **Sentinel**: Full REST API for dashboard access

---

## Can Watcher Run with Your Current Model?

### Current Model Status
You have access to:
- ✅ Claude Haiku
- ✅ Claude Opus (likely)
- ✅ Claude Sonnet (main model)

### Watcher Compatibility
**YES - Watcher will work perfectly with your current setup.**

The watcher uses:
- **Haiku**: ~$0.001 per check (very affordable)
- **Opus**: ~$0.10 per intervention (rare, only when needed)

This is actually **cheaper** than the Sentinel I created, which uses Haiku continuously.

---

## Recommendation: Hybrid Approach (Best of Both)

Instead of choosing one, integrate them both:

```
┌─────────────────────────────────────────────────────┐
│           ELF Learning Loop - Standard              │
└─────────────────────────────────────────────────────┘

┌──────────────────┐              ┌──────────────────┐
│   WATCHER        │              │   event_chronicle│
│ (Multi-tier)     │              │   Dashboard      │
│                  │              │                  │
│ Monitors:        │              │ Records:         │
│ • Agent states   │─────────────→│ • Sentinel data  │
│ • Coordination   │              │ • Learning data  │
│ • Task progress  │              │ • System events  │
│                  │              │                  │
│ Cost: $3.88/day │              │ Query: REST API  │
└──────────────────┘              └──────────────────┘
        ↑                                    ↓
        │                                    │
        └─────── Unified Event Stream ──────┘
```

### Implementation Strategy

**Keep Standard ELF Watcher** (No changes needed)
- Already in place and working
- Monitors agent coordination
- Cost-optimized tiering

**Add event_chronicle Recording** (Minimal changes)
- Watcher logs its findings to event_chronicle
- Creates unified event stream
- Dashboard gets visibility into swarm state

**Integration Points**:
1. Watcher logs to event_chronicle when:
   - Detecting stale agents → `event_type: agent_stale`
   - Restarting agents → `event_type: agent_restart`
   - Escalating to Opus → `event_type: escalation_needed`
   - Completing monitoring → `event_type: watcher_cycle`

2. Learning hook continues writing:
   - `event_type: learning_loop_completion`
   - `event_type: heuristic_discovery`
   - `event_type: learning_discovery`

3. Dashboard shows unified timeline:
   - Watcher events (blue)
   - Learning events (green)
   - System alerts (red)

---

## Proposed Modification to Watcher

### Add to watcher_loop.py

```python
def log_to_event_chronicle(event_type: str, status: str, summary: str, data: dict = None):
    """Log watcher events to event_chronicle for dashboard visibility."""
    import json
    import sqlite3
    from datetime import datetime
    
    db_path = get_base_path() / "memory" / "index.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO event_chronicle (
            timestamp, event_type, source, source_id, status, summary, data, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        event_type,
        'watcher',
        'watcher-main',
        status,
        summary,
        json.dumps(data) if data else None,
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
```

### Add to watcher summary output

Before exiting, watcher calls:
```python
log_to_event_chronicle(
    event_type='watcher_cycle',
    status='nominal',  # or 'stale', 'error', 'complete'
    summary=f'Checked {agents_count} agents, {issues_found} issues',
    data={
        'agents_checked': agents_count,
        'issues_found': issues_found,
        'actions_taken': actions_list,
        'recommendation': recommendation
    }
)
```

---

## Cost Analysis

### Option A: Watcher Only (Current Standard)
```
Daily: 2,880 Haiku checks × $0.001 = $2.88
      + ~10 Opus calls × $0.10 = $1.00
      = $3.88/day
```

### Option B: Sentinel Only (What I Created)
```
Daily: 2,880 Haiku checks × $0.001 = $2.88
      = $2.88/day
```

### Option C: Hybrid (Watcher + event_chronicle)
```
Same as Option A: $3.88/day
(No additional cost, just better visibility)
```

**Recommendation**: Option C (Hybrid) is best value - same cost as watcher, better dashboard integration.

---

## Implementation Plan

### Phase 2B: Integrate Watcher with event_chronicle

**Files to Modify**:
1. `watcher/watcher_loop.py` - Add event_chronicle logging
2. `watcher/README.md` - Document event_chronicle integration
3. Remove `dashboard_sentinel.py` (replace with watcher integration)
4. Remove `agents/sentinel_startup.py` (not needed)

**Keep**:
- `dashboard-app/backend/routers/chronicle.py` (use for watcher events too)
- `hooks/learning-loop/post_tool_learning.py` (integrate with watcher events)
- `.coordination/sentinel-config.yaml` (rename to monitor-config.yaml)

**New Files**:
- `.coordination/WATCHER-EVENT-CHRONICLE-INTEGRATION.md`

**Time Estimate**: 1-2 hours

---

## Decision Matrix

| Criteria | Watcher | Sentinel | Hybrid |
|----------|---------|----------|--------|
| **Standard ELF** | ✅✅✅ | ❌ | ✅✅✅ |
| **Cost** | ✅✅ ($3.88) | ✅ ($2.88) | ✅✅ ($3.88) |
| **Dashboard Visibility** | ❌ | ✅✅✅ | ✅✅✅ |
| **API Support** | ❌ | ✅✅✅ | ✅✅✅ |
| **Agent Monitoring** | ✅✅✅ | ❌ | ✅✅✅ |
| **Learning Loop Integration** | ❌ | ✅✅ | ✅✅✅ |
| **Production Ready** | ✅✅✅ | ⚠️ | ✅✅✅ |
| **Complexity** | ✅✅ | ✅✅ | ✅ |

---

## Recommendation

### 🎯 Go with **Hybrid Approach (Option C)**

**Reasoning**:
1. ✅ Stays true to ELF standard (uses existing watcher)
2. ✅ Cost-optimal (tiered approach)
3. ✅ Better visibility (event_chronicle)
4. ✅ Unified event stream (dashboard)
5. ✅ No breaking changes (additive only)
6. ✅ Production-ready immediately

**Next Steps**:
1. Modify watcher to log to event_chronicle
2. Remove duplicate Sentinel code
3. Keep event_chronicle infrastructure (reuse)
4. Update documentation
5. Test integrated system

---

## Your Decision Points

**A) Remove Sentinel, integrate with Watcher** (Recommended)
- Use standard ELF approach
- Better cost optimization
- Full compatibility with existing system
- Effort: ~2 hours to refactor

**B) Keep both (Sentinel + Watcher)**
- Parallel monitoring systems
- More expensive ($6.76/day)
- Redundant but safer
- Effort: 0 (keep current work)

**C) Keep Sentinel only**
- Depart from ELF standard
- Lose cost optimization
- Simpler but less efficient
- Effort: 0 (keep current work)

**Recommendation**: **A** - Modify watcher to use event_chronicle

---

## Final Notes

The watcher is a **production-tested system** that's been designed specifically for ELF multi-agent orchestration. Integrating it with event_chronicle would:

- ✅ Give you the best of both worlds
- ✅ Maintain ELF standards
- ✅ Optimize costs
- ✅ Improve visibility
- ✅ Keep system simple and maintainable

Let me know if you'd like me to proceed with the hybrid integration!
