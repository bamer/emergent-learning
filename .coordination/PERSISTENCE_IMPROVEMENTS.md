# Persistence System Improvements

## Summary

1. **WatcherEventHistory Import Error**: The file still exists but is no longer exported. The error is likely from browser cache. Fixed by removing exports from:
   - `frontend/src/components/index.ts`
   - `frontend/src/components/monitoring/index.ts`

   **Solution**: Clear browser cache and restart the dev server.

2. **Event Chronicles Dual Logging**: All timeline events are now saved to BOTH:
   - SQLite database (event_chronicle table)
   - File-based EventChronicle (JSONL files in event_chronicle/)

   This ensures data persistence and audit trails.

3. **Embeddings with Ollama**: All heuristics and learnings are automatically:
   - Saved to database
   - Embedded using Ollama (nomic-embed-text model)
   - Stored in embeddings table for semantic search

4. **Unified Logging**: Backend logs now write to:
   - Console (for development)
   - File: `.coordination/dashboard.log` (for persistence)

## API Endpoints

### Persistence Router (`/api/v1/persistence`)

**Trails**:

- `POST /trails` - Create a trail
- `POST /trails/batch` - Create multiple trails

**Heuristics** (with automatic embeddings):

- `POST /heuristics` - Create a heuristic with Ollama embedding
- `POST /heuristics/batch` - Create multiple heuristics with embeddings

**Timeline Events** (dual logging):

- `POST /timeline/events` - Create event in DB + EventChronicle
- `POST /timeline/events/batch` - Batch create with dual logging

**Learnings** (with automatic embeddings):

- `POST /learnings` - Create a learning with Ollama embedding
- `POST /learnings/batch` - Create multiple learnings with embeddings

## Frontend Service

`frontend/src/services/persistence.ts` provides:

- All API call functions
- Helper functions: `recordDiscovery()`, `recordWarning()`, `recordBlocker()`
- Auto-extraction: `extractAndSaveHeuristics()`, `autoExtractLearnings()`

## Log Files

- `.coordination/dashboard.log` - Backend API logs
- `.coordination/sentinel-log.md` - Watcher agent logs
- `.coordination/event-bridge-heartbeat.json` - Event bridge status
- `event_chronicle/` - Immutable event logs (JSONL format)

## Next Steps

1. Clear browser cache to fix import error
2. Restart backend server to enable new logging
3. Test endpoints with frontend
4. Verify events appear in both database and files
