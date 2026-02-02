# Monitoring System Improvements

## Current Issues Identified

1. **Database Integrity Check** - Typo "ntegrity" → should be "Integrity"
2. **Watcher Status** - Process running but no checks since 5 AM
3. **Missing Cards** - Need Watcher and Orchestrator event cards like Event Bridge
4. **Ollama Embeddings** - Need monitoring status

## Action Plan

### 1. Fix System Health Monitoring
- Update system_health table columns to match code
- Fix typo in integrity check display
- Add proper monitoring endpoints

### 2. Add Watcher Event Card
- Create endpoint for last 20 watcher events
- Similar structure to Event Bridge card
- Include file monitoring activities

### 3. Add Orchestrator Event Card  
- Create endpoint for last 20 orchestrator events
- Show questions received and responses
- Similar structure to Watcher card

### 4. Add Ollama Embeddings Monitoring
- Check Ollama service status
- Test embedding generation
- Add to system health monitoring

## Implementation

The monitoring system needs updates to:
1. `/routers/monitoring.py` - Fix system health queries
2. Add new endpoints for watcher/orchestrator events
3. Update frontend to display new cards
4. Add Ollama health checks
