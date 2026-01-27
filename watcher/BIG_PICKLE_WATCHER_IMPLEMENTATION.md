# big-pickle Watcher Implementation Report

**Adaptation**: From Haiku/Opus to OpenCode big-pickle
**Model**: opencode/big-pickle (local, zero-cost)
**Status**: ✅ COMPLETE
**Date**: 2026-01-28

---

## Summary

Successfully adapted the tiered watcher pattern to use OpenCode's big-pickle model for both Tier 1 (detection) and Tier 2 (decision-making).

The workflow remains identical to the original Haiku/Opus design, with big-pickle replacing both Claude models.

## Architecture Changes

### From Haiku/Opus
```
Haiku (Claude) → Detects issues → Escalates
                                      ↓
                         Opus (Claude) → Makes decisions
```

### To big-pickle (OpenCode)
```
big-pickle → Detects issues → Escalates
                                   ↓
                      big-pickle → Makes decisions
```

**Key Difference**: Both tiers use the same local model, eliminating API costs.

## Implementation: run_with_bigpickle.py

**File**: `watcher/run_with_bigpickle.py`
**Language**: Python 3
**Lines of Code**: ~250
**Design**: Single orchestrator handling both tiers

### Tier 1: Watcher Detection

1. **Generates Prompt**
   - Imports from `watcher_loop.py`
   - Uses original prompt generation (unchanged)
   - Includes coordination state from blackboard.json

2. **Calls big-pickle**
   - Via CLI: `claude --print --model opencode/big-pickle`
   - Sends prompt to model
   - Receives analysis response

3. **Analyzes Response**
   - Checks for issue indicators
   - Extracts status (nominal, warning, critical)
   - Decides if escalation needed

4. **Records Event**
   - Writes to `event_chronicle` table
   - Logs to `.coordination/watcher-log.md`
   - Includes metrics and response data

5. **Returns Exit Code**
   - Code 0: No issues, nominal state
   - Code 1: Issues detected, escalate to Tier 2

### Tier 2: Handler Decision-Making

1. **Triggered by Exit Code 1**
   - Only runs if Tier 1 found issues
   - Skipped for nominal state

2. **Generates Handler Prompt**
   - Imports from `watcher_loop.py`
   - Sends escalation context (Tier 1 analysis)
   - Requests decision from big-pickle

3. **Calls big-pickle for Decision**
   - Same CLI as Tier 1
   - Full context available (can read blackboard.json)
   - Returns decision analysis

4. **Parses Decision**
   - Extracts action: RESTART | ABANDON | ESCALATE
   - Updates blackboard.json if needed
   - Logs decision to `.coordination/decision.md`

5. **Records Event**
   - Writes to `event_chronicle` table
   - Logs decision and outcome
   - Includes decision data and metadata

6. **Returns Exit Code**
   - Code 0: Tier 2 resolved the issue
   - Code 1: Tier 2 escalated (needs human decision)
   - Code 2: Error occurred

## Configuration

Edit `watcher/run_with_bigpickle.py`:

```python
# CLI command to invoke big-pickle (line ~35)
def call_bigpickle(prompt: str) -> Tuple[str, bool]:
    result = subprocess.run(
        ["claude", "--print", "--model", "opencode/big-pickle"],
        ...
    )

# Timeout for big-pickle response (line ~40)
timeout=120,  # seconds

# Logging level (line ~50)
log_to_file(message)  # Writes to .coordination/watcher-log.md
```

## Event Recording

Both tiers record to `event_chronicle` table:

### Tier 1 Events
```json
{
  "event_type": "watcher_cycle",
  "source": "watcher",
  "status": "nominal|warning|critical",
  "summary": "Watcher analysis result",
  "data": {
    "tier": 1,
    "response_lines": 42
  }
}
```

### Tier 2 Events
```json
{
  "event_type": "handler_decision",
  "source": "watcher",
  "status": "varies",
  "summary": "Handler decision and action",
  "data": {
    "tier": 2,
    "escalation_reason": "stale agents detected",
    "decision": "RESTART"
  }
}
```

## Logging

All activities logged to `.coordination/watcher-log.md`:

```
2026-01-28T10:30:45.123456 | [TIER 1] Watcher analysis: nominal
2026-01-28T10:30:46.234567 | No escalation needed (system nominal)
2026-01-28T10:31:15.345678 | [TIER 1] Watcher analysis: warning
2026-01-28T10:31:16.456789 | [TIER 2] Handler decision: RESTART
2026-01-28T10:31:17.567890 | Handler restarted stale agent worker-1
```

## Usage

```bash
# Single pass (Tier 1 only, or Tier 1+2 if issues)
python run_with_bigpickle.py

# Continuous loop (30 second intervals)
python run_with_bigpickle.py --loop 30

# Custom interval
python run_with_bigpickle.py --loop 60

# Via startup script
./scripts/start-watcher-bigpickle.sh
./scripts/start-watcher-bigpickle.sh --once
./scripts/start-watcher-bigpickle.sh --interval 60
```

## Advantages over Haiku/Opus

| Feature | Haiku/Opus | big-pickle |
|---------|-----------|-----------|
| Cost | $3.88/day | $0/day |
| Model | External API (Claude) | Local (OpenCode) |
| Latency | Network dependent | Local, instant |
| Tier 1 Speed | Fast | Instant (local) |
| Tier 2 Speed | Varies | Instant (local) |
| Capability | Haiku↔Opus | big-pickle (both) |
| Dependencies | ANTHROPIC_API_KEY | OpenCode CLI |

## Compatibility

- ✅ Uses existing `watcher_loop.py` prompts (unchanged)
- ✅ Same `blackboard.json` format
- ✅ Same `.coordination/` structure
- ✅ Same exit codes (0, 1, 2)
- ✅ Same decision logic (RESTART, ABANDON, ESCALATE)
- ✅ Writes to same tables (event_chronicle)
- ✅ No breaking changes

## Validation

Both tiers validated via:

```bash
# Single pass test
./scripts/start-watcher-bigpickle.sh --once

# Check events recorded
sqlite3 memory/index.db "SELECT * FROM event_chronicle WHERE source='watcher';"

# View logs
tail -f .coordination/watcher-log.md

# Check via API
curl http://localhost:8888/api/chronicle/events?source=watcher&hours=1
```

## Notes

- big-pickle runs locally (no network dependency)
- Both Tier 1 and Tier 2 use same model
- Prompt format unchanged from original
- All logging and event recording maintained
- Zero API costs (local model)

The workflow is identical to the original Haiku/Opus system,
just with big-pickle handling both analysis and decision-making.
