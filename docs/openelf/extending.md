# Extending OpenELF

OpenELF is designed to be highly extensible, allowing you to add new capabilities, integrate with external systems, and customize behavior to meet your specific needs.

## Adding New Agent Types

### 1. Define the Agent Type

Add a new entry to the `AgentType` enum in `orchestrator.py`:

```python
class AgentType(Enum):
    """Agent types with their roles."""
    ORCHESTRATOR = "orchestrator"
    SENTINEL = "sentinel"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    SKEPTIC = "skeptic"
    CREATIVE = "creative"
    CEO = "ceo"
    # Add your new agent type here
    ANALYST = "analyst"  # Example: Code analysis specialist
```

### 2. Register the Agent Definition

Add the agent definition in `_initialize_agents()`:

```python
# Analyst - Code analysis specialist
agents[AgentType.ANALYST] = AgentDefinition(
    agent_type=AgentType.ANALYST,
    name="Analyst",
    description="Code analysis and quality assessment",
    icon="📊",
    priority=3,
    auto_start=False,  # Start only when needed
    session_timeout=3600,
)
```

### 3. Create the Personality File

Create either an OpenCode or ELF personality file:

**OpenCode Format** (`/home/bamer/.config/opencode/agents/analyst.md`):
```markdown
---
name: analyst
description: Code analysis and quality assessment specialist
model: opencode/nemotron-v3-coder
temperature: 0.4
mode: primary
skills:
  - "static-analysis"
  - "code-quality"
  - "security-audit"
tools:
  - "glob"
  - "grep"
  - "read"
  - "edit"
---

# Analyst Agent - Code Quality Specialist

You are the Analyst Agent, specializing in code analysis and quality assessment.

## Responsibilities
1. Static code analysis
2. Code quality metrics
3. Security vulnerability detection
4. Performance optimization suggestions

[... detailed instructions ...]
```

### 4. Update Call Logic (Optional)

If you need special handling for the new agent:

```python
# In _send_agent_message or call_agent
elif agent.agent_type == AgentType.ANALYST:
    full_prompt = f"@analyst\n\nYou are the Analyst code quality agent. {prompt}"
```

## Adding Skills to Agents

### 1. Define Skills in Personality

Add skills to existing agents:

**OpenCode Format:**
```markdown
---
name: researcher
skills:
  - "code-analysis"
  - "pattern-recognition"
  - "root-cause-analysis"
  - "documentation-search"
  - "new-skill-name"  # Your new skill
---
```

**ELF Format:**
```yaml
Skills:
  - "code-analysis"
  - "pattern-recognition"
  - "new-skill-name"  # Your new skill
```

### 2. Implement Skill Logic

Use skills in personality manager decisions:

```python
# In agent_personality_manager.py
def get_optimal_model(self, agent_type: str, prompt: str, override_model: Optional[str] = None) -> str:
    personality = self.load_personality(agent_type)
    
    # Check for specific skills
    if personality.skills and "security-audit" in personality.skills:
        # Use security-focused model
        return "opencode/trinity-large-preview-free"
    
    # Default model selection logic
    # ...
```

### 3. Skill-Based Routing

Implement skill-based task routing:

```python
def route_to_skilled_agent(self, task: str, required_skills: List[str]) -> Optional[AgentType]:
    """Route task to agent with required skills."""
    for agent_type in AgentType:
        personality = self.personality_manager.load_personality(agent_type.value)
        if personality.skills and all(skill in personality.skills for skill in required_skills):
            return agent_type
    return None
```

## Creating Plugins

### 1. Plugin Structure

Create a plugin module in `/home/bamer/.opencode/emergent-learning/plugins/`:

```python
# plugins/code_analyzer.py
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CodeAnalyzerPlugin:
    """Plugin for advanced code analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.analysis_depth = config.get('analysis_depth', 5)
        
    def analyze_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """Perform code analysis."""
        if not self.enabled:
            return {}
            
        results = {
            'complexity': self._calculate_complexity(code),
            'security_issues': self._check_security(code),
            'performance_tips': self._suggest_performance(code),
        }
        
        logger.info(f"Analyzed {file_path}: {len(results['security_issues'])} issues found")
        return results
        
    def _calculate_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        # Implementation here
        return {'cyclomatic_complexity': 10, 'lines_of_code': len(code.split('\n'))}
        
    def _check_security(self, code: str) -> List[Dict[str, Any]]:
        """Check for security vulnerabilities."""
        # Implementation here
        return []
        
    def _suggest_performance(self, code: str) -> List[str]:
        """Suggest performance optimizations."""
        # Implementation here
        return []
```

### 2. Plugin Integration

Integrate plugin with personality manager:

```python
# In agent_personality_manager.py
from plugins.code_analyzer import CodeAnalyzerPlugin

class PersonalityManager:
    def __init__(self, ...):
        self.plugins = {}
        self._load_plugins()
        
    def _load_plugins(self):
        """Load configured plugins."""
        # Example plugin loading
        analyst_personality = self.load_personality("analyst")
        if analyst_personality.plugins and 'code-analyzer' in analyst_personality.plugins:
            config = analyst_personality.plugins['code-analyzer']
            self.plugins['code-analyzer'] = CodeAnalyzerPlugin(config)
```

### 3. Plugin Usage

Use plugins in agent execution:

```python
# In orchestrator or agent execution logic
def execute_analysis_task(self, agent_type: AgentType, code: str, file_path: str):
    """Execute analysis task with plugins."""
    personality = self.personality_manager.load_personality(agent_type.value)
    
    # Use code analyzer plugin if available
    if 'code-analyzer' in self.personality_manager.plugins:
        plugin = self.personality_manager.plugins['code-analyzer']
        analysis_results = plugin.analyze_code(code, file_path)
        return analysis_results
    
    # Fallback to basic analysis
    return self._basic_code_analysis(code)
```

## Custom Tools Integration

### 1. Tool Definition

Define custom tools in agent personalities:

```markdown
---
name: researcher
tools:
  - "glob"
  - "grep"
  - "read"
  - "custom-tool-name"  # Your custom tool
---
```

### 2. Tool Implementation

Create tool wrapper functions:

```python
# tools/custom_tool.py
import subprocess
import json
from typing import Dict, Any

def custom_tool_execute(command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute custom tool."""
    try:
        # Your tool implementation
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### 3. Tool Registration

Register tools with the orchestrator:

```python
# In orchestrator
class AgentOrchestrator:
    def __init__(self):
        self.custom_tools = {
            'custom-tool-name': custom_tool_execute,
            # Add more tools
        }
        
    def _send_agent_message(self, agent: AgentDefinition, prompt: str, timeout: int):
        # Prepend tool availability information
        if agent.agent_type == AgentType.RESEARCHER:
            personality = self.personality_manager.load_personality(agent.agent_type.value)
            available_tools = ', '.join(personality.tools or [])
            tool_info = f"\n\nAvailable tools: {available_tools}"
            full_prompt = prompt + tool_info
```

## Model Provider Integration

### 1. Adding New Model Providers

Extend model support in personality manager:

```python
# In agent_personality_manager.py
def _parse_model_string(self, model_string: str) -> tuple:
    """Parse model string into provider and model ID."""
    if "/" in model_string:
        provider, model_id = model_string.split("/", 1)
    else:
        # Default to opencode
        provider, model_id = "opencode", model_string
        
    # Support for new providers
    provider_mapping = {
        "opencode": "opencode",
        "openai": "openai",
        "anthropic": "anthropic",
        "google": "google",
        # Add your custom provider mapping
        "custom-provider": "custom_provider_id"
    }
    
    return provider_mapping.get(provider, provider), model_id
```

### 2. Custom Model Routing

Implement custom model routing logic:

```python
def get_optimal_model(self, agent_type: str, prompt: str, override_model: Optional[str] = None) -> str:
    """Get optimal model with custom provider support."""
    if override_model:
        return override_model
        
    personality = self.load_personality(agent_type)
    
    # Custom routing logic for specific providers
    if "custom-provider" in self._get_available_providers():
        # Use custom provider for certain tasks
        if agent_type == "ANALYST" and len(prompt) > 1000:
            return "custom-provider/specialized-model"
            
    # Default routing
    return personality.default_model
```

## Event Handling Extensions

### 1. Custom Event Types

Add new event types to the system:

```python
# Extend event handling in orchestrator
def _record_custom_event(self, event_type: str, agent_type: AgentType, data: Dict[str, Any]):
    """Record custom event types."""
    self._record_agent_event(
        agent_type,
        event_type,  # e.g., "code_analysis_complete", "security_alert"
        f"Custom event: {event_type}",
        data
    )
```

### 2. Event Hooks

Implement event hooks for extensibility:

```python
class EventHandler:
    """Base class for event handlers."""
    def handle_event(self, event_type: str, data: Dict[str, Any]):
        raise NotImplementedError

class NotificationEventHandler(EventHandler):
    """Send notifications for specific events."""
    def handle_event(self, event_type: str, data: Dict[str, Any]):
        if event_type == "security_alert":
            self._send_notification(data)
            
    def _send_notification(self, data: Dict[str, Any]):
        # Implementation for sending alerts
        pass

# Register event handlers
self.event_handlers = [
    NotificationEventHandler(),
    # Add more handlers
]
```

## API Extensions

### 1. Custom API Endpoints

Add new REST API endpoints:

```python
# In orchestrator API
@app.route('/agents/analyst/analyze', methods=['POST'])
def analyze_code():
    """Custom endpoint for code analysis."""
    if not orchestrator:
        return jsonify({"error": "Orchestrator not initialized"}), 500
        
    try:
        data = request.get_json()
        code = data.get('code')
        file_path = data.get('file_path', 'unknown')
        
        # Execute analysis with Analyst agent
        result = orchestrator.call_agent(
            AgentType.ANALYST,
            f"Analyze this code:\n\n{code}",
            timeout=300
        )
        
        return jsonify({
            'analysis': result,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        return jsonify({"error": "Analysis failed"}), 500
```

### 2. WebSocket Integration

Add real-time communication capabilities:

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('agent_status_subscribe')
def handle_agent_status_subscription():
    """Subscribe to real-time agent status updates."""
    def status_update_callback(status):
        emit('agent_status_update', status)
        
    # Register callback for status updates
    orchestrator.register_status_callback(status_update_callback)
```

## Dashboard Extensions

### 1. Custom Dashboard Widgets

Add new visualization components:

```javascript
// In dashboard frontend
class CustomWidget extends React.Component {
    componentDidMount() {
        // Fetch custom data
        this.fetchCustomData();
    }
    
    fetchCustomData = async () => {
        const response = await fetch('/api/agents/analyst/metrics');
        const data = await response.json();
        this.setState({ metrics: data });
    }
    
    render() {
        return (
            <div className="widget">
                <h3>Code Analysis Metrics</h3>
                <MetricsChart data={this.state.metrics} />
            </div>
        );
    }
}
```

### 2. Plugin Dashboard Integration

Integrate plugin data into dashboard:

```python
# Backend endpoint for plugin data
@app.route('/api/plugins/code-analyzer/metrics', methods=['GET'])
def get_code_analyzer_metrics():
    """Get metrics from code analyzer plugin."""
    try:
        # Get plugin instance
        plugin = orchestrator.personality_manager.plugins.get('code-analyzer')
        if not plugin:
            return jsonify({"error": "Plugin not available"}), 404
            
        # Get metrics
        metrics = plugin.get_current_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Failed to get plugin metrics: {e}")
        return jsonify({"error": "Failed to retrieve metrics"}), 500
```

## Testing Extensions

### 1. Custom Test Framework

Add testing capabilities for extensions:

```python
# tests/test_analyst_agent.py
import unittest
from agents.orchestrator import AgentOrchestrator
from agents.agent_personality_manager import PersonalityManager

class TestAnalystAgent(unittest.TestCase):
    def setUp(self):
        self.personality_manager = PersonalityManager()
        self.orchestrator = AgentOrchestrator()
        
    def test_analyst_personality_loading(self):
        """Test that analyst personality loads correctly."""
        personality = self.personality_manager.load_personality('analyst')
        self.assertIsNotNone(personality)
        self.assertIn('code-analysis', personality.skills or [])
        
    def test_analyst_model_selection(self):
        """Test analyst model selection logic."""
        model = self.personality_manager.get_optimal_model(
            'analyst', 
            'Analyze this complex security issue...'
        )
        self.assertEqual(model, 'opencode/trinity-large-preview-free')
```

### 2. Integration Testing

Test plugin integration:

```python
def test_plugin_integration(self):
    """Test plugin integration with orchestrator."""
    # Start analyst agent
    success = self.orchestrator.start_agent(AgentType.ANALYST)
    self.assertTrue(success)
    
    # Test plugin functionality through agent
    result = self.orchestrator.call_agent(
        AgentType.ANALYST,
        "Analyze code for security vulnerabilities"
    )
    
    # Verify plugin results
    self.assertIsNotNone(result)
    # Add specific assertions based on expected plugin behavior
```

## Deployment Extensions

### 1. Containerization

Create Docker configuration for custom extensions:

```dockerfile
# Dockerfile.custom
FROM opencode/elf-base:latest

# Install custom dependencies
RUN pip install custom-dependency-package

# Copy custom plugins
COPY plugins/ /app/plugins/
COPY agents/custom/ /app/agents/

# Expose custom ports if needed
EXPOSE 8080

# Start with custom configuration
CMD ["python", "orchestrator.py", "--config", "/app/config/custom.yaml"]
```

### 2. Configuration Management

Manage extension configurations:

```yaml
# config/extensions.yaml
extensions:
  code_analyzer:
    enabled: true
    provider: "custom-provider"
    models:
      - "specialized-code-model"
      - "security-analysis-model"
      
  notification_service:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
plugins:
  git_history_analyzer:
    enabled: true
    depth: 1000
    
  dependency_checker:
    enabled: true
    vulnerability_scanner: "custom-scanner"
```

This extension guide provides a comprehensive framework for customizing and extending OpenELF to meet your specific requirements while maintaining compatibility with the core system.