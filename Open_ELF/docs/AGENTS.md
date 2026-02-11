# ELF Agents Documentation

## Overview

The Emergent Learning Framework (ELF) uses a sophisticated agent system where specialized AI agents handle different aspects of system monitoring, analysis, and orchestration. This document describes the agent architecture, requirements, and usage patterns.

## Philosophy: Distributed Intelligence

ELF follows a **distributed intelligence** model where:
- Multiple specialized agents work together
- No single point of failure (agents can work independently)
- Agents communicate through standardized protocols
- Human oversight at critical decision points (CEO inbox)

## Core Agents

### 1. Unified Orchestrator

**Role**: Central coordination and high-level decision making

**Responsibilities**:
- System-wide health monitoring
- Coordination between other agents
- Escalation management
- Resource allocation

**Usage**:
```python
from agent_manager import get_agent_manager
manager = get_agent_manager()
response = manager.ask_agent("unified-orchestrator", "Analyze system health")
```

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/unified-orchestrator.md`

### 2. Sentinel Agent

**Role**: Continuous system monitoring and alerting

**Responsibilities**:
- Monitor system services (EventBridge, dashboard, etc.)
- Detect anomalies and failures
- Trigger escalations when needed
- Log all activities to unified logging system

**Usage**:
```python
from agent_manager import get_agent_manager
manager = get_agent_manager()
response = manager.sentinel("Check service health")
```

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/sentinel.md`

### 3. Sentinel Monitor

**Role**: Intelligent monitoring with pattern recognition

**Responsibilities**:
- Real-time dashboard health monitoring
- Pattern recognition and anomaly detection
- Autonomous alerting and decision-making
- Event chronicle integration

**Usage**:
```python
from agents.sentinel_monitor import SentinelMonitor
sentinel = SentinelMonitor()
metrics = sentinel.run_monitoring_cycle()
```

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/sentinel.md`

### 4. CEO Agent

**Role**: High-level oversight and critical decision escalation

**Responsibilities**:
- Review escalations from other agents
- Make critical system-level decisions
- Human-in-the-loop oversight
- Approve major system changes

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/ceo.md`

### 5. Architect Agent

**Role**: System design and architecture decisions

**Responsibilities**:
- Design system improvements
- Architecture reviews
- Technical debt assessment
- Integration planning

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/architect.md`

### 6. Researcher Agent

**Role**: Deep investigation and analysis

**Responsibilities**:
- Root cause analysis
- Technical research
- Data gathering
- Pattern investigation

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/researcher.md`

### 7. Creative Agent

**Role**: Innovation and novel solutions

**Responsibilities**:
- Propose innovative solutions
- Think outside the box
- Alternative approach generation
- Brainstorming sessions

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/creative.md`

### 8. Skeptic Agent

**Role**: Critical analysis and risk assessment

**Responsibilities**:
- Challenge assumptions
- Identify risks and edge cases
- Validate proposed solutions
- Prevent groupthink

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/skeptic.md`

### 9. Learning Extractor Agent

**Role**: Extract and document learnings

**Responsibilities**:
- Extract heuristics from sessions
- Document patterns
- Create golden rules
- Knowledge management

**File**: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/learning-extractor.md`

## Agent Architecture

### Agent Configuration Format

Agents are defined in Markdown files with YAML frontmatter:

```markdown
---
name: agent-name
model: nvidia/minimaxai/minimax-m2
description: Brief description of the agent
tags: [monitoring, analysis]
permissions:
  - read_logs
  - write_escalations
---

# Agent Name

## System Prompt

You are a specialized agent for...

## Capabilities

- Capability 1
- Capability 2

## Response Format

Always respond with...
```

### Agent File Location

All agent definitions are stored in:
```
/home/bamer/.opencode/agents/OPC_ELF_System_Agents/
```

## AgentManager

The `AgentManager` class provides the primary interface for interacting with agents.

### Basic Usage

```python
from agents.agent_manager import AgentManager, get_agent_manager

# Get the singleton instance
manager = get_agent_manager()

# Ask an agent a question
response = manager.ask_agent("sentinel", "Check system health")

# Or use convenience methods
response = manager.sentinel("Check all services")
response = manager.sentinel("Analyze recent patterns")
response = manager.ceo("Review this escalation")
```

### AgentManager Features

1. **Session Persistence**: Each agent maintains its own session
2. **System Prompts**: Loaded from `.md` files
3. **Model Selection**: Automatic based on agent configuration
4. **Error Handling**: Graceful fallbacks

### Available Methods

```python
# Generic method
manager.ask_agent(agent_name: str, prompt: str) -> str

# Convenience methods
manager.sentinel(prompt: str) -> str
manager.sentinel(prompt: str) -> str
manager.ceo(prompt: str) -> str
manager.architect(prompt: str) -> str
manager.researcher(prompt: str) -> str
manager.creative(prompt: str) -> str
manager.skeptic(prompt: str) -> str
manager.learning_extractor(prompt: str) -> str
```

## Requirements for All Agents

### 1. Unified Logging (REQUIRED)

**All agents MUST use the unified logging system**:

```python
# CORRECT ✓
try:
    from elf_logging import get_logger
    logger = get_logger("my_agent")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("my_agent")

logger.info("Agent starting...")
```

**INCORRECT ✗**:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

See: [Unified Logging System](./UNIFIED_LOGGING.md)

### 2. Agent Configuration File (REQUIRED)

Every agent must have a `.md` file in:
```
/home/bamer/.opencode/agents/OPC_ELF_System_Agents/{agent-name}.md
```

Minimum required fields:
- `name`: Agent identifier
- `model`: LLM model to use
- `description`: Brief description
- System prompt in the markdown body

### 3. Error Handling (REQUIRED)

Agents must handle errors gracefully:

```python
try:
    result = perform_action()
    logger.info(f"Action completed: {result}")
except Exception as e:
    logger.error(f"Action failed: {e}")
    # Don't crash - log and continue
```

### 4. Independence (REQUIRED)

Agents must be able to function independently:

```python
# GOOD: Direct call to AgentManager
def analyze():
    manager = get_agent_manager()
    return manager.ask_agent("unified-orchestrator", "...")

# BAD: Dependency on EventBridge
def analyze():
    response = requests.post("http://localhost:9998/api/v1/mission", ...)
    # If EventBridge is down, this fails
```

## Agent Communication

### Direct Calls (Preferred)

Agents should call each other directly through AgentManager:

```python
# Agent A calls Agent B directly
manager = get_agent_manager()
analysis = manager.sentinel("Analyze patterns")
verification = manager.skeptic(f"Verify this analysis: {analysis}")
```

### Event Bridge (Legacy)

The Event Bridge can still be used for logging and monitoring, but **should not be a dependency**:

```python
# Log to Event Bridge (optional)
log_event("agent_action", "my_agent", "Action completed")

# But don't depend on it
# BAD: if event_bridge_down():
#     raise Exception("EventBridge unavailable!")
```

## Creating a New Agent

### Step 1: Create Agent Definition File

Create a new file: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/my-agent.md`

```markdown
---
name: my-agent
model: nvidia/minimaxai/minimax-m2
description: What this agent does
tags: [tag1, tag2]
permissions:
  - read_logs
  - write_files
---

# My Agent

## System Prompt

You are a specialized agent that...

## Capabilities

1. Do X
2. Do Y
3. Do Z

## Response Format

Always respond in JSON format with the following structure:
{
    "status": "success|error",
    "result": "...",
    "confidence": 0-100
}
```

### Step 2: Add Logging

Ensure your agent code uses unified logging:

```python
try:
    from elf_logging import get_logger
    logger = get_logger("my-agent")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("my-agent")
```

### Step 3: Test the Agent

```python
from agents.agent_manager import get_agent_manager

manager = get_agent_manager()
response = manager.ask_agent("my-agent", "Test prompt")
print(response)
```

### Step 4: Add Convenience Method (Optional)

Update `agent_manager.py` to add a convenience method:

```python
def my_agent(self, prompt: str) -> str:
    """Convenience method for my-agent."""
    return self.ask_agent("my-agent", prompt)
```

## Agent Development Best Practices

1. **Single Responsibility**: Each agent should have a clear, focused role
2. **Independence**: Agents should function without dependencies on other services
3. **Logging**: Always use unified logging for observability
4. **Error Handling**: Graceful degradation, not crashes
5. **Documentation**: Document agent capabilities and limitations
6. **Testing**: Test agents in isolation before integration
7. **Monitoring**: Log all actions and decisions
8. **Escalation**: Know when to escalate to CEO agent

## Troubleshooting

### Agent Not Responding

**Check**:
1. Agent `.md` file exists and is valid
2. AgentManager can load the agent
3. OpenCode server is running
4. Logs for error messages

**Solution**:
```python
# Test agent directly
from agents.agent_manager import AgentManager
manager = AgentManager()
print("Loaded agents:", manager.agents.keys())
response = manager.ask_agent("agent-name", "test")
print("Response:", response)
```

### Agent Manager Not Available

**Symptom**: `AgentManager not available - falling back to basic mode`

**Solution**:
```python
# Add Open_ELF/agents to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/bamer/.opencode/emergent-learning/Open_ELF/agents")))
from agent_manager import get_agent_manager
```

### Missing Logs

**Symptom**: Agent actions not appearing in logs

**Solution**:
1. Verify unified logger import
2. Check log file: `/home/bamer/.opencode/emergent-learning/logs/{agent-name}.log`
3. Run migration script: `python3 scripts/migrate_to_unified_logger.py`

## Related Documentation

- [Unified Logging System](./UNIFIED_LOGGING.md)
- [Agent Manager Implementation](../agents/agent_manager.py)
- [Agent Configuration Format](./agent_formats.md)
- [Orchestration System](./ORCHESTRATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

## Quick Reference

### Import AgentManager
```python
from agents.agent_manager import get_agent_manager
manager = get_agent_manager()
```

### Use Unified Logger
```python
from elf_logging import get_logger
logger = get_logger("my-agent")
logger.info("Message")
```

### Call an Agent
```python
response = manager.ask_agent("sentinel", "Check health")
# Or
response = manager.sentinel("Check health")
```

### Log Directory
```
/home/bamer/.opencode/emergent-learning/logs/
```

### Agent Definitions
```
/home/bamer/.opencode/agents/OPC_ELF_System_Agents/*.md
```

## Migration Status

As of 2026-02-07, all 35+ ELF components have been migrated to:
- ✅ Use unified logging system
- ✅ Call agents directly via AgentManager
- ✅ Remove EventBridge dependencies
- ✅ Add graceful fallbacks

See migration script: `Open_ELF/scripts/migrate_to_unified_logger.py`
