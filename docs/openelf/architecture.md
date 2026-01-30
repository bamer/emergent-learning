# OpenELF Architecture

## System Overview

OpenELF implements a layered architecture that combines the power of ELF's orchestration with OpenCode's agent management:

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenELF Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   User Tools    │    │   Dashboard     │               │
│  │  (CLI/Web/API)  │    │   Interface     │               │
│  └─────────────────┘    └─────────────────┘               │
│              │                   │                         │
│              ▼                   ▼                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agent Orchestrator                     │   │
│  │  • Lifecycle Management                             │   │
│  │  • Health Monitoring                                │   │
│  │  • Auto-restart & Recovery                          │   │
│  │  • CEO Inbox Automation                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Personality Manager                       │   │
│  │  • ELF & OpenCode Format Support                    │   │
│  │  • Intelligent Model Selection                      │   │
│  │  • Skill/Plugin Integration                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                               │
│                           ▼                               │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │   ELF Agents    │  │ OpenCode Agents │               │
│  │ (Custom Config) │  │  (Native MD)    │               │
│  └─────────────────┘  └─────────────────┘               │
│              │                   │                         │
│              └─────────┬─────────┘                         │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              OpenCode Server                        │   │
│  │  • Session Management                               │   │
│  │  • Model Routing                                │   │
│  │  • Native Agent Execution                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Orchestrator
The central coordination system that manages agent lifecycles, communications, and monitoring.

**Key Responsibilities:**
- Agent lifecycle management (start, stop, restart)
- Health monitoring and automatic recovery
- Session management with OpenCode server
- CEO inbox automation
- Pattern detection and response handling

### 2. Personality Manager
Handles loading and management of agent personalities from various formats.

**Key Responsibilities:**
- Support for both ELF and OpenCode agent formats
- Intelligent model selection based on task characteristics
- Skill/plugin/tool integration
- Configurable precedence settings

### 3. Agent Types
Standard agent types with predefined roles and capabilities:

| Agent Type  | Role                  | Default Model                    | Purpose                          |
|-------------|-----------------------|----------------------------------|----------------------------------|
| SENTINEL    | Monitoring            | opencode/kimi-k2.5-free          | System health and pattern detection |
| RESEARCHER  | Investigation         | opencode/trinity-large-preview-free | Deep code analysis and research |
| ARCHITECT   | Design                | opencode/nemotron-v3-coder       | System architecture and design   |
| SKEPTIC     | Critical Analysis     | opencode/glm-4.7-free            | Risk assessment and validation   |
| CREATIVE    | Innovation            | opencode/kimi-k2.5-free          | Creative problem solving         |
| CEO         | Decision Making       | opencode/trinity-large-preview-free | Executive decisions and strategy |

## Data Flow

1. **Initialization**: Orchestrator starts and loads personality manager
2. **Agent Startup**: Agents are started based on auto-start configuration
3. **Personality Loading**: Personality manager resolves agent configurations
4. **Session Creation**: Orchestrator creates OpenCode sessions for agents
5. **Task Execution**: Agents process tasks with appropriate models and configurations
6. **Monitoring**: Continuous health checks and performance monitoring
7. **Event Logging**: All activities logged to database for analysis

## Integration Points

### With OpenCode Server
- Session management through OpenCode API
- Model routing and execution
- Native agent format support
- Permission and security handling

### With ELF Database
- Event chronicle storage
- Learning capture and retrieval
- Decision tracking
- Performance metrics

### With External Systems
- Dashboard integration
- CLI tools
- Web APIs
- Third-party integrations