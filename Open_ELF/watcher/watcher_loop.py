#!/usr/bin/env python3
"""
Tiered Watcher System

Generates prompts for tier 1 (fast) and tier 2 (deep) watchers.
Based on original ELF design: continuous monitoring with intelligent escalation.

Usage:
    python watcher_loop.py prompt                              # Output tier 1 prompt (Haiku/fast)
    python watcher_loop.py handler-prompt --escalation <json>  # Output tier 2 prompt (Opus/deep)
    python watcher_loop.py stop                                # Create stop signal file
    python watcher_loop.py status                              # Check watcher status
    python watcher_loop.py clear                               # Clear stop signal
    python watcher_loop.py summary                             # Show last watcher actions
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
ELF_DIR = SCRIPT_DIR.parent.parent  # Go up 2 levels to emergent-learning root
if str(ELF_DIR) not in sys.path:
    sys.path.insert(0, str(ELF_DIR))

from elf_paths import get_base_path

# Paths
COORDINATION_DIR = get_base_path() / ".coordination"
BLACKBOARD_FILE = COORDINATION_DIR / "blackboard.json"
WATCHER_LOG = COORDINATION_DIR / "watcher-log.md"
STOP_FILE = COORDINATION_DIR / "watcher-stop"
DECISION_FILE = COORDINATION_DIR / "decision.md"


def gather_state() -> Dict[str, Any]:
    """Gather current coordination state."""
    state = {
        "timestamp": datetime.now().isoformat(),
        "blackboard": {},
        "agent_files": [],
        "stop_requested": STOP_FILE.exists(),
    }

    if BLACKBOARD_FILE.exists():
        try:
            state["blackboard"] = json.loads(BLACKBOARD_FILE.read_text())
        except (json.JSONDecodeError, IOError, OSError) as e:
            state["blackboard"] = {"error": f"Could not parse blackboard.json: {e}"}

    for f in COORDINATION_DIR.glob("agent_*.md"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        age_seconds = (datetime.now() - mtime).total_seconds()
        state["agent_files"].append(
            {
                "name": f.name,
                "age_seconds": round(age_seconds),
                "size_bytes": f.stat().st_size,
            }
        )

    return state


def output_tier1_prompt():
    """Output tier 1 watcher prompt (fast, frequent checks)."""
    state = gather_state()

    prompt = f"""You are TIER 1 watcher agent for a multi-agent swarm.

## Your Job

Perform fast, frequent monitoring checks of the swarm (every 30 seconds):
1. Analyze coordination state
2. Detect basic problems (stale agents, errors, stuck tasks)
3. Take basic corrective actions (restart stale agents, log errors)
4. Log your findings
5. Exit with exit code (0=nominal, 1=escalation needed, 2=error)

You are the FIRST line of defense - handle common issues yourself, only escalate complex problems.

## Current Coordination State

```json
{json.dumps(state, indent=2)}
```

## Step 1: Analyze State

Check for these problems:
- **Stale agents**: No heartbeat update > 120 seconds (check last_seen timestamps)
- **Errors**: Any "error" fields in blackboard
- **Stuck tasks**: Agent marked "active" but no progress
- **No active agents**: This is NORMAL - status = `nominal` (NOT `complete`!)

## Step 2: Determine Status

Based on analysis, your status is one of:

| Status | Meaning | Exit Code |
|--------|---------|-----------|
| `nominal` | Everything healthy (no agents is normal) | 0 |
| `stale` | Agent(s) not updating, you fixed it | 1 |
| `error` | Complex error needs tier 2 help | 1 |
| `stopped` | Stop file exists, end monitoring | 0 |

**IMPORTANT**:
- "No active agents" = `nominal`, NOT `complete`
- Exit code 0 = "check me again in 30 seconds"
- Exit code 1 = "escalate to tier 2 for complex issue"

## Step 3: Take Action (if needed)

**For `stale` agents - restart them:**

```python
import json
from pathlib import Path

bb_path = Path("{get_base_path()}") / ".coordination" / "blackboard.json"
bb = json.loads(bb_path.read_text())

# Mark agent for restart
bb["agents"]["<agent_id>"]["status"] = "restarting"
bb["agents"]["<agent_id>"]["last_seen"] = "{datetime.now().isoformat()}"

bb_path.write_text(json.dumps(bb, indent=2))
```

**For `error` states - log the error and escalate (exit code 1)**
- Log to watcher-log.md
- Include error details in summary

**For `nominal` or `stopped` - just log status**

## Step 4: Log Your Findings

Append to watcher-log.md:
```bash
echo "<timestamp> | STATUS: <status> | NOTES: <brief observation>" >> {get_base_path()}/.coordination/watcher-log.md
```

## Step 5: Output Summary

End with a clear summary block:

```
== WATCHER SUMMARY ==
STATUS: <nominal|stale|error|stopped>
AGENTS_CHECKED: <count>
ISSUES_FOUND: <count or "none">
ACTIONS_TAKEN: <what you did, or "none">
RECOMMENDATION: <what to do next, if anything>
```

## Important Notes

- You have FULL access to Bash, Read, Edit, Write tools
- You CAN and SHOULD fix basic problems directly
- You do NOT have Task tool (cannot spawn agents) - that's fine
- Be concise - this runs frequently (every 30 seconds)
- NEVER create a stop file - stop files are user-initiated only
- When no agents are active, that's NORMAL - status = `nominal`
- You will be called again periodically for continuous monitoring
"""

    print(prompt)


def output_tier2_prompt(escalation_json: str):
    """Output tier 2 handler prompt (deep analysis for complex issues)."""
    state = gather_state()

    prompt = f"""You are TIER 2 handler agent for complex watcher issues.

## Your Job

Analyze escalated issues from tier 1 watcher and provide solutions:
1. Review the problem described in the escalation
2. Analyze coordination state deeply
3. Make intelligent decisions about intervention
4. Take appropriate action (you CAN update files directly)
5. Log your findings

You are called ONLY when tier 1 watcher needs help with complex issues.

## Escalation from Tier 1

```json
{escalation_json}
```

## Current Coordination State

```json
{json.dumps(state, indent=2)}
```

## Analysis Framework

Consider:
- **Root cause**: What's actually wrong?
- **Impact**: How does this affect the swarm?
- **Immediate action**: What must be done NOW?
- **Prevention**: How to prevent this in the future?

## Step 1: Analyze the Problem

Break down the escalation:
- What specific issue occurred?
- What did tier 1 try to do?
- Why did it need escalation?

## Step 2: Determine Resolution Strategy

Your options:
- **Fix directly**: Update coordination files, restart services
- **Recommend action**: Suggest human intervention
- **Document**: Record the issue for future reference

## Step 3: Execute Resolution

**If fixing directly - you can:**

```python
# Update blackboard
import json
from pathlib import Path

bb_path = Path("{get_base_path()}") / ".coordination" / "blackboard.json"
bb = json.loads(bb_path.read_text())
# Make changes...
bb_path.write_text(json.dumps(bb, indent=2))

# Update decision file
decision_path = Path("{get_base_path()}") / ".coordination" / "decision.md"
decision_path.write_text("# Decision\\n\\n<your decision>")
```

## Step 4: Log Your Findings

Append to watcher-log.md:
```bash
echo "<timestamp> | [TIER 2] STATUS: <status> | ACTION: <what you did>" >> {get_base_path()}/.coordination/watcher-log.md
```

## Step 5: Output Summary

```
== HANDLER SUMMARY ==
STATUS: <resolved|deferred|escalated>
ISSUE_TYPE: <what kind of problem>
ACTION_TAKEN: <what you did>
RECOMMENDATION: <next steps>
```

## Important Notes

- You have FULL access to Bash, Read, Edit, Write tools
- Take time to think through complex issues
- Document your reasoning
- Consider system-wide impacts
- Never create a stop file (that's user-initiated only)
"""

    print(prompt)


def create_stop_file():
    """Create stop signal file."""
    STOP_FILE.write_text(f"Watch stopped\nCreated: {datetime.now().isoformat()}\n")
    print(f"Stop file created: {STOP_FILE}")


def clear_stop_file():
    """Clear stop signal file."""
    if STOP_FILE.exists():
        STOP_FILE.unlink()
        print(f"Stop file cleared: {STOP_FILE}")
    else:
        print("No stop file to clear")


def check_status():
    """Check and display watcher status."""
    state = gather_state()

    print("\n=== Watcher Status ===")
    print(f"Timestamp: {state['timestamp']}")
    print(f"Stop requested: {state['stop_requested']}")
    print(f"Active agents: {len(state['blackboard'].get('agents', {}))}")
    print(f"\nAgent files: {len(state['agent_files'])}")

    if WATCHER_LOG.exists():
        print(f"\nLast log entries:")
        for line in WATCHER_LOG.read_text().split("\n")[-5:]:
            if line.strip():
                print(f"  {line}")


def show_summary():
    """Show summary of recent watcher activity."""
    if not WATCHER_LOG.exists():
        print("No watcher log found")
        return

    log_content = WATCHER_LOG.read_text()
    entries = [line for line in log_content.split("\n") if line.strip()]

    print(f"\n=== Watcher Summary ({len(entries)} entries) ===")
    if entries:
        print(f"Latest: {entries[-1]}")
        if len(entries) > 1:
            print(f"Previous: {entries[-2]}")
    else:
        print("No log entries")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python watcher_loop.py <command>")
        print("Commands:")
        print("  prompt              Output tier 1 watcher prompt")
        print("  handler-prompt      Output tier 2 handler prompt")
        print("  stop                Create stop signal file")
        print("  clear               Clear stop signal file")
        print("  status              Check watcher status")
        print("  summary             Show recent watcher activity")
        sys.exit(1)

    command = sys.argv[1]

    if command == "prompt":
        output_tier1_prompt()
    elif command == "handler-prompt":
        if "--escalation" in sys.argv:
            idx = sys.argv.index("--escalation")
            if idx + 1 < len(sys.argv):
                escalation_json = sys.argv[idx + 1]
                output_tier2_prompt(escalation_json)
            else:
                print("Error: --escalation requires JSON argument")
                sys.exit(1)
        else:
            print("Error: handler-prompt requires --escalation <json>")
            sys.exit(1)
    elif command == "stop":
        create_stop_file()
    elif command == "clear":
        clear_stop_file()
    elif command == "status":
        check_status()
    elif command == "summary":
        show_summary()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
