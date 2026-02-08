# Open_ELF Architecture Documentation

## Overview

This document describes the architecture of the Open_ELF (Emergent Learning Framework) system, with a focus on the clear separation of concerns between **Event Bridge** and **AgentManager**.

## Core Principle: Single Responsibility

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE PRINCIPLE                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   🔵 AgentManager  =  ALL AI Interactions                   │
│   🟢 Event Bridge  =  Event Routing ONLY                    │
│                                                              │
│   They are SEPARATE and COMPLEMENTARY                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Overview

### AgentManager (AI Gateway)

**Purpose**: Centralized gateway for all AI/LLM interactions

**Location**: `emergent-learning/Open_ELF/agents/agent_manager.py`

**Responsibilities**:
- ✅ Load agent definitions from `.md` files
- ✅ Create and manage persistent OpenCode sessions per agent
- ✅ Send prompts to OpenCode server
- ✅ Maintain session state and context
- ✅ Provide convenience methods for specific agents (watcher, sentinel, ceo, etc.)

**Key Methods**:
```python
# Query any agent by name
manager.ask_agent("watcher", "Check system health")

# Or use convenience methods
manager.watcher("Analyze logs")
manager.sentinel("Monitor security")
manager.ceo("Make strategic decision")
manager.orchestrator("Coordinate mission")
```

**Session Management**:
- Each agent has its own persistent session
- Sessions are identified by agent name + date
- Automatic session reuse or creation
- Session cleanup on shutdown

### Event Bridge (Event Router)

**Purpose**: Route events between OpenCode SSE stream and ELF hooks

**Location**: `emergent-learning/Open_ELF/orchestrator/event_bridge.py`

**Responsibilities**:
- ✅ Connect to OpenCode SSE event stream
- ✅ Route events to appropriate ELF hooks
- ✅ Provide HTTP API for system status
- ✅ Handle tool polling and execution
- ❌ **NO AI calls** - delegates to AgentManager

**Endpoints**:
```
GET  /status                    - System status
GET  /api/v1/health            - Health check
GET  /api/v1/agents            - List available agents
POST /api/v1/ask               - ⚠️ DEPRECATED (returns 410 Gone)
POST /api/v1/mission           - Log mission submission (no AI)
POST /api/v1/action/*          - Execute system actions
```

**Event Flow**:
```
OpenCode SSE → Event Bridge → ELF Hooks
                    ↓
            Event Processing
            (NO AI calls here)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Open_ELF Architecture                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   OpenCode   │     │   OpenCode   │     │    OpenCode  │        │
│  │    Server    │◄────┤    Agent     │◄────┤   Sessions   │        │
│  │  :4096       │     │   Manager    │     │  (per agent) │        │
│  └──────┬───────┘     └──────────────┘     └──────────────┘        │
│         │                                                            │
│         │ SSE Stream                                                  │
│         ▼                                                            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  Event       │────►│   ELF Hooks  │────►│  Agent Exec  │        │
│  │  Bridge      │     │  (Pre/Post)  │     │   Engine     │        │
│  │  :9998       │     └──────────────┘     └──────┬───────┘        │
│  └──────────────┘                                  │                │
│         │                                          │                │
│         │ HTTP API                                 │                │
│         ▼                                          ▼                │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Status     │     │   Actions    │     │   Agent      │        │
│  │   Endpoints  │     │   Execution  │     │   Responses  │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AGENT DEFINITIONS (.md files)                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ watcher  │ │ sentinel │ │   ceo    │ │architect │ ...   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │         ▲                                                    │   │
│  │         │ Loaded by AgentManager                            │   │
│  └─────────┼────────────────────────────────────────────────────┘   │
│            │                                                         │
│            └───────────────────────────────────────────────────────  │
│                        ALL AI TRAFFIC GOES HERE                      │
└─────────────────────────────────────────────────────────────────────┘
```

### CEO Inbox Monitor (Autonomous Escalation Processing)

**Purpose**: Autonomous background service that processes CEO-level escalations

**Location**: `emergent-learning/Open_ELF/agents/ceo_inbox_monitor.py`

**Responsibilities**:
- ✅ Monitor CEO inbox for new escalation files
- ✅ Process escalations using CEO agent via AgentManager
- ✅ Archive processed escalations with results
- ✅ Maintain audit trail of all CEO decisions

**Behavior**:
```
New Escalation → CEO Monitor (5min interval) → AgentManager.ceo()
                  → Response logged → Escalation archived
```

**Configuration**:
- Check interval: 5 minutes (configurable)
- Escalation directory: `~/.opencode/emergent-learning/ceo-inbox/`
- Archives directory: `~/.opencode/emergent-learning/ceo-inbox/archive/`

**Start**:
```bash
bash /home/bamer/.opencode/emergent-learning/scripts/start-ceo-monitor.sh
```

Or via system startup:
```bash
bash /home/bamer/.opencode/emergent-learning/start-elf-system.sh
```

## Data Flow Examples

### Scenario 1: Agent Query (AI Interaction)

```
User Code → AgentManager → OpenCode SDK → OpenCode Server
     │           │              │              │
     │           │              │              │
     ▼           ▼              ▼              ▼
  "watcher.ask  Session ID   Bun + MJS    LLM Response
   (health)"   (persistent)  Client
```

**Code**:
```python
from agents.agent_manager import get_agent_manager

manager = get_agent_manager()
result = manager.watcher("Check system health")
# AI response in result["response"]
```

### Scenario 2: Event Processing (NO AI)

```
OpenCode SSE → Event Bridge → ELF Hooks → Action Execution
     │              │              │              │
     │              │              │              │
     ▼              ▼              ▼              ▼
  tool_poll     Route to      Pre/Post      System Command
  event         hook type     Processing    (restart, etc.)
```

**No AI involved** - pure event routing and execution.

### Scenario 3: Mission Submission (Logging Only)

```
Client → POST /api/v1/mission → Event Bridge → Database
   │              │                   │              │
   │              │                   │              │
   ▼              ▼                   ▼              ▼
Mission      HTTP Request        Log Mission    SQLite
Data         (JSON)              No AI          Record
```

**Note**: The `/api/v1/mission` endpoint logs the mission but does NOT trigger AI. To actually execute a mission with AI, use AgentManager.

## Agent Definition Format

All agents are defined in Markdown files with YAML frontmatter:

```markdown
---
name: agent_name
description: "Brief description of agent purpose"
mode: all
temperature: 0.7
model: llama/nemotron-v3-coder
author: "Bamer Team"
version: "2.0.0"
tags: ["tag1", "tag2"]
permissions:
  bash:
    "rm -rf *": "ask"
    "sudo *": "deny"
  edit:
    "**/*.env*": "deny"
---

# Agent Content

System prompt and instructions here...
```

**Required Fields**:
- `name`: Agent identifier
- `description`: What the agent does
- `mode`: Execution mode (all, ask, etc.)

**Optional Fields**:
- `temperature`: Creativity level (0.0 - 1.0)
- `model`: LLM model to use
- `author`: Creator identification
- `version`: Version string
- `tags`: Categorization tags
- `permissions`: Security restrictions

## Migration Guide

### If you were using `/api/v1/ask` endpoint:

**OLD** (DEPRECATED):
```python
# Don't do this anymore
requests.post("http://localhost:9998/api/v1/ask", json={
    "query": "Analyze system"
})
```

**NEW** (Correct):
```python
from agents.agent_manager import get_agent_manager

manager = get_agent_manager()
result = manager.ask_agent("watcher", "Analyze system")
```

### If you were using `/api/v1/mission` for AI execution:

**OLD** (Changed behavior):
```python
# This now only logs, doesn't execute AI
requests.post("http://localhost:9998/api/v1/mission", json={
    "objective": "Fix bug"
})
```

**NEW** (Correct):
```python
from agents.agent_manager import get_agent_manager

manager = get_agent_manager()
result = manager.ask_agent("architect", "Design solution for bug fix")
# Or use appropriate agent for the task
```

## Best Practices

### 1. Use AgentManager for ALL AI Interactions

```python
# ✅ CORRECT
from agents.agent_manager import get_agent_manager
manager = get_agent_manager()
response = manager.ask_agent("researcher", "Investigate issue")

# ✅ ALSO CORRECT (convenience method)
response = manager.researcher("Investigate issue")
```

### 2. Use Event Bridge for Event Routing Only

```python
# ✅ CORRECT - Check system status
requests.get("http://localhost:9998/status")

# ✅ CORRECT - Execute system action
requests.post("http://localhost:9998/api/v1/action/process-restart")

# ❌ WRONG - Don't use for AI queries (returns 410 Gone)
requests.post("http://localhost:9998/api/v1/ask", json={"query": "..."})
```

### 3. Session Persistence

AgentManager automatically:
- Creates sessions per agent
- Reuses existing sessions from the same day
- Handles session lifecycle
- Cleans up on shutdown

```python
# Session is managed automatically
manager.watcher("Task 1")  # Creates session
manager.watcher("Task 2")  # Reuses same session
```

### 4. Error Handling

```python
result = manager.ask_agent("watcher", "Check health")

if result["success"]:
    print(result["response"])
else:
    print(f"Error: {result['error']}")
```

## Configuration

### AgentManager Configuration

```python
from pathlib import Path

manager = AgentManager(
    opencode_url="http://localhost:4096",
    agents_dir=Path("/path/to/agents"),
    workdir=Path("/path/to/workspace"),
    timeout=600  # seconds
)
```

### Event Bridge Configuration

Environment variables:
```bash
export ELF_OPENCODE_URL="http://localhost:4096"
export ELF_COORDINATION_DIR="/path/to/.coordination"
export ELF_HOOKS_DIR="/path/to/hooks"
```

## Troubleshooting

### Issue: "Agent not found"
**Cause**: Agent .md file missing or malformed
**Solution**: Check `agents/OPC_ELF_System_Agents/` directory

### Issue: "Session creation failed"
**Cause**: OpenCode server not running
**Solution**: Start OpenCode server on port 4096

### Issue: "Event Bridge not responding"
**Cause**: Event Bridge not started
**Solution**: Start Event Bridge: `python event_bridge.py start`

### Issue: "/api/v1/ask returns 410 Gone"
**Cause**: Using deprecated endpoint
**Solution**: Use AgentManager instead (see Migration Guide)

## Summary

| Component | Purpose | AI Calls? | Cycle | Use For |
|-----------|---------|-----------|-------|---------|
| **AgentManager** | AI interaction gateway | ✅ YES | On-demand | All LLM queries |
| **Event Bridge** | Event routing | ❌ NO | Event-driven | SSE events, status, actions |
| **Watcher** | System health monitor | ✅ YES | Basic: 60s, AI: 10min | Resource, process, anomaly monitoring |
| **Sentinel** | Security pattern detector | ✅ YES | Basic: 30s, AI: 5min | Behavioral analysis, vulnerability detection |
| **Unified Orchestrator** | Central coordination | ✅ YES | Basic: 10s, AI: 15min | Event fusion, decision making, mission execution |
| **CEO Monitor** | Escalation processor | ✅ YES | 5 min interval | Autonomous CEO decision processing |

Remember:
- **AgentManager = AI** (OpenCode sessions, prompts, responses)
- **Event Bridge = Events** (SSE stream, hooks, HTTP API)
- **Tiered Monitors** = Autonomous monitoring with configurable AI intervals

Keep them separate, keep them clean.

---

**Version**: 1.1
**Last Updated**: 2026-02-08
**Maintainer**: ELF Team
