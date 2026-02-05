# OpenELF Agent Formats

OpenELF supports two agent format standards: the traditional ELF format and OpenCode's native agent format. This dual support provides maximum flexibility for different use cases.

## OpenCode Agent Format (Recommended)

OpenCode agents use YAML frontmatter with markdown content, stored in `/home/bamer/.config/opencode/agents/`.

### Structure

```markdown
---
name: researcher
description: Deep investigation specialist
model: opencode/nemotron-v3-coder
temperature: 0.6
skills:
  - "code-analysis"
  - "pattern-recognition"
plugins:
  - "git-history-analyzer"
tools:
  - "glob"
  - "grep"
  - "read"
permissions:
  bash:
    "rm -rf *": "ask"
    "sudo *": "deny"
---

# Researcher Agent - Investigation Specialist

Detailed agent instructions in markdown format...
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier |
| `description` | string | Brief description of agent purpose |
| `model` | string | Default model for agent execution |
| `temperature` | float | Model temperature setting (0.0-1.0) |
| `skills` | array | List of agent skills |
| `plugins` | object | Plugin configurations |
| `tools` | array | Available tools |
| `permissions` | object | Security permissions |

### Example: OpenCode Researcher Agent

```markdown
---
name: researcher
description: Deep investigation specialist - explores codebases, APIs, and documentation to uncover root causes and gather evidence
mode: primary
temperature: 0.6
model: llama/nemotron-v3-coder
permissions:
  bash:
    "rm -rf *": "ask"
    "rm -rf /*": "deny"
    "sudo *": "deny"
  edit:
    "**/*.env*": "deny"
    "**/*.key": "deny"
---

# Researcher Agent - Investigation Specialist

You are the **Researcher Agent** for the Emergent Learning Framework (ELF).

## Mission
Conduct thorough investigations to uncover facts, patterns, and root causes. Never assume - always verify with evidence from the codebase.

[... rest of agent instructions ...]
```

## ELF Agent Format (Legacy/Custom)

ELF agents use a more structured YAML format with explicit configuration sections.

### Structure

```yaml
# Role and Identity
Role: Researcher Agent
Thinking Style: Thorough and methodical

# Behavior Configuration
Behaviors:
  search_memory_first: true
  cite_sources: true
  flag_uncertainty: true

# Communication Style
Communication Style:
  verbosity: detailed
  formality: professional
  pattern: report-driven

# Model Configuration
Model Configuration:
  default_model: opencode/trinity-large-preview-free
  alternative_models:
    fast: opencode/kimi-k2.5-free
    capable: opencode/nemotron-v3-coder
  model_selection_criteria:
    complexity_threshold: high
    speed_threshold: medium

# Execution Settings
Execution:
  default_timeout: 600
  max_tokens: null
  temperature: null
```

### Example: ELF Researcher Personality

```yaml
Role: Researcher Agent
Thinking Style: Thorough and methodical
Behaviors:
  search_memory_first: "Always search memory first: 'Have we seen this before?'"
  cite_sources: "Cites sources for claims"
  flag_uncertainty: "Flags uncertainty explicitly"
Triggers:
  new_problem_domains: "New problem domains"
  unknown_error_messages: "Unknown error messages"
  exploring_solution_spaces: "Exploring solution spaces"
Communication Style:
  verbosity: detailed
  formality: professional
  pattern: report-driven
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
```

## Format Comparison

| Feature | OpenCode Format | ELF Format |
|---------|----------------|------------|
| Location | `/home/bamer/.config/opencode/agents/` | `/home/bamer/.opencode/emergent-learning/agents/[name]/personality.md` |
| File Extension | `.md` | `.md` |
| Metadata | YAML frontmatter | Full YAML document |
| Content | Markdown instructions | Markdown instructions |
| Simplicity | High | Medium |
| Flexibility | Medium | High |
| Standardization | OpenCode Standard | ELF Custom |
| Precedence | Configurable | Configurable |

## Precedence Handling

When both formats exist for the same agent name, precedence is determined by configuration:

### Default Behavior (ELF Precedence)
1. `/home/bamer/.opencode/emergent-learning/agents/[name]/personality.md`
2. `/home/bamer/.opencode/emergent-learning/agents/[name].md`
3. `/home/bamer/.config/opencode/agents/[name].md`

### OpenCode Precedence
1. `/home/bamer/.config/opencode/agents/[name].md`
2. `/home/bamer/.opencode/emergent-learning/agents/[name]/personality.md`
3. `/home/bamer/.opencode/emergent-learning/agents/[name].md`

Configure precedence in the orchestrator:

```python
# In orchestrator.py
self.personality_manager = PersonalityManager(
    opencode_precedence=True  # Set to True to prioritize OpenCode agents
)
```

## Best Practices

### Choosing a Format

**Use OpenCode Format When:**
- Creating new agents
- Wanting standardization
- Leveraging existing OpenCode agent ecosystem
- Prioritizing simplicity

**Use ELF Format When:**
- Needing advanced configuration options
- Customizing existing agents extensively
- Requiring backward compatibility
- Needing fine-grained control

### Migration Strategy

Migrating from ELF to OpenCode format:

1. **Backup existing personalities**
2. **Convert YAML structure to frontmatter**
3. **Move content to markdown body**
4. **Test with precedence configuration**
5. **Gradually migrate agents**

Example conversion:

**ELF Format:**
```yaml
Role: Researcher Agent
Model Configuration:
  default_model: opencode/trinity-large-preview-free
  temperature: 0.6
```

**OpenCode Format:**
```markdown
---
name: researcher
model: opencode/trinity-large-preview-free
temperature: 0.6
---

# Researcher Agent

[Instructions here]
```