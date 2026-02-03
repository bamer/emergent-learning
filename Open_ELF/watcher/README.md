# ELF Watcher (OpenCode Adaptation)

## Adaptation from Original ELF Design

This is an adaptation of the original [Tiered Watcher Pattern](https://github.com/Spacehunterz/Emergent-Learning-Framework_ELF/blob/main/src/watcher/README.md) for OpenCode.

### Key Differences from Original

| Original ELF | OpenCode Adaptation |
|-------------|---------------------|
| **Two models**: Haiku (tier 1) + Opus (tier 2) | **One model**: `opencode/big-pickle` (adapts to prompt depth) |
| Model change for different intelligence levels | **Prompt depth change** - same model, different thinking levels |
| Cost optimization (Haiku is cheaper) | Free model - cost not a factor |
| External API (Anthropic) | Local HTTP API (OpenCode) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LAUNCHER.PY                            │
│  Orchestrates tiered monitoring with same model           │
│  - Tier 1: Fast prompt every 30 seconds               │
│  - Tier 2: Deep prompt (escalation only)               │
└──────────────┬────────────────────────────┬─────────────────┘
               │                            │
               ▼                            ▼
    ┌──────────────────┐        ┌──────────────────────┐
    │  TIER 1 PROMPT   │        │   TIER 2 PROMPT     │
    │  Fast, Basic     │        │  Deep Analysis      │
    │  Quick Checks     │        │  Decision Making     │
    │  Exit Code 1     │        │  Escalated from T1  │
    │  (Need Help)     │        │                    │
    └──────────────────┘        └──────────────────────┘
               │                            ▲
               │                            │
               └────────────────────────────┘

           ┌────────────────────────┐
           │   .coordination/       │
           │   - blackboard.json    │
           │   - watcher-log.md    │
           │   - watcher-stop      │
           └────────────────────────┘
```

## Concept

The Tiered Watcher Pattern solves the problem of continuous AI monitoring:

- **Problem**: Running deep analysis constantly is wasteful
- **Solution**: Use fast prompts for frequent checks, deep prompts only when needed
- **Benefit**: Efficient monitoring without unnecessary computation

### Tier 1: Fast Watcher (Every 30 seconds)
- Checks coordination state quickly
- Detects basic issues (stale agents, errors)
- Handles simple problems autonomously
- Exit code 1 when tier 2 help is needed

### Tier 2: Deep Handler (Escalation Only)
- Invoked only when tier 1 requests help
- Deep analysis of complex issues
- Makes intelligent decisions
- Higher computation cost but infrequent

### Launcher
- Runs tier 1 in continuous loop
- Monitors exit codes
- Escalates to tier 2 when needed (exit code = 1)
- Handles graceful shutdown via stop file
- Logs all activity

## Quick Start

### 1. Start Watcher

```bash
# From ELF directory
cd /home/bamer/.opencode/emergent-learning
python Open_ELF/watcher/launcher.py
```

### 2. Stop Watcher

```bash
# Graceful shutdown (create stop file)
touch .coordination/watcher-stop

# Or send SIGINT
Ctrl+C
```

### 3. Monitor Activity

```bash
# Watch logs
tail -f .coordination/watcher-log.md

# View current status
cat .coordination/blackboard.json

# Check launcher status
ps aux | grep "launcher.py"
```

## Configuration

Edit `Open_ELF/watcher/config.py` to customize:

```python
POLL_INTERVAL = 30              # Seconds between tier 1 checks
HEARTBEAT_TIMEOUT = 120         # Seconds before considering agent dead
OPENCODE_SERVER_URL = "http://localhost:4096"
OPENCODE_MODEL = "opencode/big-pickle"  # Single model for both tiers
```

### Environment Variables

```bash
export OPENCODE_SERVER_URL="http://localhost:4096"
export OPENCODE_WATCHER_MODEL="opencode/big-pickle"
```

## Files and Directories

```
Open_ELF/watcher/
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── launcher.py          # Main orchestrator (tiered loop)
├── watcher_loop.py      # Prompt generator (tier 1 + tier 2)
└── README.md            # This file

.coordination/
├── blackboard.json      # Shared state between agents
├── watcher-log.md       # All watcher activity
└── watcher-stop         # Graceful shutdown signal (user-created)
```

## Exit Codes

- **0**: Normal (will check again in 30 seconds)
- **1**: Escalation needed (tier 2 will be invoked)
- **2**: Error occurred (will retry next cycle)

## Prompt Depth Levels

### Tier 1 Prompt Characteristics
- **Goal**: Fast, frequent monitoring
- **Thinking**: Minimal, pattern-based
- **Actions**: Quick fixes, restart stale agents, log errors
- **Response Time**: ~10-20 seconds

### Tier 2 Prompt Characteristics
- **Goal**: Deep analysis for complex issues
- **Thinking**: Thorough, multi-step reasoning
- **Actions**: Intelligent decisions, complex interventions
- **Response Time**: ~30-60 seconds

The same `big-pickle` model adapts its thinking level based on prompt requirements.

## Workflow

### Normal Operation (Most Common)
```
Every 30s:
  Launcher → Tier 1 (fast prompt)
           ↓
           STATUS: nominal
           ↓
           Exit code 0
           ↓
           Wait 30s
           ↓
  Repeat
```

### Escalation Flow (Infrequent)
```
Every 30s:
  Launcher → Tier 1 (fast prompt)
           ↓
           STATUS: stale or error
           ↓
           Exit code 1
           ↓
           Tier 2 (deep prompt)
           ↓
           Deep analysis + action
           ↓
           Exit code 0
           ↓
           Wait 30s
           ↓
  Repeat
```

### Graceful Shutdown
```
User creates: .coordination/watcher-stop
           ↓
Launcher detects stop file
           ↓
Log: "Stop file detected, exiting gracefully"
           ↓
Exit code 0
```

## Troubleshooting

### Watcher Won't Start

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
cd /home/bamer/.opencode/emergent-learning
# Ensure OpenCode server is running
opencode serve --port 4096
```

**Problem**: `Connection refused` to OpenCode

**Solution**:
```bash
# Start OpenCode server
opencode serve --port 4096

# Or check correct port in config.py
```

### Watcher Keeps Restarting

**Check logs**:
```bash
tail -50 .coordination/watcher-log.md
```

**Common causes**:
- OpenCode server not responding
- Configuration files corrupted
- Permissions issues with `.coordination` directory

### Tier 2 Never Invoked

**Verify tier 1 is detecting issues**:
```bash
# Check for non-nominal statuses
grep -E "STATUS: (stale|error)" .coordination/watcher-log.md
```

**Tier 1 should exit with code 1 when intervention is needed**. If it's always 0 (nominal), it's working correctly.

### Watcher Stops Automatically

**Problem**: Watcher creates its own stop file

**Solution**: This is a **logic error** - watcher should NEVER create stop files.
- Check `watcher_loop.py` prompt for instructions
- Verify prompt says "NEVER create a stop file"
- Status when no agents = `nominal`, NOT `complete`

## Key Insights

### No Active Agents = Normal
- **Wrong**: "No agents = complete → create stop file"
- **Correct**: "No agents = nominal → continue monitoring"

The watcher should run continuously regardless of agent count. It monitors the system, not specific agents.

### Continuous Loop vs Single Pass
- **Wrong**: "Do ONE monitoring pass then exit"
- **Correct**: "Run continuous loop, check every 30 seconds"

The launcher handles the loop. The watcher agent just does ONE check and reports back.

### Exit Codes Matter
- **Exit code 0**: "Check me again in 30 seconds"
- **Exit code 1**: "I need help, call tier 2"
- **Exit code 2**: "Error occurred, retry immediately"

The launcher uses exit codes to decide next action.

## Migration Notes

This watcher was migrated from `/watcher/` to `/Open_ELF/watcher/` to:

1. Follow original ELF directory structure
2. Separate watcher from other components
3. Make it easier to maintain

The `start-elf-system.sh` script can be updated to use:
```bash
python Open_ELF/watcher/launcher.py >logs/watcher.log 2>&1 &
```

## Future Improvements

1. **Log Rotation**: Implement automatic log rotation
2. **Metrics**: Track how often tier 2 is invoked
3. **Alerting**: Send notifications for critical issues
4. **Health Checks**: More sophisticated agent health detection
5. **Web Interface**: Dashboard integration for real-time status
