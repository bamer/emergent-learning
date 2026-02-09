# Mission & Pheromone System Investigation Report
**Date:** 2026-02-10
**Severity:** CRITICAL - Missions not completing

## Executive Summary

Two related issues have been identified:

1. **Pheromone trails system** - PARTIALLY WORKING - Last recording was 9 hours ago
2. **Mission execution system** - BROKEN - Missions created but never complete, stuck in "running" state

## Issue 1: Pheromone Trails Not Recording

### Current Status
- **Recorded entries:** 6 total in `pheromone_trails` table
- **Last recording:** 2026-02-09 13:20:00 (approximately 9 hours ago)
- **Hook script:** `/home/bamer/.opencode/emergent-learning/hooks/post_tool_use/record_pheromone.py`
- **Hook config:** Not found in expected location (`.config/opencode/hooks/post_tool_use.json`)

### Root Cause Analysis

The pheromone recording script (`record_pheromone.py`) exists and is correctly implemented to:
1. Accept tool_execution events via stdin or CLI argument
2. Extract file paths from various tool types (Read, Grep, Bash, Edit, Write)
3. Aggregate statistics per file in `pheromone_trails` table

**However**, there's no evidence this script is currently being called by the post-tool hook system.

### Expected Hook Configuration

The hook should be configured to call:
```bash
python /home/bamer/.opencode/emergent-learning/hooks/post_tool_use/record_pheromone.py
```

After every tool execution.

### Impact

- **Low data quality:** New file access patterns are not being tracked
- **No hotspot analysis:** Cannot identify frequently accessed files
- **Missing optimization data:** No data for adaptive caching or prioritization

---

## Issue 2: Mission Tasks Never Finish (CRITICAL)

### Current Status

**Running missions (stuck):**
| Mission ID | Agent | Created | Status | Age |
|-----------|-------|---------|--------|-----|
| `mission_20260209_120610_1115` | - | Feb 09 12:06 | running | ~10 hours |
| `mission_20260209_033220_0004` | auto | Feb 09 03:32 | running | ~19 hours |
| `mission_20260209_032855_2147` | auto | Feb 09 03:28 | running | ~19 hours |
| `mission_20260209_031917_1422` | researcher | Feb 09 03:19 | running | ~19 hours |

**Mission patterns:**
- Created successfully ✅
- Started successfully ✅
- Assigned session ID ✅
- **NEVER COMPLETED** ❌

### Root Cause Analysis

The mission system architecture consists of:

1. **Mission Engine** (`mission_engine.py`) - Core execution engine
   - Has `start_background_processing()` method to run queue processing in a thread
   - Has `_process_queue_loop()` that should pick up pending missions and execute them
   - **NEVER STARTED**

2. **Mission Live Handler** (`mission_live_handler.py`)
   - Has `_execute_live_mission_async()` to execute missions individually
   - Requires the Mission Engine to be initialized and started
   - **NEVER INVOKED**

3. **Mission Storage** (`mission_store.py`)
   - Stores missions as markdown files in `.coordination/missions/` directories
   - Has methods to start/complete/fail missions
   - **FILE STORAGE WORKING** - Mission files are being created and updated

4. **Missions Router** (`routers/missions.py`)
   - Provides API endpoints to query mission status
   - **READ-ONLY** - Does not execute missions

### The Critical Gap

**There is no background service that:**
1. Starts the Mission Engine
2. Calls `start_background_processing()` to process the mission queue
3. Converts dashboard missions to orchestrator format
4. Executes missions and updates their status to completed/failed

### Mission Bridge is a Placeholder

The `mission_bridge.py` script exists but is marked as a placeholder:
```python
if __name__ == "__main__":
    print("🚀 Mission Bridge Starting...")
    print("This is a placeholder - will be integrated with orchestrator")
```

It's **NOT RUNNING** as a background service.

### Expected Workflow

The system should work like this:

```
Dashboard creates mission (mark as "runnning")
    ↓
Mission Bridge monitors .coordination/missions/
    ↓
Mission Engine starts background processing
    ↓
Mission picked from queue, executed via AgentManager
    ↓
Result saved, status updated to "completed" or "failed"
```

**What's happening instead:**
```
Dashboard creates mission (mark as "runnning")
    ↓
❌ Nothing else happens - mission sits in "running" forever
```

### Impact

- **No mission completion:** Users can run missions but they never finish
- **Misleading UI:** Missions appear to be "running" when they're actually stuck
- **Resource waste:** Stale mission files accumulate
- **Broken user experience:** The "Live Panel Tasks & Trails" feature is non-functional

---

## Architecture Issues

### 1. Missing Integration Points

| Component | Status | Issue |
|-----------|--------|-------|
| `record_pheromone.py` | Exists | Not hooked into tool execution |
| `mission_engine.py` | Exists | Background processing never started |
| `mission_bridge.py` | Exists | Marked as placeholder, not running |
| `mission_live_handler.py` | Exists | Never initialized |
| Orchestrator | Running | No integration with mission system |

### 2. Missing Background Services

The system needs these background services:

1. **Pheromone Hook Integration**
   - Configure `post_tool_use.json` to call `record_pheromone.py`
   - Test hook execution

2. **Mission Executor Service**
   - Reads from `.coordination/missions/running/`
   - Uses `MissionEngine` to execute missions
   - Updates status to `completed/failed`
   - Moves to appropriate directory

3. **Mission Queue Processor**
   - Monitors `.coordination/missions/pending/`
   - Converts files to Mission objects
   - Adds to MissionEngine queue
   - Starts background processing

---

## Root Causes Summary

### Pheromone Trails Issue
- **Primary cause:** Post-tool hook not configured to call `record_pheromone.py`
- **Secondary cause:** Hook config file missing or not in expected location

### Mission Execution Issue
- **Primary cause:** No background service executing the mission queue
- **Secondary cause:** Mission Bridge is placeholder code, not integrated
- **Root cause:** Complete lack of integration between dashboard, mission engine, and orchestrator

---

## Recommended Fixes

### Priority 1: Fix Mission Execution (CRITICAL)

**Solution 1: Create Mission Executor Service**

Create a background service that:
1. Starts the Mission Engine with background processing enabled
2. Monitors `.coordination/missions/running/` directory
3. For each mission:
   - Calls `execute_mission()` via AgentManager
   - Updates status to `completed/failed`
   - Moves to appropriate directory
4. Runs continuously as a daemon

**Solution 2: Integrate Mission Bridge with Orchestrator**

Complete the `mission_bridge.py` implementation to:
1. Connect to running Orchestrator instance
2. Monitor `.coordination/missions/` for new files
3. Convert dashboard mission format to orchestrator format
4. Submit to orchestrator for execution
5. Track completion and update status

### Priority 2: Fix Pheromone Trails (HIGH)

**Solution: Configure Post-Tool Hook**

1. Create or update hook config at `.opencode/hooks/post_tool_use.json`
2. Add entry for `record_pheromone.py`
3. Test hook execution by running manual tool commands
4. Verify records appear in `pheromone_trails` table

### Priority 3: Cleanup Stale Missions (MEDIUM)

**Solution: Mission Cleanup Script**

Create a cleanup script that:
1. Moves "running" missions older than 24 hours to "failed"
2. Marks them with error: "Timeout - never completed"
3. Archives old completed/failed missions

---

## Verification Steps

### After Fixes Applied:

1. **Create a test mission via dashboard**
2. **Wait 30 seconds**
3. **Verify mission status changes:**
   - From "running" → "pending" → "running" → "completed" or "failed"
4. **Check mission file in `.coordination/missions/`**
   - Should have logs of execution progress
   - Should show result or error
5. **Verify pheromone trails:**
   - Execute a Read tool command
   - Check `pheromone_trails` table for new entry
   - Verify timestamp is current

---

## Files to Create/Modify

### New Files Needed:

1. `/home/bamer/.opencode/emergent-learning/Open_ELF/mission-engine/mission_executor_service.py`
   - Background service to execute missions

2. `/home/bamer/.opencode/emergent-learning/scripts/cleanup-stale-missions.sh`
   - Cleanup script for stuck missions

3. `/home/bamer/.opencode/emergent-learning/.opencode/hooks/post_tool_use.json` (or update existing)
   - Hook configuration

### Files to Modify:

1. `Open_ELF/orchestrator/mission_bridge.py`
   - Complete the integration with orchestrator

2. `Open_ELF/mission-engine/mission_engine.py`
   - Ensure background processing is properly configured

---

## Learning for Building

### [LEARNED:architecture] Mission systems require dedicated background execution services, not just data structures

The system had all the components (engine, storage, API) but was missing the critical piece: **a background service that actually executes the missions**. This is a classic case of having perfect architecture but no runtime orchestration.

### [LEARNED:integration] Hooks must be explicitly configured and tested

The pheromone recording script was well-implemented but never called because the hook configuration was missing. Future systems must include:
1. Explicitly documented hook configuration
2. Verification that hooks are being called
3. Debug logging to confirm execution

### [LEARNED:monitoring] "Running" status requires active monitoring

The "running" status is misleading if there's no process tracking execution. Future systems should:
1. Track actual process PIDs for running missions
2. Use heartbeats or watchdogs to detect stuck missions
3. Auto-timeout and fail missions that don't progress

---

## Next Steps

1. ✅ Create mission executor service script
2. ✅ Configure post-tool hook for pheromones
3. ✅ Add mission cleanup functionality
4. 🔄 Test mission creation and execution
5. 🔄 Verify pheromone trail recording
6. 🔄 Document the final architecture
