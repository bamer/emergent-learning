# ELF API Overview

## 🏗️ Architecture

The Emergent Learning Framework (ELF) follows a layered architecture with clearly defined components that communicate through well-defined APIs.

### Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EventBridge (9998)                    │
│  - Listens to OpenCode SSE events                       │
│  - Creates sessions                                     │
│  - Logs events to database                              │
│  - Routes events to LearningProcessor                   │
└────────────────────────┬────────────────────────────────┘
                         │ events
                         ▼
┌─────────────────────────────────────────────────────────┐
│              UnifiedOrchestrator                        │
│  - Receives events via register_listener()              │
│  - Manages services (Learning Capture, Sentinel)        │
│  - Autoservices failed services                         │
│  - Escalates critical issues                            │
└────────────────────────┬────────────────────────────────┘
                         │ health status
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (8888)                     │
│  - Web UI for monitoring                                │
│  - API for creating missions                            │
│  - Displays service status                              │
└─────────────────────────────────────────────────────────┘
```

### API Layers

1. **Infrastructure Layer** (EventBridge)
   - Low-level event processing
   - System health monitoring
   - Basic status endpoints

2. **Orchestration Layer** (UnifiedOrchestrator)
   - Service management
   - Mission coordination
   - Decision making

3. **Application Layer** (Dashboard)
   - User-facing APIs
   - Mission submission
   - Agent management

## 🔌 Communication Patterns

### RESTful APIs
Most ELF components expose RESTful APIs for synchronous communication.

### Event-Driven Architecture
Core components communicate through events using Server-Sent Events (SSE) for real-time updates.

### Database Integration
Components share data through a centralized SQLite database (`memory/index.db`).

## 🔄 Data Flow

1. **Event Ingestion**: OpenCode emits SSE events → EventBridge captures and logs
2. **Processing**: EventBridge routes events to appropriate processors
3. **Decision Making**: UnifiedOrchestrator makes decisions based on events
4. **Action Execution**: Services perform actions based on orchestrator decisions
5. **Feedback Loop**: Results are logged and fed back into the system

## 📊 Database Schema

Events and metrics are stored in `memory/index.db`:

### Table: `metrics`
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    metric_type TEXT,      -- 'event', 'metric', 'log'
    metric_name TEXT,      -- Event type or metric name
    metric_value REAL,     -- Value (often 1 for events)
    tags TEXT,             -- JSON tags for categorization
    context TEXT,          -- Additional context data
    timestamp TEXT         -- ISO timestamp
);
```

### Table: `event_chronicle`
```sql
CREATE TABLE event_chronicle (
    id INTEGER PRIMARY KEY,
    event_type TEXT,
    source TEXT,
    source_id TEXT,
    summary TEXT,
    status TEXT,
    data TEXT,  -- JSON
    timestamp TEXT,
    created_at DATETIME
);
```

## 🛡️ Security Model

### Internal APIs
- Designed for localhost use
- Minimal authentication requirements
- Trusted component communication

### External Integration Points
- Require proper authentication
- Rate limited
- Input validation and sanitization

## 📈 Monitoring and Observability

All components expose health and metrics endpoints:
- `/status` - Basic status information
- `/health` - Detailed health checks
- `/metrics` - Performance and usage metrics

## 🔄 Versioning

APIs follow semantic versioning with the version prefix `/api/v1/`.

### Version Compatibility
- v1.x - Stable, backward-compatible changes
- v2.x - Major breaking changes (when needed)

## 📚 API Design Principles

1. **Consistency**: Uniform naming, structure, and error handling
2. **Simplicity**: Easy to understand and use
3. **Reliability**: Clear error messages and status codes
4. **Performance**: Efficient endpoints with pagination where needed
5. **Security**: Proper input validation and secure defaults
6. **Observability**: Comprehensive logging and monitoring

## 🚀 Getting Started

See the [Quick Start Guide](README.md) for immediate setup instructions.

## 📖 Detailed Documentation

- [Orchestrator API](endpoints/orchestrator/)
- [EventBridge API](endpoints/eventbridge/)
- [Integration APIs](endpoints/integrations/)