# Architecture

## System Diagram

```
+---------------------------------------------------------------+
|                      Opencode Session                      |
+---------------------------------------------------------------+
|                                                               |
|   +--------------+    +--------------+    +--------------+    |
|   |   Pre-Hook   |--->|  Task Tool   |--->|  Post-Hook   |    |
|   |   (inject)   |    |  (execute)   |    |   (record)   |    |
|   +------+-------+    +--------------+    +-------+------+    |
|          |                                        |           |
|          v                                        v           |
|   +-------------------------------------------------------+   |
|   |                    SQLite Database                    |   |
|   |  +----------+ +----------+ +---------+ +----------+   |   |
|   |  |Heuristics| |Learnings | | Metrics | |  Trails  |   |   |
|   |  +----------+ +----------+ +---------+ +----------+   |   |
|   +-------------------------------------------------------+   |
|          ^                                        ^           |
|          |                                        |           |
|   +------+-------+                        +-------+------+    |
|   | Query System |                        |  Dashboard   |    |
|   |  (query.py)  |                        | (React+API)  |    |
|   +--------------+                        +--------------+    |
+---------------------------------------------------------------+
```

## Database Layer

The framework uses **Peewee ORM** for all database operations, providing:
- Type-safe queries with Python expressions
- Automatic table creation and schema management
- Connection pooling handled by the ORM
- Cross-platform SQLite compatibility

## Database Tables

| Table | Purpose |
|-------|---------|
| `heuristics` | Learned patterns with confidence |
| `learnings` | Failures and successes |
| `metrics` | Usage statistics |
| `trails` | Pheromone signals for swarm |
| `workflow_runs` | Swarm execution instances |
| `node_executions` | Individual agent work |
| `assumptions` | Hypotheses to verify or challenge |
| `invariants` | Statements that must always be true |
| `spike_reports` | Research investigation knowledge |
| `decisions` | Architecture decision records |

## File Locations

| Path | Purpose |
|------|---------|
| `~/.opencode/AGENTS.md` | Agent instructions |
| `~/.opencode/settings.json` | Hook configurations |
| `~/.opencode/emergent-learning/memory/index.db` | SQLite database |
| `~/.opencode/emergent-learning/src/query/query.py` | Query system |
| `~/.opencode/emergent-learning/hooks/learning-loop/` | Hook scripts |
| `~/.opencode/emergent-learning/dashboard-app/` | React dashboard |
| `~/.opencode/emergent-learning/conductor/` | Swarm orchestration |
| `~/.opencode/emergent-learning/agents/` | Agent personalities |

## Hooks System

**PreToolUse (Task):**
1. Hook triggered before Task tool executes
2. Queries database for relevant heuristics
3. Injects heuristics into agent context

**PostToolUse (Task):**
1. Hook triggered after Task completes
2. Analyzes output for success/failure
3. Updates heuristic confidence
4. Lays trails for files touched
5. Auto-records failures
