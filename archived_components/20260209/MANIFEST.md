# Archived Components Manifest

**Archive Date**: 2026-02-09
**Reason**: ELF Learning Workflow Refactoring

## Files Archived

### Monitoring Components (Merged)
- `Open_ELF/watcher/elf_watcher.py` → Replaced by `core/watcher.py`
- `agents/sentinel_monitor.py` → Merged into `core/watcher.py`

### Event Handling (Consolidated)
- `Open_ELF/orchestrator/event_bridge.py` → Replaced by `core/event_bridge_v2.py`

### Learning Operations (Centralized)
- `hooks/learning-loop/post_tool_learning.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/record_pheromone.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/pre_tool_learning.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/pre_tool_semantic_memory.py` → Merged into `core/learning_processor.py`
- `hooks/learning-loop/user_prompt_inject_context.py` → Merged into `core/learning_processor.py`

### Workflow (Integrated)
- `conductor/conductor.py` → Trail functionality moved to `core/learning_processor.py`
- `pattern_response_handler.py` → Integrated into `core/learning_processor.py`

## New Architecture

```
Level 1: core/watcher.py (merged Watcher + Sentinel)
Level 2: Open_ELF/orchestrator/unified_orchestrator.py (service management)
Level 3: CEO agent (strategic decisions)

Supporting:
- core/learning_processor.py (all learning + trails)
- core/event_bridge_v2.py (event routing)
```

## Restoration

If you need to restore these files:
1. Copy from this archive directory back to original location
2. Update imports and dependencies
3. Test thoroughly before production use

## Documentation

See `../REFACTORING_SUMMARY.md` for complete refactoring details.
