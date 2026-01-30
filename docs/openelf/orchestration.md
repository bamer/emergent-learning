# OpenELF Orchestration System

The Agent Orchestrator is the central nervous system of OpenELF, responsible for coordinating all agent activities, managing lifecycles, and ensuring system stability.

## Core Responsibilities

### Agent Lifecycle Management
- **Startup**: Initialize agents based on configuration
- **Monitoring**: Continuously track agent health and performance
- **Recovery**: Automatically restart failed agents with exponential backoff
- **Shutdown**: Gracefully terminate agents and clean up resources

### Session Management
- **Creation**: Establish OpenCode sessions for each agent
- **Maintenance**: Keep sessions alive and healthy
- **Timeout**: Automatically clean up idle sessions
- **Error Handling**: Recover from session failures

### Communication Coordination
- **Message Routing**: Direct prompts to appropriate agents
- **Response Handling**: Process and return agent responses
- **Model Selection**: Choose optimal models per task
- **Prompt Enhancement**: Add personality-specific prefixes

### System Integration
- **CEO Inbox**: Monitor and process executive decisions
- **Pattern Detection**: Identify and respond to system patterns
- **Event Logging**: Record all activities for analysis
- **Health Checks**: Maintain system-wide awareness

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Lifecycle     │  │   Sessions      │  │  Messaging  │ │
│  │   Manager       │  │   Manager       │  │   Router    │ │
│  │                 │  │                 │  │             │ │
│  │ • Start/Stop    │  │ • Create/Delete │  │ • Route     │ │
│  │ • Health Check  │  │ • Keep-alive    │  │ • Format    │ │
│  │ • Auto-restart  │  │ • Timeout       │  │ • Model Sel │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Monitoring    │  │  Integration    │  │   Storage   │ │
│  │                 │  │                 │  │             │ │
│  │ • Health Loop   │  │ • CEO Inbox     │  │ • Events    │ │
│  │ • Pattern Det   │  │ • Building Int  │  │ • Metrics   │ │
│  │ • Perf Metrics  │  │ • APIs          │  │ • Logs      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Agent Definitions

The orchestrator manages agents through structured definitions:

```python
class AgentDefinition:
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        description: str,
        icon: str,
        priority: int = 5,
        auto_start: bool = False,
        session_timeout: int = 3600,
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.icon = icon
        self.priority = priority  # 1=highest, 10=lowest
        self.auto_start = auto_start
        self.session_timeout = session_timeout  # seconds
        self.status = AgentStatus.STOPPED
        self.session_id = None
        self.last_activity = None
        self.start_time = None
        self.error_count = 0
        self.metadata = {}
```

## Agent Status Lifecycle

Agents transition through well-defined states:

```python
class AgentStatus(Enum):
    STOPPED = "stopped"     # Agent is not running
    STARTING = "starting"   # Agent initialization in progress
    RUNNING = "running"     # Agent is active and ready
    BUSY = "busy"          # Agent is processing a task
    ERROR = "error"        # Agent encountered an error
    STOPPING = "stopping"   # Agent shutdown in progress
```

State transitions:
```
STOPPED → STARTING → RUNNING ↔ BUSY
   ↑         ↓         ↓       ↑
   └───── ERROR ←──────┴───────┘
   ↑         ↓
STOPPING ←────┘
```

## Standard Agent Types

| Type | Name | Priority | Auto-Start | Description |
|------|------|----------|------------|-------------|
| ORCHESTRATOR | ELF Orchestrator | 1 | True | Central coordination |
| SENTINEL | Sentinel | 2 | True | Monitoring and pattern detection |
| RESEARCHER | Researcher | 4 | False | Deep investigation |
| ARCHITECT | Architect | 5 | False | System design |
| SKEPTIC | Skeptic | 6 | False | Critical analysis |
| CREATIVE | Creative | 7 | False | Innovation generation |
| CEO | CEO | 1 | False | Executive decisions |

## Session Management

### Session Creation

```python
def _create_agent_session(self, agent: AgentDefinition) -> Optional[Dict[str, Any]]:
    """Create OpenCode session for an agent."""
    response = requests.post(
        f"{self.server_url}/session",
        json={"title": f"ELF Agent: {agent.name}"},
        timeout=10,
    )
    
    if response.status_code == 200:
        session_data = response.json()
        self.stats["total_sessions_created"] += 1
        return session_data
    else:
        logger.error(f"Failed to create session for {agent.name}: {response.status_code}")
        return None
```

### Session Maintenance

The orchestrator continuously monitors session health:

```python
def _monitoring_loop(self):
    """Background monitoring loop for agent health."""
    while self.running and not self.shutdown_event.is_set():
        current_time = datetime.now()
        
        for agent_type, agent in self.agents.items():
            if agent.status == AgentStatus.RUNNING:
                # Check for session timeout
                if agent.last_activity and agent.session_timeout:
                    idle_time = (current_time - agent.last_activity).total_seconds()
                    if idle_time > agent.session_timeout:
                        logger.info(f"⏰ Agent {agent.name} session timeout, stopping...")
                        self.stop_agent(agent_type)
            
            elif agent.status == AgentStatus.ERROR:
                # Try to restart errored agents (with backoff)
                if agent.error_count < 3:  # Max 3 restart attempts
                    wait_time = min(60, 10 * agent.error_count)  # Exponential backoff
                    if (agent.last_activity and 
                        (current_time - agent.last_activity).total_seconds() > wait_time):
                        logger.info(f"🔄 Attempting to restart errored agent {agent.name}...")
                        agent.status = AgentStatus.STOPPED
                        self.start_agent(agent_type)
```

## Communication System

### Model Selection Integration

The orchestrator leverages the personality manager for intelligent model selection:

```python
def call_agent(
    self,
    agent_type: AgentType,
    prompt: str,
    timeout: int = 300,
    model: Optional[str] = None,
) -> Optional[str]:
    # Determine optimal model using personality manager
    target_model = "opencode/big-pickle"  # fallback
    if self.personality_manager and personality_manager_available:
        target_model = self.personality_manager.get_optimal_model(
            agent_type.name, prompt, model
        )
        logger.info(f"🧠 Personality-selected model for {agent.name}: {target_model}")
    
    # Get prompt prefix from personality manager
    if self.personality_manager and personality_manager_available:
        prompt_prefix = self.personality_manager.get_agent_prompt_prefix(
            agent_type.name
        )
        full_prompt = f"{prompt_prefix}\n\n{prompt}"
```

### Message Formatting

Agents receive formatted prompts based on their type:

```python
# Parse model string for API
provider, model_id = "opencode", "big-pickle"
if "/" in target_model:
    provider, model_id = target_model.split("/", 1)
else:
    provider, model_id = "opencode", target_model

message_data = {
    "model": {"providerID": provider, "modelID": model_id},
    "parts": [{"type": "text", "text": full_prompt}],
}
```

## CEO Inbox Integration

The orchestrator automatically processes executive decisions:

```python
def _check_ceo_inbox(self) -> List[str]:
    """Check CEO inbox for pending decisions."""
    inbox_path = Path("/home/bamer/.opencode/emergent-learning/ceo-inbox")
    if not inbox_path.exists():
        return []

    # Get all .md files in inbox (unprocessed)
    inbox_items = []
    for file_path in inbox_path.glob("*.md"):
        inbox_items.append(str(file_path))
    return inbox_items

def _notify_ceo_of_inbox(self, inbox_items: List[str]):
    """Notify CEO agent about pending inbox items."""
    if not inbox_items:
        return

    # Build notification prompt
    items_summary = []
    for item_path in inbox_items:
        filename = Path(item_path).name
        items_summary.append(f"- {filename}")

    prompt = f"""
🚨 **CEO INBOX ALERT**

You have {len(inbox_items)} pending decision(s) requiring immediate attention:

{chr(10).join(items_summary)}

Please review and provide decisions on each item.
Items are located in: /home/bamer/.opencode/emergent-learning/ceo-inbox/

Priority: CRITICAL - System stability issues require executive decisions.
"""

    # Call CEO agent with notification
    response = self.call_agent(
        AgentType.CEO,
        prompt,
        timeout=600,  # 10 minutes for complex decisions
    )
```

## Health Monitoring

### Continuous Monitoring Loop

```python
def _monitoring_loop(self):
    """Background monitoring loop for agent health."""
    logger.info("🔍 Starting agent monitoring loop")

    while self.running and not self.shutdown_event.is_set():
        try:
            # Check agent health
            current_time = datetime.now()

            for agent_type, agent in self.agents.items():
                if agent.status == AgentStatus.RUNNING:
                    # Check for session timeout
                    if agent.last_activity and agent.session_timeout:
                        idle_time = (current_time - agent.last_activity).total_seconds()
                        if idle_time > agent.session_timeout:
                            logger.info(f"⏰ Agent {agent.name} session timeout, stopping...")
                            self.stop_agent(agent_type)

                elif agent.status == AgentStatus.ERROR:
                    # Try to restart errored agents (with backoff)
                    if agent.error_count < 3:  # Max 3 restart attempts
                        wait_time = min(60, 10 * agent.error_count)  # Exponential backoff
                        if (agent.last_activity and 
                            (current_time - agent.last_activity).total_seconds() > wait_time):
                            logger.info(f"🔄 Attempting to restart errored agent {agent.name}...")
                            agent.status = AgentStatus.STOPPED
                            self.start_agent(agent_type)

            # Check CEO inbox
            self._check_ceo_inbox_and_notify()

            # Sleep before next check
            self.shutdown_event.wait(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.stats["errors_handled"] += 1
            self.shutdown_event.wait(60)  # Wait longer on error
```

### Performance Metrics

The orchestrator tracks comprehensive statistics:

```python
self.stats = {
    "total_sessions_created": 0,
    "total_messages_sent": 0,
    "agents_started": 0,
    "agents_stopped": 0,
    "errors_handled": 0,
    "uptime_seconds": 0,
}
```

## API Integration

### Status Reporting

```python
def get_agent_status(self):
    """Get current status of all agents."""
    agent_statuses = {}
    for agent_type, agent in self.agents.items():
        agent_statuses[agent_type.value] = {
            "name": agent.name,
            "status": agent.status.value,
            "icon": agent.icon,
            "session_id": agent.session_id,
            "error_count": agent.error_count,
        }
    
    return {
        "orchestrator": {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
        },
        "agents": agent_statuses,
        "stats": self.stats.copy(),
    }
```

### External Control

The orchestrator can be controlled programmatically:

```python
# Start an agent
orchestrator.start_agent(AgentType.RESEARCHER)

# Stop an agent
orchestrator.stop_agent(AgentType.RESEARCHER)

# Call an agent
response = orchestrator.call_agent(
    AgentType.RESEARCHER, 
    "Analyze this code for potential issues..."
)

# Get system status
status = orchestrator.get_agent_status()
```

## Configuration Options

### Agent Definition Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_type` | AgentType | Required | Agent type enumeration |
| `name` | str | Required | Human-readable name |
| `description` | str | Required | Brief description |
| `icon` | str | Required | Unicode icon for display |
| `priority` | int | 5 | Priority level (1-10) |
| `auto_start` | bool | False | Start automatically |
| `session_timeout` | int | 3600 | Session timeout in seconds |

### System-Wide Settings

```python
# Server configuration
server_url: str = "http://localhost:4096"

# Database path
db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/bamer/.opencode/emergent-learning/logs/orchestrator.log"),
        logging.StreamHandler(),
    ],
)
```

## Error Handling and Recovery

### Graceful Degradation

The orchestrator handles various failure scenarios:

```python
def start_agent(self, agent_type: AgentType) -> bool:
    """Start a specific agent."""
    try:
        logger.info(f"🚀 Starting agent: {agent.name}")
        agent.status = AgentStatus.STARTING

        # Create OpenCode session for the agent
        session_data = self._create_agent_session(agent)

        if session_data:
            agent.session_id = session_data["id"]
            agent.status = AgentStatus.RUNNING
            agent.last_activity = datetime.now()
            # ... success handling ...
            return True
        else:
            agent.status = AgentStatus.ERROR
            agent.error_count += 1
            logger.error(f"❌ Failed to start agent {agent.name}")
            return False

    except Exception as e:
        agent.status = AgentStatus.ERROR
        agent.error_count += 1
        logger.error(f"❌ Exception starting agent {agent.name}: {e}")
        self.stats["errors_handled"] += 1
        return False
```

### Exponential Backoff

Errored agents are restarted with increasing delays:

```python
# Try to restart errored agents (with backoff)
if agent.error_count < 3:  # Max 3 restart attempts
    wait_time = min(60, 10 * agent.error_count)  # Exponential backoff
    if (agent.last_activity and 
        (current_time - agent.last_activity).total_seconds() > wait_time):
        logger.info(f"🔄 Attempting to restart errored agent {agent.name}...")
        agent.status = AgentStatus.STOPPED
        self.start_agent(agent_type)
```

## Integration Points

### With Personality Manager

```python
# Initialize Personality Manager with OpenCode precedence
if personality_manager_available:
    self.personality_manager = PersonalityManager(
        opencode_precedence=False  # Set to True to prioritize OpenCode agents
    )
else:
    self.personality_manager = None
```

### With Event Chronicle

```python
def _record_agent_event(
    self,
    agent_type: AgentType,
    event_type: str,
    summary: str,
    data: Dict[str, Any] = None,
):
    """Record agent-specific events to database."""
    try:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO event_chronicle (timestamp, event_type, source, source_id, status, summary, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                event_type,
                "agent_orchestrator",
                agent_type.value,
                "completed",
                summary,
                json.dumps(data) if data else None,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
```

This comprehensive orchestration system provides robust, scalable agent management while maintaining flexibility for customization and extension.