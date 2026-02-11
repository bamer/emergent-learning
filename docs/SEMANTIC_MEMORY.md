# Semantic Memory System (MANDATORY)

## Overview
The ELF system requires a **semantic memory** component using Ollama embeddings for similarity-based search of learnings and memories.

**IMPORTANT: This is a MANDATORY component** of the learning system. The full learning capabilities depend on semantic search working properly.

## Status
- **Ollama**: 🟡 **REQUIRED** for embeddings (must be running)
- **Semantic Daemon**: 🟡 **REQUIRED** for embedding storage (`http://localhost:5001`)
- **Current Status**: Non-blocking errors - learning capture continues but with ERROR logging

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Learning Capture                        │
│                   (Always Running)                         │
└────────────────────────┬────────────────────────────────┘
                         │
            ┌────────────▼────────────┐
            │   Embedding Storage    │
            │   (MANDATORY but        │
            │    non-blocking)        │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │   Semantic Daemon        │
            │   (localhost:5001)     │
            │   ⚠️ REQUIRED          │
            │   - Store embeddings   │
            │   - Semantic search     │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │   Ollama                │
            │   ⚠️ REQUIRED          │
            │   - Generate embeddings │
            └───────────────────────────┘
```

    def _store_embedding(self, text: str, source_id: str, source_type: str, metadata: Optional[Dict] = None):
        """
        Store text with embedding in semantic daemon (MANDATORY but non-blocking).

        MANDATORY: Semantic memory is required for the full learning system.
        NON-BLOCKING: Errors are logged as ERROR but learning capture continues.

        Errors are tracked in the database for monitoring and alerting.
        """
        success = False

        try:
            # Attempt to store embedding
            with urllib.request.urlopen(...) as resp:
                success = True

        except urllib.error.URLError as e:
            # MANDATORY system not running - log as ERROR (not debug)
            # This violates golden rule: semantic daemon should be running
            logger.error(
                f"[SEMANTIC_FAILURE] Semantic daemon unavailable ({e}) - "
                f"Source: {source_type}:{source_id}. "
                f"This is a MANDATORY component - ensure Ollama and semantic daemon are running."
            )

            # Track failure in database for monitoring
            self._track_semantic_failure("daemon_unavailable", source_type, str(e))

        except Exception as e:
            logger.error(f"[SEMANTIC_FAILURE] Failed to store embedding: {e}", exc_info=True)

            # Track failure in database for monitoring
            self._track_semantic_failure("storage_error", source_type, str(e))

        return success
```

## Requirements

### Optional: With Semantic Search
1. **Ollama installed and running**
2. **Semantic daemon running** (`python -m semantic.daemon`)
3. **Ollama model available** (e.g., `nomic-embed-text`, `all-minilm`)

### Minimal: Without Semantic Search
1. **Just the database** - learning capture works normally
2. **Keyword-based search** - use `query.py --context` with keywords

## Usage

### Semantic Search (when daemon is running)
```bash
# Search for similar past experiences
python query.py --context "database connection timeout" --depth standard

# Returns:
# - Golden rules matching query
# - Semantically similar heuristics
# - Relevant learnings from past sessions
```

### Keyword Search (always available)
```bash
# Search by keyword/domain
python query.py --context --domain database

# Returns:
# - Golden rules for domain
# - Heuristics with matching keywords
# - Learnings tagged with domain
```

## Startup Commands

### Start Ollama (REQUIRED)
```bash
# Install Ollama (once)
curl -fsSL https://ollama.gg/install.sh | sh

# Pull embedding model (once)
ollama pull nomic-embed-text

# Start Ollama (REQUIRED - should run at all times)
ollama serve
```

### Start Semantic Daemon (REQUIRED)
```bash
# From emergent-learning directory
# REQUIRED - should run at all times
python -m semantic.daemon
```

### Verification
```bash
# Check both services are running
pgrep -f "ollama" > /dev/null && echo "✓ Ollama: RUNNING" || echo "✗ Ollama: STOPPED (REQUIRED)"
lsof -i :5001 > /dev/null && echo "✓ Semantic Daemon: RUNNING" || echo "✗ Semantic Daemon: STOPPED (REQUIRED)"
```

## Configuration

### Environment Variables
```bash
# Default: http://localhost:5001
export SEMANTIC_DAEMON_URL="http://localhost:5001"

# Default: nomic-embed-text
export SEMANTIC_MODEL="nomic-embed-text"
```

### Learning Processor
```python
# In learning_processor.py
SEMANTIC_DAEMON_URL = "http://localhost:5001"
```

## Error Messages

### "[SEMANTIC_FAILURE] Semantic daemon unavailable"
**Cause**: Semantic daemon not running (MANDATORY system is down)

**Severity**: 🔴 **ERROR** (not debug/warning)

**Impact**: Learning capture continues WITHOUT embeddings. Reduced search capabilities.

**Required Action**: Start semantic daemon (it's mandatory!)

```bash
python -m semantic.daemon
```

### "[SEMANTIC_FAILURE] Failed to generate embedding"
**Cause**: Ollama not running or model not available

**Severity**: 🔴 **ERROR** (not debug/warning)

**Impact**: Learning capture continues WITHOUT embeddings. Reduced search capabilities.

**Required Action**: Start Ollama (it's mandatory!)

```bash
ollama serve
```

### "Connection refused on localhost:5001"
**Cause**: Semantic daemon not running

**Severity**: 🔴 **ERROR** - logged under `semantic_failure` metric

**Impact**: Learning capture continues but semantic search unavailable

**Required Action**: Start semantic daemon immediately

```bash
python -m semantic.daemon
```

### Tracking Semantic Failures

Failures are tracked in the database for monitoring:

```sql
-- Check recent semantic failures
SELECT timestamp, metric_name, context, metric_value
FROM metrics
WHERE metric_type = 'semantic_failure'
ORDER BY timestamp DESC
LIMIT 10;
```

## Benefits

### With Semantic Memory (EXPECTED STATE)
- **Contextual similarity** - Find learnings based on meaning, not just keywords
- **Semantic recommendations** - Get relevant heuristics even with different terminology
- **Cross-domain insights** - Discover patterns across different domains
- **Full learning capabilities** - Complete coverage of all learning mechanisms

### Without Semantic Memory (DEGRADED STATE)
- **Reduced search** - Only keyword-based search available
- **Limited discovery** - Missing contextual relationships between learnings
- **Degraded golden rule promotion** - Reduced ability to identify related patterns
- **Error accumulation** - `semantic_failure` metrics will indicate degraded state

**This is NOT an intended state - semantic memory is MANDATORY.**

## Decision Matrix

| Scenario | Action Required |
|----------|----------------|
| **Production System** | ✅ MUST ENSURE Ollama + Semantic Daemon running |
| **Development Setup** | ✅ MUST ENSURE Ollama + Semantic Daemon running |
| **AI Research** | ✅ FULLY ENABLE semantic search |
| **Quick Testing** | ✅ START services first |
| **Domain Exploration** | ✅ USE semantic search for better insights |

**Guideline**: Semantic memory is NOT optional - it's a core component of the learning system. Treat Ollama and semantic daemon as critical infrastructure.

## Migration

### From No-Semantic to Full-Semantic
To enable the full learning system with semantic memory:

1. ✅ Install Ollama: `curl -fsSL https://ollama.gg/install.sh | sh`
2. ✅ Start Ollama (daemon): `ollama serve` - SHOULD BE ALWAYS RUNNING
3. ✅ Pull model: `ollama pull nomic-embed-text`
4. ✅ Start semantic daemon: `python -m semantic.daemon` - SHOULD BE ALWAYS RUNNING
5. ✅ Verify: Check for `[SEMANTIC_FAILURE]` errors in logs
6. ✅ Monitor: Check `semantic_failure` metrics in database

### From Partial to Full Coverage
If semantic failures are occurring:

```bash
# Check which component is failing
grep "SEMANTIC_FAILURE" /home/bamer/.opencode/emergent-learning/logs/*.log

# Check database for semantic failure metrics
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "
SELECT timestamp, metric_name, COUNT(*) as count
FROM metrics
WHERE metric_type = 'semantic_failure'
GROUP BY metric_name, timestamp
ORDER BY timestamp DESC
LIMIT 10;
"

# Fix issues:
# - "daemon_unavailable": Start semantic daemon
# - "storage_error": Check semantic daemon logs
# - "embedding_error": Check Ollama and model
```!

## Monitoring

### Check Semantic System Status
```bash
# Check Ollama status
pgrep -f ollama && echo "✓ Ollama: RUNNING" || echo "✗ Ollama: STOPPED (REQUIRED)"

# Check Semantic Daemon status
lsof -i :5001 && echo "✓ Semantic Daemon: RUNNING" || echo "✗ Semantic Daemon: STOPPED (REQUIRED)"

# Check for recent semantic failures
grep "SEMANTIC_FAILURE" /home/bamer/.opencode/emergent-learning/logs/*.log | tail -20
```

### Database Monitoring
```sql
-- Learnings are always captured in database
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM heuristics;"
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM learnings WHERE type='learning';"

-- Check semantic failure rate
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "
SELECT
    DATE(timestamp) as date,
    metric_name,
    COUNT(*) as failures
FROM metrics
WHERE metric_type = 'semantic_failure'
  AND timestamp > datetime('now', '-7 days')
GROUP BY date, metric_name
ORDER BY date DESC;
"

-- Expected result: 0 failures (semantic system should be working)
-- If you see failures, Ollama/daemon are NOT running properly
```

## Troubleshooting

### Problem: "Failed to generate embedding" errors in logs
**Diagnosis**: Semantic system unavailable

**Solution**: This is expected and non-blocking. Learning capture works without it.

**To Fix (Optional)**: Start Ollama and semantic daemon

### Problem: Learning capture is slow
**Diagnosis**: Trying to contact semantic daemon which is not responding

**Solution**: Already handled - timeout is 5 seconds, non-blocking after that

**To Fix (Optional)**: Start semantic daemon or ignore (learning still works)

### Problem: Can't find similar past learnings
**Diagnosis**: Semantic search not available, using keyword search instead

**Solution**: Use specific domains and keywords with `query.py --context --domain X`

**Example**:
```bash
# Instead of general search
python query.py --context "how to handle errors"

# Use domain-focused search
python query.py --context --domain database error
```

## References

- **Learning Documentation**: `docs/AUTO_LEARNING.md` - Full 3-mechanism auto-learning system
- **Query Documentation**: Running `python query.py --help`
- **Database Schema**: `memory/index.db` tables: `heuristics`, `learnings`, `metrics`, `trails`
- **Golden Rules**: `python query.py --context` always includes golden rules (from database)

---

## Summary

The ELF learning system has **3 required components**:

1. ✅ **Database** (learning storage) - Always required
2. ✅ **3 Learning Mechanisms** (explicit, error-context, anti-pattern) - Always required  
3. ⚠️ **Semantic Memory** (similarity search) - **Required but non-blocking**

### Why Non-Blocking?

The non-blocking design allows the system to **gracefully degrade** while still **alerting administrators** when the MANDATORY semantic components are not working:

```
✓ Learning capture continues (database-first)
✓ Heuristics stored in database (with source_type tracking)
✓ Keyword search works (always available)
✓ Golden rules consulted (from database)
✗ Semantic search degraded (ERROR logged in database)
✗ Embeddings not stored (ERROR logged in database)
```

### Alerting on Semantic Failures

The system maintains **semantic_failure metrics** in the database:

```bash
# Check for recent semantic failures
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db "
SELECT timestamp, metric_name, context, metric_value
FROM metrics
WHERE metric_type = 'semantic_failure'
ORDER BY timestamp DESC
LIMIT 20;
"
```

If you see failures in this table, **Ollama and/or the semantic daemon are not running** - this should be investigated and fixed.

### Operational Checklist

Before running the ELF learning system, ensure:

- [ ] Ollama installed: `ollama --version`
- [ ] Ollama running: `pgrep -f ollama`
- [ ] Embedding model available: `ollama list`
- [ ] Semantic daemon running: `lsof -i :5001`
- [ ] No [SEMANTIC_FAILURE] errors in logs
- [ ] No `semantic_failure` metrics in database

**Rule**: Operate with semantic memory running for full learning capabilities.
