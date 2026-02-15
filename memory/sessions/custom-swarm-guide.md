# Launching Custom Swarms with Any Number of Agents

## Quick Answer

To launch a swarm with **6 (or any number of) agents**, use the `--agents` flag (or `-a`):

```bash
/swarm "Implement a new functionality" -a "agent1,agent2,agent3,agent4,agent5,agent6"
```

### Example: Implement New Authentication Feature

```bash
/swarm "Implement JWT authentication system" \
  -a "architect,researcher,skeptic,creative,coder-agent,janitor-agent" \
  --context "We use Node.js, Express, PostgreSQL"
```

---

## Available Agents (13 Total)

### Core Agents

| Agent | Description | Best For |
|-------|-------------|----------|
| **architect** | System design architect | Designing architecture |
| **researcher** | Deep investigation specialist | Researching solutions |
| **skeptic** | Critical analyst and risk identifier | Reviewing for issues |
| **creative** | Innovation specialist | Brainstorming alternatives |
| **learning-extractor** | Synthesizes learnings | Extracting insights |

### System Agents

| Agent | Description | Use Case |
|-------|-------------|----------|
| **ceo** | CEO/CTO decision maker | Strategic decisions |
| **sentinel** | System monitoring | Health checks |
| **unified-orchestrator** | Central system brain | Complex orchestration |
| **multi-agent-coordinator** | Workflow coordination | Multi-agent tasks |

### Work Agents

| Agent | Description | Use Case |
|-------|-------------|----------|
| **coder-agent** | Executes coding subtasks | Writing code |
| **janitor-agent** | Cleanup and tech debt | Refactoring |
| **multi-agent-orchestrator-bf** | Distributed task coordinator | Parallel workflows |

---

## Predefined Modes

If you don't want to specify custom agents, use predefined modes:

| Mode | Agents | Use Case |
|------|--------|----------|
| `--mode analysis` | researcher → architect | Research & structure |
| `--mode design` | architect → creative → skeptic | Design & critique |
| `--mode implementation` | architect → researcher → skeptic | Build & validate |
| `--mode learning` | learning-extractor → researcher → architect | Extract insights |
| `--mode all` (default) | researcher → architect → skeptic → creative → learning-extractor | Full comprehensive |

---

## Custom Swarm Examples

### 1. Quick Implementation (3 Agents)

```bash
/swarm "Fix the login bug" \
  -a "researcher,skeptic,coder-agent"
```

**Why these agents:**
- **researcher**: Investigate the bug
- **skeptic**: Find edge cases
- **coder-agent**: Write the fix

### 2. Design Review (4 Agents)

```bash
/swarm "Review the database schema design" \
  -a "architect,researcher,skeptic,sentinel"
```

**Why these agents:**
- **architect**: Evaluate architecture
- **researcher**: Check best practices
- **skeptic**: Identify risks
- **sentinel**: Monitor for issues

### 3. Implement New Feature (5 Agents)

```bash
/swarm "Implement real-time notifications" \
  -a "architect,researcher,creative,coder-agent,janitor-agent" \
  --context "WebSocket-based, Redis pub/sub, Node.js backend"
```

**Why these agents:**
- **architect**: Design the system
- **researcher**: Research websockets/Redis
- **creative**: Innovate on UX
- **coder-agent**: Write implementation
- **janitor-agent**: Clean up code

### 4. Full Development Cycle (6 Agents) ⭐

```bash
/swarm "Implement user authentication feature" \
  -a "architect,researcher,skeptic,creative,coder-agent,janitor-agent" \
  --context "JWT-based, refresh tokens, role-based access"
```

**Agent sequence:**
1. **architect** → Design authentication flow
2. **researcher** → Research JWT best practices
3. **creative** → Improve UX (login experience)
4. **skeptic** → Find security risks
5. **coder-agent** → Implement the feature
6. **janitor-agent** → Refactor and document

### 5. Strategic Architecture (7 Agents)

```bash
/swarm "Design microservices architecture" \
  -a "architect,researcher,skeptic,creative,sentinel,ceo,multi-agent-coordinator"
```

**Why these agents:**
- **architect**: Design the architecture
- **researcher**: Research patterns
- **skeptic**: Identify risks
- **creative**: Innovate on design
- **sentinel**: Monitor considerations
- **ceo**: Strategic decisions
- **multi-agent-coordinator**: Coordinate services

### 6. Codebase Deep Dive (8 Agents)

```bash
/swarm "Analyze and improve codebase quality" \
  -a "architect,researcher,skeptic,sentinel,learning-extractor,coder-agent,janitor-agent,multi-agent-orchestrator-bf"
```

**Agent roles:**
- **architect**: Review architecture
- **researcher**: Find patterns
- **skeptic**: Find bugs
- **sentinel**: Check health
- **learning-extractor**: Document insights
- **coder-agent**: Fix critical issues
- **janitor-agent**: Clean up tech debt
- **multi-agent-orchestrator-bf**: Coordinate parallel fixes

---

## Choosing the Right Agents

### By Task Type

| Task | Recommend Agents |
|------|-----------------|
| **Design** | architect, researcher, creative, skeptic |
| **Research** | researcher, architect, learning-extractor |
| **Implementation** | architect, researcher, coder-agent, skeptic |
| **Refactoring** | architect, janitor-agent, skeptic, learning-extractor |
| **Debugging** | researcher, skeptic, coder-agent, debugger (if exists) |
| **Strategy** | ceo, architect, multi-agent-coordinator, researcher |
| **Review** | skeptic, architect, researcher, learning-extractor |

### By Outcome

| Outcome | Agent Sequence |
|---------|----------------|
| **Fast Fix** | researcher → coder-agent |
| **Thorough** | architect → researcher → skeptic → coder-agent |
| **Innovative** → creative → coder-agent → skeptic |
| **Comprehensive** | architect → researcher → creative → skeptic → coder-agent → janitor-agent |
| **Production-Ready** | architect → researcher → skeptic → coder-agent → janitor-agent → sentinel |

---

## Syntax Details

### Basic Syntax

```bash
python3 swarm-cli.py run "TASK" -a "agent1,agent2,agent3,..."
```

### With Context

```bash
python3 swarm-cli.py run "TASK" \
  -a "agent1,agent2,agent3" \
  -c "Your context here"
```

### Via /swarm Command

```bash
/swarm "TASK" -a "agent1,agent2,agent3" -c "context"
```

### Full Example

```bash
/swarm "Implement payment processing with Stripe" \
  -a "architect,researcher,skeptic,creative,coder-agent,janitor-agent" \
  -c "Node.js backend, PostgreSQL, Stripe API v3, PCI compliance required"
```

---

## Checking Swarm Status

### Check Most Recent Swarm

```bash
python3 swarm-cli.py status
```

### Check Specific Swarm

```bash
python3 swarm-cli.py status --file path/to/swarm_result_*.json
```

### Output Example

```
📊 Swarm Status
============================================================
Task: Implement a new user authentication feature with JWT
Mode: custom
Started: 2026-02-14T02-14-00

Agent Status:
  ✅ architect      - spawned
      Session: ses_3a79f994...
  ✅ researcher     - spawned
      Session: ses_3a7a4a0e...
  ✅ skeptic        - spawned
      Session: ses_3a797405...
  ✅ creative       - spawned
      Session: ses_3a7973f9...
  ✅ coder-agent    - spawned
      Session: ses_3a79359d...
  ✅ janitor-agent  - spawned
      Session: ses_3a793591...
```

---

## Agent Descriptions

### For "Implementing New Functionality"

Here's what each agent will do for your implementation task:

```
architect        → Designs the overall structure and architecture
researcher       → Researches best practices, libraries, patterns
skeptic          → Finds edge cases, security risks, potential issues
creative         → Proposes innovative approaches and UX improvements
coder-agent      → Writes the actual implementation code
janitor-agent    → Refactors, cleans up, and documents the code
```

### For Implementing "New User Authentication with JWT"

**1. architect**
- Designs authentication flow diagrams
- Specifies where JWTs are stored
- Defines refresh token strategy
- Maps out role-based access control

**2. researcher**
- Researches JWT libraries (jsonwebtoken, jwks-rsa)
- Finds security best practices (token rotation, signing algorithms)
- Investigates session management patterns
- Looks up regulatory requirements (GDPR, PCI)

**3. skeptic**
- Identifies security vulnerabilities (XSS, CSRF, CSRF tokens needed?)
- Finds edge cases (expired tokens, concurrent logins)
- Tests failure scenarios (network errors, database down)
- Challenges assumptions (is JWT really the best choice here?)

**4. creative**
- Improves login UX (remember me, social login, magic links)
- Innovates on token handling (short-lived access tokens, long-lived refresh)
- Proposes alternative approaches if appropriate
- Designs user-facing auth flows

**5. coder-agent**
- Implements authentication middleware
- Writes token generation and validation
- Creates login/logout endpoints
- Adds refresh token rotation

**6. janitor-agent**
- Refactors code to be DRY and modular
- Adds comprehensive error handling
- Writes unit tests for auth functions
- Adds comments and documentation

---

## Pro Tips

### 1. Order Matters

Agent sequence affects the workflow:
- **architect first**: Start with design
- **researcher early**: Research before coding
- **skeptic middle**: Review before implementation
- **creative early**: Innovation before constraints
- **coder-agent mid**: Implement after design
- **janitor-agent last**: Clean up when done

### 2. Add Context

Always provide context for better results:
```bash
/swarm "Task" -a "agents" -c "Tech stack, requirements, constraints"
```

### 3. Test Small First

Start with 2-3 agents, then expand:
```bash
# First iteration
/swarm "Design feature" -a "architect,researcher"

# Second iteration (after review)
/swarm "Implement feature" -a "architect,researcher,skeptic,coder-agent"

# Third iteration (comprehensive)
/swarm "Ship feature" -a "architect,researcher,skeptic,coder-agent,janitor-agent,sentinel"
```

### 4. Combine Modes and Custom

You can use modes as templates:
```bash
# Use design mode as base, add more agents
/swarm "Design complex system" \
  -a "$(python3 swarm-cli.py agents --mode design | awk '{print $2}' | tr '\n' ','),ceo,multi-agent-coordinator"
```

### 5. Reuse Previous Agents

Check status to see what agents were used:
```bash
python3 swarm-cli.py status --file path/to/previous/result.json
```

---

## Common Mistakes

### ❌ wrong
```bash
/swarm "Task" -a "architect, developer, tester"  # agent names don't exist
```

### ✅ right
```bash
# Check available agents first
python3 swarm-cli.py list

# Use correct agent names
/swarm "Task" -a "architect,researcher,coder-agent"
```

### ❌ wrong
```bash
/swarm "Task" -a "architect, researcher, skeptic"  # spaces after commas
```

### ✅ right
```bash
/swarm "Task" -a "architect,researcher,skeptic"  # no spaces
```

---

## Summary

To launch a custom swarm with 6 agents:

1. **List available agents:** `python3 swarm-cli.py list`
2. **Choose 6 agents for your task**
3. **Run swarm:**
   ```bash
   /swarm "Implement new functionality" \
     -a "agent1,agent2,agent3,agent4,agent5,agent6" \
     -c "Your context"
   ```
4. **Check status:** `python3 swarm-cli.py status`

That's it! 🚀
