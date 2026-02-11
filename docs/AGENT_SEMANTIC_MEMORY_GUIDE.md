# Agent Semantic Memory Guide

**Version**: 1.0 - 2026-02-11
**Purpose**: Precise guide for agents on WHEN and HOW to use semantic memory embedding

---

## 🎯 TL;DR

- **Automatic**: Learnings, tool failures, heuristics → Auto-embedded (you do nothing)
- **Manual**: Agent decisions, actions, outcomes → You call `/store` API
- **Search**: Find related memories via `/search` API for semantic similarity

---

## 📊 What Gets Auto-Embedded (No Agent Action Required)

### 1. **Heuristics** (Auto)
- **Trigger**: When LearningProcessor captures a heuristic
- **Condition**: Tool output contains `should/always/never/must/prefer/avoid/recommend` patterns
- **Metadata**: `source_type="heuristic"`, `domain`, `confidence`

```python
# Example auto-embedded:
# "system: Always use unified logging"
# "database: Use connection pooling for database locks"
```

### 2. **Tool Failures** (Auto)
- **Trigger**: Any tool execution failure
- **Condition**: `outcome == "failure"` in LearningProcessor
- **Metadata**: `source_type="failure"`, `domain`, `reason`

```python
# Example auto-embedded:
# "Failure: Database connection timeout. Connection refused."
```

### 3. **Learnings** (Auto)
- **Trigger**: Tool output contains learning patterns
- **Condition**: `outcome in ("success", "unknown")` with learning extraction
- **Metadata**: `source_type="learning"`, `domain`, `source="error_context|anti_pattern|implicit|explicit"`

---

## 🎛️ What Agents Must Embed Manually

Agents **MUST** call the `/store` API when they make:

### 1. **Strategic Decisions**
- Policy decisions
- Configuration choices
- Architecture decisions

```python
def store_decision(agent_name, decision_text, priority="medium"):
    """Store a strategic decision with semantic embedding."""
    response = requests.post(
        "http://localhost:5001/store",
        json={
            "text": decision_text,
            "source_id": f"{agent_name}_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_type": "decision",
            "metadata": {
                "agent": agent_name,
                "priority": priority,  # low/medium/high
                "timestamp": datetime.now().isoformat(),
                "decision_type": "strategic"
            }
        }
    )
    return response.json()
```

**Example**:
```python
store_decision(
    "ceo",
    "When EventBridge queue exceeds 1000 events, increase worker threads by 2",
    priority="high"
)
```

### 2. **Agent Actions with Outcomes**
- Completed analyzes
- Actions taken
- Problem resolutions

```python
def store_action(agent_name, action_text, outcome="success"):
    """Store an agent action with its outcome."""
    response = requests.post(
        "http://localhost:5001/store",
        json={
            "text": f"Action: {action_text}\nOutcome: {outcome}",
            "source_id": f"{agent_name}_action_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_type": "action",
            "metadata": {
                "agent": agent_name,
                "outcome_type": outcome,
                "timestamp": datetime.now().isoformat()
            }
        }
    )
    return response.json()
```

**Example**:
```python
store_action(
    "sentinel",
    "Restarted EventBridge service due to queue backlog of 500 events",
    "success"
)
```

### 3. **Pattern Discoveries**
- New anti-patterns found
- System behavior observations

```python
def store_pattern(agent_name, pattern_text, confidence=0.7):
    """Store a discovered pattern."""
    response = requests.post(
        "http://localhost:5001/store",
        json={
            "text": pattern_text,
            "source_id": f"{agent_name}_pattern_{hash(pattern_text) % 100000}",
            "source_type": "pattern",
            "metadata": {
                "agent": agent_name,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
        }
    )
    return response.json()
```

### 4. **Important Observations**
- System health trends
- Resource usage patterns
- Performance improvements

```python
def store_observation(agent_name, observation_text):
    """Store an important observation."""
    response = requests.post(
        "http://localhost:5001/store",
        json={
            "text": observation_text,
            "source_id": f"{agent_name}_observation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_type": "observation",
            "metadata": {
                "agent": agent_name,
                "timestamp": datetime.now().isoformat()
            }
        }
    )
    return response.json()
```

---

## 🔍 How to Query Semantic Memory

### Basic Search
```python
def search_memory(query_text, top_k=5, source_type=None):
    """Search semantic memory for related content."""
    payload = {
        "query": query_text,
        "top_k": top_k
    }
    if source_type:
        payload["source_type"] = source_type

    response = requests.post("http://localhost:5001/search", json=payload)
    results = response.json().get("results", [])

    print(f"Found {len(results)} matches for: '{query_text}'")
    for result in results:
        print(f"  [{result['source_type']}] {result['text']} (score: {result['score']:.2f})")

    return results
```

**Example**:
```python
# Find similar CEO decisions
decisions = search_memory("high CPU usage restart service", source_type="decision", top_k=3)

# Find previous failures
failures = search_memory("database timeout", source_type="failure", top_k=5)

# Find relevant heuristics
heuristics = search_memory("logging", source_type="heuristic")
```

---

## 📋 Summary: Agent Decision Tree

```
Agent makes decision/action?
│
├─ YES → Should this be remembered for future reference?
│         │
│         ├─ YES → Call `POST /store` with details
│         │
│         └─ NO  → Nothing needed
│
└─ NO → Nothing needed (system will auto-embed learnings/failures)
```

---

## 📝 Complete Reference

### Endpoints

| Endpoint | Method | Purpose | Required Fields |
|----------|--------|---------|----------------|
| `/store` | POST | Embed & store text | `text`, `source_id`, `source_type` |
| `/search` | POST | Semantic search | `query`, `top_k` (optional), `source_type` (optional) |
| `/health` | GET | Check daemon status | - |
| `/stats` | GET | Get statistics | - |
| `/embed` | GET | Get vector only | `text` |

### Metadata Fields

| Field | Type | Purpose | Examples |
|-------|------|---------|----------|
| `agent` | string | Agent name | `cea`, `sentinel`, `watcher` |
| `priority` | string | Importance | `low`, `medium`, `high` |
| `confidence` | float | Confidence 0-1 | `0.7`, `0.95`, `1.0` |
| `timestamp` | string | ISO 8601 | `2026-02-11T22:30:00` |
| `domain` | string | Category | `system`, `database`, `infrastructure` |
| `decision_type` | string | Type of decision | `strategic`, `operational`, `configuration` |
| `outcome_type` | string | Result | `success`, `failure`, `partial` |

### Source Types

| Type | When Used | Auto/Manual |
|------|-----------|-------------|
| `heuristic` | LearningProcessor captures heuristics | **Automatic** |
| `failure` | Tool execution fails | **Automatic** |
| `learning` | Tool output contains learnings | **Automatic** |
| `decision` | Agent makes strategic decision | **Manual (Agent MUST call)** |
| `action` | Agent performs action, records outcome | **Manual (Agent MUST call)** |
| `pattern` | Agent discovers pattern | **Manual (Agent MUST call)** |
| `observation` | Agent makes important observation | **Manual (Agent MUST call)** |

---

## ❌ What NOT to Embed

- ❌ Debug/trace output (use logging instead)
- ❌ Pure informational messages (use `/stats` instead)
- ❌ Temporary data (use ephemeral storage)
- ❌ Duplicates (check `/search` first to avoid)
- ❌ Trivial operations ("read file X" is NOT worth embedding)

---

## ✅ Best Practices

### 1. **Make Searchable**
```python
# ❌ BAD - Too vague
store_decision("cea", "Did something")

# ✅ GOOD - Specific and searchable
store_decision("cea", "Restarted EventBridge service after queue exceeded 500 events for 5 consecutive checks")
```

### 2. **Include Context**
```python
# ❌ BAD - No context
store_action("sentinel", "Fixed the issue")

# ✅ GOOD - With context
store_action(
    "sentinel",
    "Fixed database lock by killing blocking process PID 45678",
    "success"
)
```

### 3. **Use Appropriate Priority**
```python
# "critical" - System-wide impact, production issues
# "high" - Important decisions, major fixes
# "medium" - Standard operations, improvements
# "low" - Optimizations, minor observations
```

### 4. **Search Before Storing**
```python
# Check if already exists
existing = search_memory("similar decision", source_type="decision", top_k=1)
if not existing:
    store_decision(...)
```

---

## 🔧 Python Helper Module

Create `agent_memory_helper.py` for your agent:

```python
"""
Helper module for agents to use ELF semantic memory.
"""
import requests
import json
from datetime import datetime

SEMANTIC_DAEMON = "http://localhost:5001"

def store_decision(text, priority="medium", agent=None):
    """Store a strategic decision."""
    agent_name = agent or __name__.split('.')[-1]
    return requests.post(
        f"{SEMANTIC_DAEMON}/store",
        json={
            "text": text,
            "source_id": f"{agent_name}_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_type": "decision",
            "metadata": {
                "agent": agent_name,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "decision_type": "strategic"
            }
        }
    ).json()

def store_action(text, outcome="success", agent=None):
    """Store an action with its outcome."""
    agent_name = agent or __name__.split('.')[-1]
    return requests.post(
        f"{SEMANTIC_DAEMON}/store",
        json={
            "text": f"Action: {text}\nOutcome: {outcome}",
            "source_id": f"{agent_name}_action_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_type": "action",
            "metadata": {
                "agent": agent_name,
                "outcome_type": outcome,
                "timestamp": datetime.now().isoformat()
            }
        }
    ).json()

def search_memory(query, top_k=5, source_type=None):
    """Search semantic memory for related content."""
    payload = {"query": query, "top_k": top_k}
    if source_type:
        payload["source_type"] = source_type
    response = requests.post(f"{SEMANTIC_DAEMON}/search", json=payload)
    return response.json().get("results", [])
```

---

## 📚 Quick Reference Card

| Scenario | Action | API Call |
|----------|--------|----------|
| Made strategic decision | Store it | `POST /store` |
| Completed action with result | Store it | `POST /store` |
| Tool succeeded (normal operation) | Nothing | System auto-embeds |
| Tool failed | Nothing | System auto-embeds |
| Discovered new pattern | Store it | `POST /store` |
| Need to find related decision | Search | `POST /search` |
| Learning from tool output | Nothing | System auto-embeds |
| Debug output | Nothing | Use logger |

---

**Remember**: Semantics make memory memorable. When you store to `/store`, make it:
1. **Specific** - Include enough detail to be searchable
2. **Actionable** - Something that can guide future decisions
3. **Contextual** - Include when/how/why information
4. **Concise** - Summarize key insight in 1-2 sentences

---

**End of Guide**
