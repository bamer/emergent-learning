# Semantic Embedding System - Operations Guide

## Overview

The ELF Semantic Embedding System provides vector embeddings for heuristics, learnings, failures, and other knowledge artifacts. It enables semantic search across the entire ELF knowledge base.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ELF Scripts   │────▶│  Semantic Daemon │────▶│   Ollama Server │
│ (record, query) │     │   (port 5001)    │     │  (port 11434)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │   SQLite Database │
                      │  (index.db)      │
                      └──────────────────┘
```

## Components

### 1. Ollama Server (Port 11434)
- **Model**: `nomic-embed-text` (768 dimensions)
- **Purpose**: Generates embeddings via API
- **Status**: Always running as system service

### 2. Semantic Daemon (Port 5001)
- **Script**: `semantic/daemon.py`
- **Purpose**: 
  - Flask API for embedding generation
  - Database storage and retrieval
  - Semantic search endpoints
- **Database**: `/home/bamer/.opencode/emergent-learning/memory/index.db`

### 3. Database (index.db)
- **Location**: `/home/bamer/.opencode/emergent-learning/memory/index.db`
- **Tables**:
  - `heuristics` - Heuristic rules and metadata
  - `embeddings` - Vector embeddings for all content
  - `learnings` - Session learnings and summaries
  - `failures` - Failure records and analysis

## Startup Procedures

### Manual Start (Development)

```bash
# 1. Ensure Ollama is running
ollama serve  # Usually runs as systemd service

# 2. Kill any existing daemon
pkill -9 -f "daemon.py"

# 3. Start semantic daemon
cd /home/bamer/.opencode/emergent-learning/semantic
python3 daemon.py --port 5001
```

### Automatic Start (Production)

```bash
# Use the startup script (handles cleanup automatically)
cd /home/bamer/.opencode/emergent-learning
./start-elf-system.sh
```

The startup script performs:
1. Aggressive port cleanup (pkill + lsof + fuser)
2. Port availability verification
3. Daemon startup without `--daemon` flag
4. Network listening verification

## Maintenance Tasks

### Check Daemon Status

```bash
# Check if daemon is running
ps aux | grep "daemon.py.*5001"

# Check if port is listening
netstat -tlnp | grep 5001
# or
ss -tlnp | grep 5001

# Check daemon health
curl http://localhost:5001/health

# View daemon statistics
curl http://localhost:5001/stats | python3 -m json.tool
```

### Check Embedding Statistics

```bash
# Via API
curl http://localhost:5001/stats | python3 -m json.tool

# Output example:
{
  "total_embeddings": 2037,
  "by_source": {
    "heuristic": 209,
    "learning": 500,
    "failure": 1300
  },
  "recent_24h": 31
}

# Direct database query
sqlite3 /home/bamer/.opencode/emergent-learning/memory/index.db \
  "SELECT source_type, COUNT(*) FROM embeddings GROUP BY source_type;"
```

### Backfill Missing Embeddings

After bulk importing heuristics or other content:

```bash
# For heuristics
python3 /home/bamer/.opencode/emergent-learning/scripts/backfill-heuristic-embeddings.py

# For other content types, create similar script or use API:
curl -X POST http://localhost:5001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here"}'
```

### Database Unification

If multiple `index.db` files exist:

```bash
# Run unification script
python3 /home/bamer/.opencode/emergent-learning/scripts/unify-databases.py

# This will:
# 1. Merge all databases into primary
# 2. Create symlinks from legacy paths
# 3. Verify consistency
```

## Troubleshooting

### Problem: Embedding Rate Shows 0

**Symptoms**: Dashboard shows "Embedding Rate: 0" despite new heuristics

**Causes**:
1. Daemon not running
2. Wrong database path
3. Port conflict
4. Ollama server down

**Solution**:
```bash
# 1. Check daemon
ps aux | grep "daemon.py.*5001"

# 2. Check Ollama
ollama ps

# 3. Restart daemon
pkill -9 -f "daemon.py"
cd /home/bamer/.opencode/emergent-learning/semantic
python3 daemon.py --port 5001 &

# 4. Verify
curl http://localhost:5001/stats

# 5. If still 0, run backfill
python3 /home/bamer/.opencode/emergent-learning/scripts/backfill-heuristic-embeddings.py
```

### Problem: Port 5001 Already in Use

**Symptoms**: Daemon fails to start with "Address already in use"

**Solution**:
```bash
# Find process using port 5001
lsof -ti:5001

# Kill it
kill -9 $(lsof -ti:5001)

# Or use startup script (handles this automatically)
./start-elf-system.sh
```

### Problem: DaemonContext AttributeError

**Symptoms**: `AttributeError: module 'daemon' has no attribute 'DaemonContext'`

**Cause**: Missing `python-daemon` package

**Solution**: Run daemon WITHOUT `--daemon` flag:
```bash
python3 daemon.py --port 5001  # No --daemon flag
```

The script will still run in background when started via `nohup` or `&`.

### Problem: Multiple Database Files

**Symptoms**: Data appears in one database but not another

**Diagnosis**:
```bash
# Find all index.db files
find /home/bamer/.opencode -name "index.db" -type f

# Check each one
for db in $(find /home/bamer/.opencode -name "index.db"); do
  echo "=== $db ==="
  sqlite3 "$db" "SELECT COUNT(*) FROM heuristics;"
done
```

**Solution**: Run unification script
```bash
python3 /home/bamer/.opencode/emergent-learning/scripts/unify-databases.py
```

## API Endpoints

### Generate Embedding
```bash
curl -X POST http://localhost:5001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here"}'
```

### Store Text with Embedding
```bash
curl -X POST http://localhost:5001/store \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "heuristic-123",
    "source_type": "heuristic",
    "text": "Your text here",
    "metadata": {"domain": "python"}
  }'
```

### Semantic Search
```bash
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Your search query",
    "top_k": 10
  }'
```

### Health Check
```bash
curl http://localhost:5001/health
```

### Statistics
```bash
curl http://localhost:5001/stats
```

## Monitoring

### Dashboard
Access the ELF Dashboard at `http://localhost:3001/` and check:
- **Embedding Rate** (Last Hour, 24 Hours, 7 Days, 30 Days)
- **Total Embeddings**
- **Semantic Service Status**

### Logs
```bash
# Daemon logs
tail -f /home/bamer/.opencode/emergent-learning/Open_ELF/logs/semantic-daemon.log

# Ollama logs (journalctl if running as systemd service)
journalctl -u ollama -f
```

## Best Practices

1. **Always use startup script** for production deployments
2. **Run backfill** after bulk imports
3. **Monitor embedding rate** - should be > 0 if system is active
4. **Check database consistency** monthly
5. **Keep Ollama model updated**: `ollama pull nomic-embed-text`
6. **Backup database regularly**: `sqlite3 index.db .backup > backup.db`

## Version History

- **2026-02-19**: Database unification, startup script fixes, backfill automation
- **2026-02-11**: Semantic daemon integrated with unified logging
- **2026-02-05**: Initial semantic search implementation

## Support

For issues:
1. Check logs first
2. Verify daemon and Ollama are running
3. Check database path consistency
4. Review this guide's troubleshooting section
