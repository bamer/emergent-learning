# OpenELF API Reference

This document provides a comprehensive reference for the OpenELF API, including both internal Python interfaces and external REST endpoints.

## Python API Reference

### AgentOrchestrator Class

The main orchestrator class that manages all agent operations.

#### Constructor
```python
AgentOrchestrator(server_url: str = "http://localhost:4096")
```

**Parameters:**
- `server_url` (str): URL of the OpenCode server

#### Methods

##### `start_orchestrator()`
Initializes and starts the orchestrator system.

```python
def start_orchestrator(self) -> None
```

**Returns:** None

**Example:**
```python
orchestrator = AgentOrchestrator()
orchestrator.start_orchestrator()
```

##### `shutdown()`
Gracefully shuts down the orchestrator and all agents.

```python
def shutdown(self) -> None
```

**Returns:** None

##### `start_agent(agent_type: AgentType) -> bool`
Starts a specific agent type.

```python
def start_agent(self, agent_type: AgentType) -> bool
```

**Parameters:**
- `agent_type` (AgentType): Type of agent to start

**Returns:** bool - True if successful, False otherwise

**Example:**
```python
success = orchestrator.start_agent(AgentType.RESEARCHER)
```

##### `stop_agent(agent_type: AgentType) -> bool`
Stops a specific agent type.

```python
def stop_agent(self, agent_type: AgentType) -> bool
```

**Parameters:**
- `agent_type` (AgentType): Type of agent to stop

**Returns:** bool - True if successful, False otherwise

##### `call_agent(agent_type: AgentType, prompt: str, timeout: int = 300, model: Optional[str] = None) -> Optional[str]`
Calls an agent with a specific prompt.

```python
def call_agent(
    self,
    agent_type: AgentType,
    prompt: str,
    timeout: int = 300,
    model: Optional[str] = None
) -> Optional[str]
```

**Parameters:**
- `agent_type` (AgentType): Type of agent to call
- `prompt` (str): Prompt to send to the agent
- `timeout` (int): Request timeout in seconds (default: 300)
- `model` (Optional[str]): Override model selection

**Returns:** Optional[str] - Agent response or None if failed

**Example:**
```python
response = orchestrator.call_agent(
    AgentType.RESEARCHER,
    "Analyze this code for potential bugs...",
    timeout=600
)
```

##### `get_agent_status() -> Dict[str, Any]`
Gets the current status of all agents.

```python
def get_agent_status(self) -> Dict[str, Any]
```

**Returns:** Dict containing orchestrator status, agent statuses, and statistics

**Example:**
```python
status = orchestrator.get_agent_status()
print(f"Active agents: {status['stats']['agents_started']}")
```

### AgentType Enum

Enumeration of all supported agent types.

```python
class AgentType(Enum):
    ORCHESTRATOR = "orchestrator"
    SENTINEL = "sentinel"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    CREATIVE = "creative"
    CEO = "ceo"
```

### AgentStatus Enum

Enumeration of agent lifecycle states.

```python
class AgentStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    BUSY = "busy"
    ERROR = "error"
    STOPPING = "stopping"
```

### AgentDefinition Class

Structure defining agent configuration.

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
    )
```

**Parameters:**
- `agent_type` (AgentType): Agent type enumeration
- `name` (str): Human-readable agent name
- `description` (str): Brief description of agent purpose
- `icon` (str): Unicode icon for display
- `priority` (int): Priority level (1-10, lower is higher priority)
- `auto_start` (bool): Whether to start automatically
- `session_timeout` (int): Session timeout in seconds

### PersonalityManager Class

Manages agent personalities and configurations.

#### Constructor
```python
PersonalityManager(
    personalities_dir: str = "/home/bamer/.opencode/emergent-learning/agents",
    opencode_agents_dir: str = "/home/bamer/.config/opencode/agents",
    opencode_precedence: bool = False
)
```

**Parameters:**
- `personalities_dir` (str): Directory for ELF personalities
- `opencode_agents_dir` (str): Directory for OpenCode agents
- `opencode_precedence` (bool): Whether OpenCode agents take precedence

#### Methods

##### `load_personality(agent_type: str) -> AgentPersonality`
Loads personality for a specific agent type.

```python
def load_personality(self, agent_type: str) -> AgentPersonality
```

**Parameters:**
- `agent_type` (str): Agent type name

**Returns:** AgentPersonality object

##### `get_optimal_model(agent_type: str, prompt: str, override_model: Optional[str] = None) -> str`
Determines optimal model for agent and prompt.

```python
def get_optimal_model(
    self,
    agent_type: str,
    prompt: str,
    override_model: Optional[str] = None
) -> str
```

**Parameters:**
- `agent_type` (str): Agent type name
- `prompt` (str): Task prompt
- `override_model` (Optional[str]): Model override

**Returns:** str - Optimal model identifier

##### `get_agent_prompt_prefix(agent_type: str) -> str`
Gets prompt prefix for agent personality.

```python
def get_agent_prompt_prefix(self, agent_type: str) -> str
```

**Parameters:**
- `agent_type` (str): Agent type name

**Returns:** str - Formatted prompt prefix

### AgentPersonality Dataclass

Unified structure for agent personalities.

```python
@dataclass
class AgentPersonality:
    role: str
    description: str
    thinking_style: str
    behaviors: Dict[str, Any]
    triggers: Dict[str, Any]
    communication_style: Dict[str, str]
    default_model: str = "opencode/big-pickle"
    alternative_models: Dict[str, Any] = None
    model_selection_criteria: Dict[str, Any] = None
    model_capabilities: Dict[str, Any] = None
    default_timeout: int = 300
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    skills: Optional[List[str]] = None
    plugins: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
```

## REST API Reference

The orchestrator provides a REST API for external integration.

### Base URL
```
http://localhost:8889
```

### Authentication
API endpoints currently do not require authentication. In production environments, implement appropriate authentication mechanisms.

### Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T12:00:00Z"
}
```

#### GET /agents/status
Get current status of all agents.

**Response:**
```json
{
  "orchestrator": {
    "running": true,
    "start_time": "2026-01-31T10:00:00Z"
  },
  "agents": {
    "sentinel": {
      "name": "Sentinel",
      "status": "running",
      "icon": "🔍",
      "session_id": "ses_abc123",
      "error_count": 0
    },
    "researcher": {
      "name": "Researcher",
      "status": "stopped",
      "icon": "🔬",
      "session_id": null,
      "error_count": 0
    }
  },
  "stats": {
    "total_sessions_created": 5,
    "total_messages_sent": 12,
    "agents_started": 3,
    "agents_stopped": 1,
    "errors_handled": 0,
    "uptime_seconds": 7200
  }
}
```

#### POST /agents/start/{agent_type}
Start a specific agent.

**Path Parameters:**
- `agent_type` (string): Type of agent to start (sentinel, researcher, architect, skeptic, creative, ceo)

**Response:**
```json
{
  "success": true,
  "message": "Agent Researcher started successfully",
  "session_id": "ses_def456"
}
```

#### POST /agents/stop/{agent_type}
Stop a specific agent.

**Path Parameters:**
- `agent_type` (string): Type of agent to stop

**Response:**
```json
{
  "success": true,
  "message": "Agent Researcher stopped successfully"
}
```

#### POST /agents/call/{agent_type}
Call an agent with a prompt.

**Path Parameters:**
- `agent_type` (string): Type of agent to call

**Request Body:**
```json
{
  "prompt": "Analyze this code for potential issues...",
  "timeout": 300,
  "model": "opencode/nemotron-v3-coder"
}
```

**Response:**
```json
{
  "success": true,
  "response": "After analyzing the code, I found several potential issues...",
  "model_used": "opencode/nemotron-v3-coder",
  "execution_time": 45.2
}
```

### Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Agent type not found
- `500 Internal Server Error`: Server-side error

**Error Response Format:**
```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE"
}
```

## WebSocket API

Real-time status updates are available via WebSocket.

### Connection
```
ws://localhost:8889/ws
```

### Messages

#### Agent Status Updates
```json
{
  "type": "agent_status_update",
  "data": {
    "agent": "researcher",
    "status": "running",
    "timestamp": "2026-01-31T12:00:00Z"
  }
}
```

#### System Events
```json
{
  "type": "system_event",
  "data": {
    "event": "agent_started",
    "agent": "researcher",
    "timestamp": "2026-01-31T12:00:00Z"
  }
}
```

## Command-Line Interface

OpenELF provides CLI tools for management and interaction.

### orchestrator.py
Main orchestrator control script.

```bash
# Start orchestrator
python orchestrator.py

# Start with specific configuration
python orchestrator.py --server-url http://custom-server:4096
```

### agentctl
Agent control utility.

```bash
# List all agents
agentctl list

# Start specific agent
agentctl start researcher

# Stop specific agent
agentctl stop researcher

# Get agent status
agentctl status

# Call agent with prompt
agentctl call researcher "Analyze this code..."
```

## Environment Variables

### System Configuration
```bash
# OpenCode server URL
OPENCODE_SERVER_URL=http://localhost:4096

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/opencode/orchestrator.log

# Database path
DATABASE_PATH=/home/user/.opencode/emergent-learning/memory/index.db
```

### Agent Configuration
```bash
# Directory paths
ELF_AGENTS_DIR=/home/user/.opencode/emergent-learning/agents
OPENCODE_AGENTS_DIR=/home/user/.config/opencode/agents

# Precedence setting
OPENCODE_PRECEDENCE=false
```

## Configuration Files

### orchestrator.yaml
Main orchestrator configuration.

```yaml
server:
  url: "http://localhost:4096"
  timeout: 30

database:
  path: "/home/user/.opencode/emergent-learning/memory/index.db"
  wal_mode: true

logging:
  level: "INFO"
  file: "/var/log/opencode/orchestrator.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

agents:
  default_timeout: 300
  session_check_interval: 30
  max_restart_attempts: 3
```

### agent_defaults.yaml
Default agent configurations.

```yaml
sentinel:
  priority: 2
  auto_start: true
  session_timeout: 3600
  default_model: "opencode/kimi-k2.5-free"

researcher:
  priority: 4
  auto_start: false
  session_timeout: 7200
  default_model: "opencode/trinity-large-preview-free"
```

## Integration Examples

### Python Client
```python
import requests
import json

class OpenELFClient:
    def __init__(self, base_url="http://localhost:8889"):
        self.base_url = base_url
        
    def get_agent_status(self):
        response = requests.get(f"{self.base_url}/agents/status")
        return response.json()
        
    def call_agent(self, agent_type, prompt, timeout=300):
        data = {
            "prompt": prompt,
            "timeout": timeout
        }
        response = requests.post(
            f"{self.base_url}/agents/call/{agent_type}",
            json=data
        )
        return response.json()

# Usage
client = OpenELFClient()
status = client.get_agent_status()
response = client.call_agent("researcher", "Analyze this code...")
```

### JavaScript Client
```javascript
class OpenELFClient {
    constructor(baseUrl = 'http://localhost:8889') {
        this.baseUrl = baseUrl;
    }
    
    async getAgentStatus() {
        const response = await fetch(`${this.baseUrl}/agents/status`);
        return await response.json();
    }
    
    async callAgent(agentType, prompt, timeout = 300) {
        const response = await fetch(`${this.baseUrl}/agents/call/${agentType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                timeout: timeout
            })
        });
        return await response.json();
    }
}

// Usage
const client = new OpenELFClient();
const status = await client.getAgentStatus();
const response = await client.callAgent('researcher', 'Analyze this code...');
```

This API reference provides comprehensive documentation for integrating with and extending the OpenELF system through its various interfaces.