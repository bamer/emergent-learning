# Tiered Watcher with big-pickle - Quick Start Guide

## Prerequisites

big-pickle must be available via OpenCode CLI:
```bash
claude --model opencode/big-pickle --help  # Should work
```

## Start the Watcher

```bash
# Single pass (manual check)
./scripts/start-watcher-bigpickle.sh --once

# Continuous (30s intervals, Ctrl+C to stop)
./scripts/start-watcher-bigpickle.sh

# Custom interval (60 seconds)
./scripts/start-watcher-bigpickle.sh --interval 60
```

## Monitor Activity

```bash
# Watch watcher logs
tail -f .coordination/watcher-log.md

# Check event chronicle
sqlite3 memory/index.db "SELECT * FROM event_chronicle WHERE source='watcher' ORDER BY id DESC LIMIT 10;"

# View via API
curl http://localhost:8888/api/chronicle/events?source=watcher&hours=1
```

## What to Expect

1. **Tier 1**: big-pickle analyzes coordination state
2. **Tier 1**: Polls `.coordination/blackboard.json` for issues
3. **Tier 1**: Exits with code 0 (nominal) or 1 (issues detected)
4. **If issues** → **Tier 2**: big-pickle handler (CEO) invoked
5. **Tier 2**: Reads full context, makes decision (RESTART/ABANDON/ESCALATE)
6. **Tier 2**: Updates blackboard.json, exits
7. **Logs**: Events recorded to event_chronicle table

## Exit Codes

- **0**: Normal completion (no issues or Tier 2 resolved)
- **1**: Tier 2 escalated to human (ESCALATE decision)
- **2**: Error occurred (will need manual inspection)

## Files to Watch

- `.coordination/watcher-log.md` - Watcher/Handler logs
- `.coordination/blackboard.json` - Agent coordination state
- `.coordination/decision.md` - Handler decisions
- `memory/index.db` - event_chronicle table
- `logs/watcher.log` - Full logs

## Configuration

Edit `watcher/run_with_bigpickle.py` to change:

```python
# Model name (line ~35)
["claude", "--print", "--model", "opencode/big-pickle"]

# Timeout (line ~40)
timeout=120,  # seconds

# Interval in script (line ~200)
interval=30  # seconds
```

## Troubleshooting

**Problem**: "Error calling big-pickle"
```bash
which claude  # Should exist
claude --model opencode/big-pickle --version  # Should work
```

**Problem**: Watcher not writing to logs
```bash
ls -la .coordination/watcher-log.md  # Should exist
# Check permissions on .coordination/
```

**Problem**: No events recorded
```bash
sqlite3 memory/index.db ".tables" | grep event_chronicle
# If missing, event_chronicle table needs creation
```

## Full Documentation

See `README.md` for complete documentation, architecture details, and advanced usage.

---

*Part of the Emergent Learning Framework*
