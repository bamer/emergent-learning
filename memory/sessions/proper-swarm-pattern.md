# OpenCode Proper Swarm Implementation

The simple `swarm-cli.py` we built earlier spawns all agents at once and walks away. This is **NOT** how proper swarm workflows should work.

## The Correct Pattern

A proper swarm follows a **phased, plan-driven workflow**:

```
USER: "Add user authentication with JWT"
│
├─ PHASE 0: Check for .swarm/plan.md
│          Exists? Resume. New? Continue.
│
├─ PHASE 1: Clarify
│          Ask user questions about requirements
│          "Do you need refresh tokens? What's the session duration?"
│
├─ PHASE 2: Discover
│          @researcher scans codebase → structure, languages, patterns
│
├─ PHASE 3: Consult SMEs
│          @researcher domain: security → auth best practices
│          @researcher domain: api → JWT patterns, refresh flow
│          Guidance saved to .swarm/context.md
│
├─ PHASE 4: Plan
│          Creates .swarm/plan.md with phases, tasks, acceptance criteria
│          Phase 1: Foundation [3 tasks]
│          Phase 2: Core Auth [4 tasks]
│          Phase 3: Session Management [3 tasks]
│
├─ PHASE 4.5: Critic Gate
│             @skeptic reviews plan → APPROVED / NEEDS_REVISION / REJECTED
│             Max 2 revision cycles before escalating to user
│
├─ PHASE 5: Execute (per task)
│   ┌─────────┐    ┌────────────┐    ┌──────────────┐
│   │ @coder  │ →  │ @reviewer  │ →  │    @test     │
│   │ 1 task  │    │ check all  │    │ write + run  │
│   └─────────┘    └────────────┘    └──────────────┘
│        │               │                   │
│        │     If REJECTED: retry    If FAIL: fix + retest
│        └───────────────┘
│   Update plan.md: [x] Task complete (only if PASS)
│   Next task...
│
└─ PHASE 6: Phase Complete
           Re-scan with @explorer
           Update context.md with learnings
           Archive to .swarm/history/
           "Phase 1 complete. Ready for Phase 2?"
```

## Available Agents (From /home/bamer/.opencode/agents)

### Core Roles
- **architect** - Design system architecture and create plans
- **researcher** - Discover codebase, consult SMEs, scan results
- **skeptic** - Critic gate, quality gate, risk analysis
- **learning-extractor** - Extract learnings and update context

### Execution Roles
- **coder** - Implement tasks (various language-specific coders: python-pro, typescript-pro, etc.)
- **reviewer** - Code review (code-reviewer, architect-review)
- **test** - Write and run tests (test-automator, unit tester)

### Coordination Roles
- **multi-agent-coordinator** - Orchestrate across agents
- **unified-orchestrator** - Overall coordination

### Quality Roles
- **sentinel** - Monitor quality and health
- **ceo** - Strategic decisions (escalation point)

## Implementation Files

I've created `swarm_orchestrated.py` which implements:

1. **Phase 0**: Check for `.swarm/plan.md`
2. **Phase 1**: Clarify with user (uses `agent_manager.ask_agent(architect, "what questions...")`)
3. **Phase 2**: Discover codebase (`agent_manager.ask_agent(researcher, "scan codebase...")`)
4. **Phase 3**: Consult SMEs (`agent_manager.ask_agent(researcher, "domain expertise...")`)
5. **Phase 4**: Create plan (`agent_manager.ask_agent(architect, "create plan...")`)
6. **Phase 4.5**: Critic gate (`agent_manager.ask_agent(skeptic, "review plan...")`)
7. **Phase 5**: Execute tasks (loop: coder → reviewer → test)
8. **Phase 6**: Complete phase (scan, update context, archive)

## Usage

```bash
# Run proper orchestrated swarm
python3 swarm_orchestrated.py "Add user authentication with JWT"

# The swarm will:
# 1. Ask clarifying questions interactively
# 2. Scan your codebase
# 3. Consult domain experts
# 4. Create a detailed plan (.swarm/plan.md)
# 5. Get plan approved by critic
# 6. Execute tasks with coder → reviewer → test loop
# 7. Update context and archive results
```

## Key Difference

### Simple Swarm (swarm-cli.py - WRONG)
```bash
/swarm "Task" -a "agent1,agent2,agent3"
# → Spawns all 3 agents at once
# → Returns immediately
# → User manually checks each session
# → No coordination, no plan, no quality gates
```

### Proper Swarm (swarm_orchestrated.py - CORRECT)
```bash
python3 swarm_orchestrated.py "Task"
# → Sequential phases
# → Plan-driven execution
# → Quality gates (critic gate)
# → Coder → Reviewer → Test loop per task
# → Progress tracking in .swarm/plan.md
# → Context accumulation in .swarm/context.md
```

## Swarm Directory Structure

```
.swarm/
├── plan.md              # Phase 4: Detailed implementation plan
├── context.md           # Discovery + SME guidance + learnings
└── history/
    ├── swarm_20250214_143022.md   # Archived runs
    └── swarm_20250214_150815.md
```

## Next Steps

The orchestrated swarm is created but needs:

1. **Interactive clarification**: Handle user questions properly
2. **Task parsing**: Parse plan.md to extract phases and tasks
3. **Full execution loop**: Implement coder → reviewer → test loop with retry
4. **Progress tracking**: Update plan.md with checkboxes as tasks complete
5. **Phase management**: Track which phases are complete

Would you like me to:
- A) Complete the Phase 5 execution loop implementation?
- B) Test the current phases (0-4) with a real task?
- C) Create a simpler version that works with existing tools?
