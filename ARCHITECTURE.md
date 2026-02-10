# Open_ELF Architecture Documentation

## Overview

This document describes the architecture of the Open_ELF (Emergent Learning Framework) system after the 2026-02-09 refactoring.

## Architecture Refactoring (2026-02-09)

The system has been refactored from an over-engineered 8+ component architecture to a clean 3-level hierarchy with consolidated supporting components.

### Hierarchy Levels

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT HIERARCHY                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 1: Watcher (core/sentinel.py)                         │
│  ├── Health Monitoring                                      │
│  ├── Pattern Detection                                      │
│  ├── AI Analysis (every 5 minutes)                          │
│  └── Escalates to Orchestrator (warning/critical)          │
│                                                              │
│  Level 2: Orchestrator (Open_ELF/orchestrator/)             │
│  ├── Service Management                                     │
│  ├── Auto-restart Services                                  │
│  ├── AI Analysis (independent schedule)                     │
│  └── Escalates to CEO (critical only)                      │
│                                                              │
│  Level 3: CEO (agents/OPC_ELF_System_Agents/ceo.md)        │
│  ├── Strategic Decision Making                              │
│  └── Critical Escalation Processing                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Overview

### Level 1: Watcher (`core/sentinel.py`)

**Status**: ✅ **ACTIVE** (Replaces old Watcher + Sentinel)

**Responsibilities**:
- Service health monitoring (OpenCode, Dashboard, EventBridge, Learning Capture)
- Database metrics collection
- Pattern detection with cooldown periods
- AI-powered analysis via AgentManager
- Escalation to Orchestrator on warning/critical

**Timing**:
- Basic health checks: Every 60 seconds
- AI analysis: Every 300 seconds (5 minutes)
- Pattern cooldown: 30 minutes between same pattern reports

**Usage**:
```python
from core.sentinel import Watcher

sentinel = Watcher()
sentinel.run_continuous()
```

### Level 2: Unified Orchestrator

**Status**: ✅ **ACTIVE** (Unchanged)

**Responsibilities**:
- Service management and coordination
- Auto-restart failed services
- Event processing and decision making
- AI analysis on its own schedule
- Escalation to CEO when critical

**Location**: `Open_ELF/orchestrator/unified_orchestrator.py`

### Level 3: CEO Agent

**Status**: ✅ **ACTIVE** (Unchanged)

**Responsibilities**:
- Strategic decision making
- Critical escalation processing
- High-level system oversight

**Location**: `agents/OPC_ELF_System_Agents/ceo.md`

## Supporting Components

### LearningProcessor (`core/learning_processor.py`)

**Status**: ✅ **ACTIVE** (Replaces hooks + conductor trails)

**Responsibilities**:
- Pre-tool context injection and heuristic consultation
- Post-tool outcome analysis and validation
- **ALL trail systems** (both preserved):
  - Pheromone trails (file access tracking)
  - Workflow trails (scents: discovery, blocker, hot, cold)
- Hot spot analysis (combined)
- Advisory verification
- Auto-failure recording
- Heuristic promotion
- Trail decay management

**Usage**:
```python
from core.learning_processor import LearningProcessor, ToolEvent

processor = LearningProcessor()
result = processor.post_tool_process(tool_event)
```

### EventBridge v2 (`core/event_bridge_v2.py`)

**Status**: ✅ **ACTIVE** (Replaces old EventBridge)

**Responsibilities**:
- SSE event listening from OpenCode
- Direct database logging
- Routes tool events to LearningProcessor
- Status API endpoint
- No hook execution
- No AI calls

**Usage**:
```bash
python core/event_bridge_v2.py start
```

### AgentManager

**Status**: ✅ **ACTIVE** (Unchanged)

**Location**: `Open_ELF/agents/agent_manager.py`

All AI interactions go through AgentManager with persistent sessions per agent.

## Legacy Components (Permanently Deleted)

The following legacy components have been **permanently removed** from the codebase (2026-02-10):

### Learning (All consolidated into `core/learning_processor.py`)
- ❌ `hooks/post_tool_use/post_tool_learning.py` - **DELETED**
- ❌ `hooks/post_tool_use/record_pheromone.py` - **DELETED**
- ❌ `archived_components/` directory - **DELETED** (entire archive removed)

All learning operations, pheromone trails, and workflow trails are now handled by the centralized `LearningProcessor` in `core/learning_processor.py`.

## Data Flow

```
OpenCode SSE → EventBridge v2 → LearningProcessor → Database
                                      ↓
                                 Watcher (metrics)
                                      ↓
                               Orchestrator (actions)
                                      ↓
                              AgentManager (AI)
```

## Escalation Flow

```
Watcher (L1) detects issue
    ↓
Creates escalation file for Orchestrator
    ↓
Orchestrator (L2) reviews and acts
    ↓
If critical → Escalates to CEO (L3)
    ↓
CEO (L3) makes strategic decisions
```

## File Structure

```
emergent-learning/
├── core/                                    # NEW: Core components
│   ├── __init__.py
│   ├── sentinel.py                          # Level 1 Agent (merged)
│   ├── learning_processor.py               # All learning + trails
│   └── event_bridge_v2.py                  # Simplified event routing
│
├── Open_ELF/
│   ├── agents/
│   │   └── OPC_ELF_System_Agents/
│   │       ├── sentinel.md                      # Agent definition
│   │       ├── sentinel.md                     # Agent definition
│   │       ├── ceo.md                          # Level 3 Agent definition
│   │       └── ...
│
│ ├── REFACTORING_SUMMARY.md                  # Detailed refactoring info
│ ├── CODE_CLEANUP_SUMMARY_20260210.md         # Legacy cleanup & fixes
│ └── CHANGELOG.md                             # Version history
```

## Quick Start

```bash
# Start all services
./start-elf-system.sh

# Start minimal (backend + sentinel)
./start-elf-system.sh minimal

# Test compilation
python -m py_compile core/sentinel.py core/learning_processor.py core/event_bridge_v2.py
```

## Configuration

### Watcher Intervals
Edit `core/sentinel.py`:
- `BASIC_INTERVAL = 60` - Health check interval (seconds)
- `AI_INTERVAL = 300` - AI analysis interval (seconds)

### Database
All data stored in `memory/index.db` with preserved tables:
- `heuristics` - Golden rules and regular heuristics
- `learnings` - System learnings
- `trails` - Workflow trails with scents
- `pheromone_trails` - File access trails
- `metrics` - System metrics

## Migration Notes

### From Old Components

If you have code using old components:

**Old Watcher**:
```python
# OLD (deprecated)
from Open_ELF.sentinel.elf_sentinel import ElfWatcher

# NEW
from core.sentinel import Watcher
```

**Old Hooks**:
```python
# OLD (deprecated)
import hooks.learning_loop.post_tool_learning

# NEW
from core.learning_processor import LearningProcessor
processor = LearningProcessor()
result = processor.post_tool_process(event)
```

**Old EventBridge**:
```bash
# OLD (deprecated)
python Open_ELF/orchestrator/event_bridge.py start

# NEW
python core/event_bridge_v2.py start
```

## Troubleshooting

### Watcher not starting
```bash
# Check if old processes are running
pkill -f "elf_sentinel.py"
pkill -f "sentinel_monitor.py"

# Start new sentinel
cd /home/bamer/.opencode/emergent-learning
python core/sentinel.py
```

### Trail data missing
Both trail tables are preserved in the database. Use:
```bash
python core/learning_processor.py --hot-spots
```

### Service startup issues
Check `logs/` directory for detailed error messages.

## Summary

- **Code Reduction**: 72% (~5,300 → ~1,500 lines)
- **Components**: 8+ → 4 (Watcher, Orchestrator, LearningProcessor, EventBridge)
- **Hierarchy**: Clear L1 → L2 → L3 escalation path
- **Functionality**: 100% preserved (all trails, heuristics, monitoring)
- **Maintainability**: Much improved with single-responsibility components

---

**Last Updated**: 2026-02-09
**Version**: 3.0 (Refactored)
