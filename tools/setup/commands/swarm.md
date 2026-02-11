# /swarm - Coordinated Multi-Agent Execution

Spawn and manage coordinated agents using the blackboard pattern.

## Usage

```
/swarm [task]    # Execute task with monitoring
/swarm show      # View full state
/swarm reset     # Clear blackboard
/swarm stop      # Stop monitoring
```

## Examples

```
/swarm investigate the authentication system
/swarm implement feature X
/swarm show
/swarm reset
```

---

## How Monitoring Works

**Single-Pass Sentinel Model:**
1. You spawn work agents with `[SWARM]` tag
2. Hook reminds main Claude if sentinel needed
3. Main Claude spawns nvidia/qwen/qwen3-next-80b-a3b-instruct sentinel (single pass)
4. Sentinel analyzes state, fixes problems, logs, exits
5. Next user message triggers next monitoring cycle

Sentinels do NOT self-perpetuate (cost control). The cycle is driven by user interaction.

---

## Instructions

### `/swarm <task>` (Execute)

**With task:** Start fresh coordinated execution

1. **Initialize** (if needed):
   ```bash
   mkdir -p ~/.opencode/emergent-learning/.coordination
   python ~/.opencode/emergent-learning/sentinel/sentinel_loop.py clear
   ```

2. **Analyze & decompose** the task into parallel subtasks

3. **Show plan**:
   ```
   ## Swarm Plan

   **Task:** [task]
   **Agents:** [count]

   | # | Subtask | Scope |
   |---|---------|-------|
   | 1 | ... | src/... |
   | 2 | ... | tests/... |

   Proceed? [Y/n]
   ```

4. **Spawn work agents** using Task tool with `[SWARM]` marker:

   **IMPORTANT:**
   - Always include `[SWARM]` in description (triggers hooks)
   - Always use `run_in_background: true` (Golden Rule #12)

   ```
   Task tool call:
   - description: "[SWARM] Investigate auth service"
   - prompt: "Your task: ..."
   - subagent_type: "general-purpose"
   - run_in_background: true
   ```

5. **Spawn sentinel** (optional but recommended):
   ```bash
   python ~/.opencode/emergent-learning/sentinel/sentinel_loop.py prompt
   ```

   Then spawn with Task tool:
   ```
   - description: "[SENTINEL] Monitor swarm"
   - subagent_type: "general-purpose"
   - model: "nvidia/qwen/qwen3-next-80b-a3b-instruct"
   - run_in_background: true
   - prompt: (output from above command)
   ```

   The sentinel will:
   - Do ONE comprehensive monitoring pass
   - Detect problems (stale agents, errors)
   - Fix issues directly (update blackboard)
   - Log findings and exit

   A UserPromptSubmit hook will remind you to spawn another sentinel if needed.

6. **Iterate** on follow-up tasks from queue (max 5 iterations)

7. **Synthesize** all findings into summary

8. **Stop monitoring** when done:
   ```bash
   python ~/.opencode/emergent-learning/sentinel/sentinel_loop.py stop
   ```

### `/swarm show` (View State)

```bash
python ~/.opencode/emergent-learning/sentinel/sentinel_loop.py status
```

Also check blackboard:
```bash
cat ~/.opencode/emergent-learning/.coordination/blackboard.json | python -m json.tool
```

### `/swarm reset` (Clear)

Clear all state:
```bash
rm -rf ~/.opencode/emergent-learning/.coordination/*
```

### `/swarm stop` (Disable)

Stop monitoring:
```bash
python ~/.opencode/emergent-learning/sentinel/sentinel_loop.py stop
```

This creates a `sentinel-stop` file that prevents future sentinel spawns.

---

## Finding Types

Agents report in `## FINDINGS` section:
- `[fact]` - Confirmed information
- `[hypothesis]` - Suspected pattern
- `[blocker]` - Cannot proceed
- `[question]` - Need input

## Constraints

- File-based IPC (no external services)
- Windows compatible
- Single-pass sentinels (user-driven cycle)
- Max 5 iterations per swarm
