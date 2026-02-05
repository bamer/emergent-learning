# OpenELF Configuration Guide

This guide covers all configuration options for the OpenELF plugin system, including agent setup, precedence management, and system customization.

## System Configuration

### Directory Structure

OpenELF uses a standardized directory structure:

```
/home/bamer/.opencode/emergent-learning/
├── agents/                    # ELF agent personalities
│   ├── researcher/
│   │   └── personality.md     # ELF format personality
│   ├── architect.md           # Alternative ELF format
│   └── ...
├── docs/
│   └── openelf/               # This documentation
├── memory/                    # Learning database
├── logs/                      # System logs
└── ceo-inbox/                 # Executive decisions

/home/bamer/.config/opencode/agents/  # OpenCode native agents
├── researcher.md              # OpenCode format agent
├── architect.md               # OpenCode format agent
└── ...
```

### Environment Variables

OpenELF respects standard environment variables:

```bash
# OpenCode server configuration
OPENCODE_SERVER_URL=http://localhost:4096
OPENCODE_API_KEY=your-api-key

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=/home/bamer/.opencode/emergent-learning/logs/orchestrator.log

# Database configuration
DATABASE_PATH=/home/bamer/.opencode/emergent-learning/memory/index.db
```

## Agent Precedence Configuration

Control which agent format takes precedence when conflicts occur.

### Global Precedence Setting

In `orchestrator.py`:

```python
# Initialize Personality Manager with precedence control
if personality_manager_available:
    self.personality_manager = PersonalityManager(
        personalities_dir="/home/bamer/.opencode/emergent-learning/agents",
        opencode_agents_dir="/home/bamer/.config/opencode/agents",
        opencode_precedence=False  # Set to True to prioritize OpenCode agents
    )
else:
    self.personality_manager = None
```

### Precedence Behaviors

| Setting | Behavior | Use Case |
|---------|----------|----------|
| `opencode_precedence=False` (Default) | ELF agents take precedence | Project customization, legacy compatibility |
| `opencode_precedence=True` | OpenCode agents take precedence | Standardization, leveraging ecosystem |

## Agent Configuration Files

### OpenCode Agent Format

Located in `/home/bamer/.config/opencode/agents/`

```markdown
---
name: researcher
description: Deep investigation specialist
model: opencode/nemotron-v3-coder
temperature: 0.6
mode: primary
skills:
  - "code-analysis"
  - "pattern-recognition"
plugins:
  git-history-analyzer:
    enabled: true
    depth: 100
tools:
  - "glob"
  - "grep"
  - "read"
permissions:
  bash:
    "rm -rf *": "ask"
    "rm -rf /*": "deny"
    "sudo *": "deny"
  edit:
    "**/*.env*": "deny"
    "**/*.key": "deny"
---

# Researcher Agent Instructions

Detailed markdown instructions here...
```

### ELF Agent Format

Located in `/home/bamer/.opencode/emergent-learning/agents/`

```yaml
# Basic Information
Role: Researcher Agent
Thinking Style: Thorough and methodical

# Behavioral Configuration
Behaviors:
  search_memory_first: "Always search memory first: 'Have we seen this before?'"
  cite_sources: "Cites sources for claims"
  flag_uncertainty: "Flags uncertainty explicitly"

# Trigger Conditions
Triggers:
  new_problem_domains: "New problem domains"
  unknown_error_messages: "Unknown error messages"
  exploring_solution_spaces: "Exploring solution spaces"

# Communication Preferences
Communication Style:
  verbosity: detailed        # concise | normal | detailed
  formality: professional    # casual | professional | formal
  pattern: report-driven     # conversational | report-driven | question-heavy | directive

# Model Configuration
Model Configuration:
  default_model: opencode/trinity-large-preview-free
  alternative_models:
    fast: opencode/kimi-k2.5-free
    capable: opencode/nemotron-v3-coder
    balanced: opencode/trinity-large-preview-free
  model_selection_criteria:
    complexity_threshold: high
    speed_threshold: medium
    cost_threshold: medium

# Execution Parameters
Execution:
  default_timeout: 600
  max_tokens: null
  temperature: null
```

## Model Selection Configuration

### Agent-Specific Model Settings

Each agent type can define its preferred models:

```python
# In agent_personality_manager.py default personalities
"RESEARCHER": AgentPersonality(
    role="Investigation Agent",
    description="Deep investigation and research",
    thinking_style="Thorough and methodical",
    default_model="opencode/trinity-large-preview-free",
    alternative_models={
        "fast": "opencode/kimi-k2.5-free",
        "balanced": "opencode/trinity-large-preview-free",
        "capable": "opencode/nemotron-v3-coder",
    },
    model_selection_criteria={
        "complexity_threshold": "high",
        "cost_threshold": "medium",
    },
    default_timeout=600,
),
```

### Model Selection Criteria

Criteria used for intelligent model selection:

| Criterion | Values | Purpose |
|-----------|--------|---------|
| `complexity_threshold` | high, medium, low | Task complexity matching |
| `speed_threshold` | high, medium, low | Response time requirements |
| `cost_threshold` | high, medium, low | Budget optimization |
| `risk_threshold` | high, medium, low | Accuracy requirements |
| `creativity_threshold` | high, medium, low | Innovation needs |

## Performance Tuning

### Session Timeout Configuration

Adjust session timeouts per agent type:

```python
# In AgentDefinition
agents[AgentType.SENTINEL] = AgentDefinition(
    agent_type=AgentType.SENTINEL,
    name="Sentinel",
    description="Continuous monitoring and pattern detection",
    icon="🔍",
    priority=2,
    auto_start=True,
    session_timeout=1800,  # 30 minutes for monitoring agent
)
```

### Resource Limits

Configure execution limits:

```yaml
# In ELF agent personality
Execution:
  default_timeout: 600    # 10 minutes
  max_tokens: 4000        # Token limit
  temperature: 0.7        # Creativity level
```

## Security Configuration

### Permission Management

Control agent capabilities through permissions:

```markdown
# In OpenCode agent format
permissions:
  bash:
    "rm -rf *": "ask"      # Require confirmation
    "rm -rf /*": "deny"    # Block dangerous commands
    "sudo *": "deny"       # Block privilege escalation
  edit:
    "**/*.env*": "deny"    # Protect environment files
    "**/*.key": "deny"     # Protect key files
    "node_modules/**": "deny"  # Protect dependencies
```

### Access Control

Fine-grained access control per agent:

```python
# In orchestrator
def call_agent(
    self,
    agent_type: AgentType,
    prompt: str,
    timeout: int = 300,
    model: Optional[str] = None,
):
    # Check if agent is authorized for this operation
    if not self._is_authorized(agent_type, prompt):
        logger.warning(f"Unauthorized access attempt to {agent_type.name}")
        return None
    
    # Proceed with normal execution
    # ...
```

## Logging Configuration

### Log Levels

Configure logging verbosity:

```python
# In orchestrator.py
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/bamer/.opencode/emergent-learning/logs/orchestrator.log"),
        logging.StreamHandler(),
    ],
)
```

### Log File Management

Log rotation and retention:

```bash
# Example log rotation script
0 0 * * * find /home/bamer/.opencode/emergent-learning/logs/ -name "*.log" -mtime +7 -delete
```

## Database Configuration

### Event Chronicle Settings

Database connection and performance:

```python
# In orchestrator
def __init__(self, server_url: str = "http://localhost:4096"):
    self.db_path = "/home/bamer/.opencode/emergent-learning/memory/index.db"
    # ...

def _record_agent_event(...):
    try:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for concurrency
        # ...
```

### Performance Optimization

Database performance tuning:

```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize for frequent writes
PRAGMA synchronous=NORMAL;

-- Cache optimization
PRAGMA cache_size=10000;
```

## API Configuration

### HTTP Server Settings

REST API configuration:

```python
# Example API endpoint configuration
@app.route('/agents/status', methods=['GET'])
def get_agent_status():
    """Get current status of all agents."""
    if not orchestrator:
        return jsonify({"error": "Orchestrator not initialized"}), 500
    
    try:
        status = orchestrator.get_agent_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        return jsonify({"error": "Internal server error"}), 500
```

### CORS and Security

API security configuration:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Restrict to known origins

# Add authentication middleware
@app.before_request
def check_authentication():
    # Implement your authentication logic here
    pass
```

## Monitoring and Metrics

### Health Check Configuration

System health monitoring:

```python
def _monitoring_loop(self):
    """Background monitoring loop for agent health."""
    while self.running and not self.shutdown_event.is_set():
        try:
            # Perform health checks
            self._check_agent_health()
            self._check_system_resources()
            self._check_ceo_inbox()
            
            # Wait before next check
            self.shutdown_event.wait(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self.stats["errors_handled"] += 1
            self.shutdown_event.wait(60)  # Wait longer on error
```

### Metrics Collection

Performance metrics configuration:

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

## Customization Examples

### Project-Specific Agent Override

Create a custom researcher agent in ELF format:

```yaml
# /home/bamer/.opencode/emergent-learning/agents/researcher/personality.md
Role: Project Researcher
Thinking Style: Methodical and Security-Focused

Behaviors:
  security_first: "Always consider security implications"
  code_review_focus: "Prioritize code quality and best practices"

Model Configuration:
  default_model: opencode/nemotron-v3-coder  # Use coding-specialized model
  alternative_models:
    security: opencode/trinity-large-preview-free  # For security analysis
  
Execution:
  default_timeout: 900  # 15 minutes for thorough analysis
  temperature: 0.3      # More deterministic for security reviews
```

### Team Collaboration Setup

Configure for team development:

```python
# In orchestrator initialization
self.personality_manager = PersonalityManager(
    personalities_dir="/shared/team-agents",      # Shared team configurations
    opencode_agents_dir="/home/bamer/.config/opencode/agents",  # Individual agents
    opencode_precedence=False  # Team configs override individual
)
```

### Development vs Production

Environment-specific configuration:

```python
import os

# Development configuration
if os.getenv('ENVIRONMENT') == 'development':
    personality_manager = PersonalityManager(
        opencode_precedence=True,  # Use standard OpenCode agents
        personalities_dir="/dev/elf-agents"  # Development-specific agents
    )
else:
    # Production configuration
    personality_manager = PersonalityManager(
        opencode_precedence=False,  # Use customized production agents
        personalities_dir="/prod/elf-agents"
    )
```

## Troubleshooting Configuration

### Common Issues

1. **Agent not loading**: Check file paths and format consistency
2. **Wrong model selected**: Verify model configuration in personalities
3. **Permission denied**: Review permissions section in agent files
4. **Performance issues**: Adjust timeouts and session configurations

### Diagnostic Commands

```bash
# Check if orchestrator is running
ps aux | grep orchestrator

# View recent logs
tail -f /home/bamer/.opencode/emergent-learning/logs/orchestrator.log

# Test personality loading
python -c "
from agent_personality_manager import PersonalityManager
pm = PersonalityManager()
personality = pm.load_personality('researcher')
print(f'Loaded: {personality.default_model}')
"

# Check database connectivity
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db ".tables"
```

### Configuration Validation

Validate configuration integrity:

```python
def validate_configuration(self):
    """Validate orchestrator configuration."""
    issues = []
    
    # Check required directories
    if not self.personalities_dir.exists():
        issues.append(f"Personalities directory not found: {self.personalities_dir}")
    
    if not self.opencode_agents_dir.exists():
        issues.append(f"OpenCode agents directory not found: {self.opencode_agents_dir}")
    
    # Check database accessibility
    try:
        conn = sqlite3.connect(self.db_path)
        conn.close()
    except Exception as e:
        issues.append(f"Database connection failed: {e}")
    
    return issues
```

This comprehensive configuration guide provides the foundation for customizing and optimizing your OpenELF deployment for any environment or use case.