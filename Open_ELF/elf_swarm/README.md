# ELF SWARM - Proper Multi-Agent Workflow

A phased, plan-driven multi-agent workflow implementation for the Emergent Learning Framework (ELF).

## Overview

ELF SWARM implements the correct swarm workflow pattern with sequential phases and quality gates:

```
USER: "Add feature X"
│
├─ PHASE 0: Check for .swarm/plan.md
├─ PHASE 1: Clarify (ask user questions)
├─ PHASE 2: Discover (scan codebase)
├─ PHASE 3: Consult SMEs (domain experts)
├─ PHASE 4: Plan (create .swarm/plan.md)
├─ PHASE 4.5: Critic Gate (skeptic reviews)
├─ PHASE 5: Execute (coder → reviewer → test loop)
└─ PHASE 6: Complete (archive results)
```

## Usage

### Basic Usage

```python
from emergent_learning.Open_ELF.elf_swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator(task="Implement user authentication")
orchestrator.run()
```

### From Command Line

```bash
cd /home/bamer/.opencode
python -c "from emergent_learning.Open_ELF.elf_swarm import SwarmOrchestrator; SwarmOrchestrator('Add feature X').run()"
```

## Architecture

```
Open_ELF/elf_swarm/
├── __init__.py              # Package exports
├── orchestrator.py          # Main workflow orchestrator
├── swarm_manager.py         # State and plan management
├── phases/
│   ├── __init__.py
│   ├── phase0_check.py    # Check for existing plan
│   ├── phase1_clarify.py  # Ask clarifying questions
│   ├── phase2_discover.py # Scan codebase
│   ├── phase3_sme.py      # Consult domain experts
│   ├── phase4_plan.py     # Create implementation plan
│   ├── phase45_critic.py  # Critic gate
│   ├── phase5_execute.py  # Execute tasks
│   └── phase6_complete.py # Archive completion
└── templates/
    ├── plan_template.md
    └── context_template.md
```

## Phases

### Phase 0: Check Plan
Checks if `.swarm/plan.md` exists. If yes, resumes.

### Phase 1: Clarify
Uses `architect` agent to identify missing information and ask clarifying questions.

### Phase 2: Discover
Uses `researcher` agent to scan codebase:
- Project structure
- Languages/frameworks
- Existing patterns
- Relevant files

### Phase 3: Consult SMEs
Uses domain-specific research (SMEs) to get expert guidance:
- Security consultants
- API specialists
- Database experts
- etc.

### Phase 4: Create Plan
Uses `architect` agent to create detailed implementation plan:
- Phases (logical groupings)
- Tasks with acceptance criteria
- Dependencies

### Phase 4.5: Critic Gate
Uses `skeptic` agent to review plan:
- Feasibility check
- Completeness check
- Risk analysis

Returns: `APPROVED`, `NEEDS_REVISION`, or `REJECTED`

### Phase 5: Execute
For each task in plan:
- **coder** implements
- **reviewer** checks (if REJECT → retry)
- **test** validates (if FAIL → fix → retest)
- Mark task complete: `[x] Task name`

### Phase 6: Complete
- Re-scan codebase
- Extract learnings
- Update context
- Archive to `.swarm/history/swarm_YYYYMMDD_HHMMSS.md`

## Swarm State

### Directory Structure

```
.swarm/
├── plan.json          # JSON plan state (internal)
├── plan.md            # Human-readable plan
├── context.json       # JSON context state (internal)
├── context.md         # Human-readable context
└── history/
    └── swarm_*.md     # Archived runs
```

### Plan Format

```markdown
# Swarm Implementation Plan

## Phase 1: Foundation

### Task 1.1: Set up project structure
- Description: Create directories and initialize
- Acceptance Criteria:
  - [ ] src/ directory created
  - [ ] tests/ directory created
- Dependencies: none
- Status: pending
```

### Context Format

```markdown
# Swarm Context

Created: 2025-02-14T14:30:00

## Task
Implement user authentication

## Discovery
{codebase exploration results}

## SME Consultation

### Security
{auth best practices}

### API
{JWT patterns}

## Learnings
{key takeaways}
```

## Agent Mapping

See availble agents at:
- ELF personas: `/home/bamer/.opencode/agents/OPC_ELF_System_Agents/`
- Plugin agents: `/home/bamer/.opencode/agents/plugins/`

### Core Agents
- **architect**: Design and plan
- **researcher**: Discover and research
- **skeptic**: Quality gates
- **learning-extractor**: Learnings extraction

### Execution Agents
- **coder**: Implementation (python-pro, typescript-pro, etc.)
- **reviewer**: Code review (code-reviewer, architect-review)
- **test**: Testing (test-automator, etc.)

### Domain SMEs
- **security**: security-auditor, backend-security-coder
- **api**: graphql-architect, backend-architect
- **database**: database-architect, sql-pro
- etc.

## Integration with ELF

This is part of the Emergent Learning Framework:

- Uses `agent_manager` from ELF agents
- Saves learnings to ELF building
- Follows ELF golden rules
- Logs to ELF logging system

## Status

**Implemented:** Phases 0-4.5 (clarify → discover → SMEs → plan → critic gate)

**Planned:** Phase 5 (coder→reviewer→test loop) and Phase 6 (complete)

## Development Notes

To complete Phase 5:
1. Parse markdown plan to extract phases and tasks
2. Implement task executor with coder→reviewer→test loop
3. Update plan.md with task completion checkboxes
4. Implement retry logic (max 3 attempts per task)

To extend:
1. Add domain SMEs to `phase3_sme.py`
2. Add custom task parsers for specific project types
3. Add quality metrics to phase45 critic gate
4. Add automated summary generation in phase6
