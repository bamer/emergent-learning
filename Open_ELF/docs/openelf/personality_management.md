# OpenELF Personality Management

The Personality Manager is the core component responsible for loading, managing, and configuring agent personalities in OpenELF. It seamlessly integrates support for both ELF and OpenCode agent formats.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Personality Manager                    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   ELF Loader    │  │   OpenCode Loader       │  │
│  │                 │  │                         │  │
│  │ • Parse YAML    │  │ • Parse Frontmatter     │  │
│  │ • Legacy Format │  │ • Native Format         │  │
│  └─────────────────┘  └─────────────────────────┘  │
│                           │                        │
│                           ▼                        │
│  ┌─────────────────────────────────────────────────┐│
│  │              AgentPersonality                   ││
│  │                                                 ││
│  │ • Unified data structure                        ││
│  │ • Format-agnostic fields                        ││
│  │ • Extended capabilities                         ││
│  └─────────────────────────────────────────────────┘│
│                           │                        │
│                           ▼                        │
│  ┌─────────────────────────────────────────────────┐│
│  │              Model Selection                    ││
│  │                                                 ││
│  │ • Intelligent routing                           ││
│  │ • Context-aware decisions                       ││
│  │ • Performance optimization                      ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## AgentPersonality Data Structure

The `AgentPersonality` class provides a unified interface for all agent configurations:

```python
@dataclass
class AgentPersonality:
    # Basic info
    role: str
    description: str
    thinking_style: str

    # Behaviors
    behaviors: Dict[str, Any]
    triggers: Dict[str, Any]
    communication_style: Dict[str, str]

    # Model configuration
    default_model: str = "opencode/big-pickle"
    alternative_models: Dict[str, Any] = None
    model_selection_criteria: Dict[str, Any] = None

    # Model capabilities
    model_capabilities: Dict[str, Any] = None

    # Execution preferences
    default_timeout: int = 300
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    # Extended capabilities
    skills: Optional[List[str]] = None
    plugins: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
```

## Loading Mechanism

### File Resolution

The personality manager searches for agent files in a specific order:

```python
# With ELF precedence (default)
personality_locations = [
    # ELF format locations
    self.personalities_dir / agent_type.lower() / "personality.md",
    self.personalities_dir / f"{agent_type.lower()}.md",
    # OpenCode format locations
    self.opencode_agents_dir / f"{agent_type.lower()}.md",
]

# With OpenCode precedence
personality_locations = [
    # OpenCode format locations
    self.opencode_agents_dir / f"{agent_type.lower()}.md",
    # ELF format locations
    self.personalities_dir / agent_type.lower() / "personality.md",
    self.personalities_dir / f"{agent_type.lower()}.md",
]
```

### Parsing Logic

The system automatically detects format based on content structure:

```python
# Detect OpenCode format
if "model" in yaml_content and "name" in yaml_content:
    # Parse as OpenCode format
    personality = AgentPersonality(
        role=yaml_content.get("name"),
        description=yaml_content.get("description"),
        default_model=yaml_content.get("model"),
        temperature=yaml_content.get("temperature"),
        skills=yaml_content.get("skills", []),
        plugins=yaml_content.get("plugins", {}),
        tools=yaml_content.get("tools", []),
        # ... other fields
    )
else:
    # Parse as ELF format
    personality = AgentPersonality(
        role=yaml_content.get("Role"),
        thinking_style=yaml_content.get("Thinking Style"),
        behaviors=yaml_content.get("Behaviors", {}),
        # ... other fields
    )
```

## Extended Capabilities

### Skills System

Agents can declare specific skills that enable specialized behaviors:

```yaml
# OpenCode format
skills:
  - "code-analysis"
  - "pattern-recognition"
  - "root-cause-analysis"
  - "documentation-search"
```

Skills can be used for:
- Task routing
- Capability matching
- Performance optimization
- Specialized tool selection

### Plugins Integration

Plugin configurations allow for extensible functionality:

```yaml
plugins:
  git-history-analyzer:
    enabled: true
    depth: 100
  dependency-mapper:
    scan_depth: 3
```

### Tools Availability

Declare available tools for agent use:

```yaml
tools:
  - "glob"
  - "grep"
  - "read"
  - "edit"
  - "bash"
```

## Model Selection Intelligence

The personality manager includes sophisticated model selection logic:

### Criteria-Based Selection

```python
def get_optimal_model(self, agent_type: str, prompt: str, override_model: Optional[str] = None) -> str:
    # Use override if provided
    if override_model:
        return override_model

    # Analyze prompt characteristics
    prompt_length = len(prompt)
    prompt_words = len(prompt.split())

    # Agent-specific logic
    if agent_type == "RESEARCHER":
        if prompt_length > 800:
            return "opencode/nemotron-v3-coder"  # High capability for complex analysis
        elif prompt_length > 500:
            return "opencode/trinity-large-preview-free"  # Comprehensive analysis
    elif agent_type == "SENTINEL":
        if prompt_words < 20:
            return "opencode/gpt-5-nano"  # Ultra-fast for simple checks
```

### Performance Optimization

Models are selected based on:
- **Task Complexity**: Longer prompts may require more capable models
- **Response Time**: Fast models for simple queries
- **Cost Efficiency**: Lower-cost models for routine tasks
- **Capability Matching**: Specialized models for specific tasks

## Configuration API

### Initialization

```python
from agent_personality_manager import PersonalityManager

# Default configuration
pm = PersonalityManager()

# Custom directories
pm = PersonalityManager(
    personalities_dir="/custom/elf/agents",
    opencode_agents_dir="/custom/opencode/agents"
)

# OpenCode precedence
pm = PersonalityManager(opencode_precedence=True)
```

### Runtime Methods

```python
# Load personality
personality = pm.load_personality("researcher")

# Get optimal model
model = pm.get_optimal_model("researcher", "Analyze this complex code...")

# Get execution configuration
config = pm.get_execution_config("researcher", "opencode/nemotron-v3-coder")

# Get prompt prefix
prefix = pm.get_agent_prompt_prefix("researcher")

# List available models
models = pm.list_available_models("researcher")

# Get all OpenCode models
all_models = pm.get_all_available_opencode_models()
```

## Caching and Performance

The personality manager implements intelligent caching:

```python
class PersonalityManager:
    def __init__(self):
        self.cache: Dict[str, AgentPersonality] = {}  # In-memory cache
    
    def load_personality(self, agent_type: str) -> AgentPersonality:
        # Return cached version if available
        if agent_type in self.cache:
            return self.cache[agent_type]
        
        # Load and cache new personality
        personality = self._load_from_file(agent_type)
        self.cache[agent_type] = personality
        return personality
```

## Error Handling

Robust error handling ensures system stability:

```python
def load_personality(self, agent_type: str) -> AgentPersonality:
    try:
        # Attempt to load personality
        content = personality_file.read_text()
        # ... parsing logic ...
        return personality
    except FileNotFoundError:
        # Fall back to default personality
        logger.warning(f"No personality file found for {agent_type}")
        return self._get_default_personality(agent_type)
    except yaml.YAMLError as e:
        # Handle YAML parsing errors
        logger.warning(f"Failed to parse YAML for {agent_type}: {e}")
        return self._get_default_personality(agent_type)
    except Exception as e:
        # Handle other errors
        logger.error(f"Failed to load personality for {agent_type}: {e}")
        return self._get_default_personality(agent_type)
```

## Default Personalities

Fallback personalities ensure system functionality even when files are missing:

```python
defaults = {
    "SENTINEL": AgentPersonality(
        role="Monitoring Agent",
        description="System monitoring and health checks",
        thinking_style="Alert and analytical",
        default_model="opencode/kimi-k2.5-free",
        alternative_models={
            "fast": "opencode/gpt-5-nano",
            "balanced": "opencode/gpt-5-mini",
        },
        default_timeout=300,
    ),
    "RESEARCHER": AgentPersonality(
        role="Investigation Agent",
        description="Deep investigation and research",
        thinking_style="Thorough and methodical",
        default_model="opencode/trinity-large-preview-free",
        alternative_models={
            "fast": "opencode/kimi-k2.5-free",
            "capable": "opencode/nemotron-v3-coder",
        },
        default_timeout=600,
    ),
    # ... other defaults ...
}
```

## Integration with Orchestrator

The orchestrator seamlessly integrates with the personality manager:

```python
class AgentOrchestrator:
    def call_agent(self, agent_type: AgentType, prompt: str, model: Optional[str] = None):
        # Get optimal model using personality manager
        target_model = self.personality_manager.get_optimal_model(
            agent_type.name, prompt, model
        )
        
        # Get prompt prefix
        prompt_prefix = self.personality_manager.get_agent_prompt_prefix(
            agent_type.name
        )
        
        # Get execution configuration
        exec_config = self.personality_manager.get_execution_config(
            agent_type.name, target_model
        )
        
        # Execute with optimized configuration
        return self._send_agent_message(agent, full_prompt, exec_config["timeout"])
```

This integration provides:
- Dynamic model selection based on task requirements
- Appropriate prompt formatting per agent personality
- Optimized execution parameters
- Consistent error handling and logging