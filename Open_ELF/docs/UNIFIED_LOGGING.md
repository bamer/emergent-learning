# Unified ELF Logging System

## Overview

The Unified ELF Logging System provides centralized logging for all agents, daemons, and components in the Emergent Learning Framework. All logs are written to a single directory: `/home/bamer/.opencode/emergent-learning/logs/`

## Philosophy: "Ça marche ou ça crash"

The logging system follows the ELF philosophy: **critical errors will crash the system rather than fail silently**. This ensures that serious issues are immediately visible and cannot be ignored.

## Usage

### Basic Usage

All agents and daemons MUST use the unified logging system:

```python
from elf_logging import get_logger, log_critical, log_error, log_warning, log_info

# Get a logger for your module
logger = get_logger("my_agent")

# Use it like standard logging
logger.info("System starting...")
logger.warning("Low memory detected")
logger.error("Failed to connect to database")
logger.critical("SYSTEM FAILURE - SHUTTING DOWN")  # Will crash the system!
```

### Direct Helper Functions

For quick logging without getting a logger instance:

```python
from elf_logging import log_info, log_warning, log_error, log_critical

log_info("my_agent", "Information message")
log_warning("my_agent", "Warning message")
log_error("my_agent", "Error message")
log_critical("my_agent", "Critical message", crash=True)  # Will exit!
```

## Migration Guide

### From Standard Python Logging

**Before (❌ INCORRECT):**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Message")
```

**After (✅ CORRECT):**
```python
# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from elf_logging import get_logger, log_critical, log_error, log_warning, log_info
    logger = get_logger("my_module")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("my_module")

logger.info("Message")
```

### Automated Migration

A migration script is available to update all files automatically:

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF
python3 scripts/migrate_to_unified_logger.py
```

To preview changes without applying them:

```bash
python3 scripts/migrate_to_unified_logger.py --dry-run
```

## Log Directory Structure

All logs are centralized in:
```
/home/bamer/.opencode/emergent-learning/logs/
├── agent_manager.log
├── alert_agent.log
├── central_orchestrator.log
├── dashboard.log
├── event_bridge.log
├── elf_sentinel.log
├── sentinel_monitor.log
├── unified_orchestrator.log
├── CRASH.log  # Critical errors that crashed the system
└── ... (one log per component)
```

## Log Format

All logs use the standardized format:
```
2026-02-07 23:15:35,292 - [AgentManager] - INFO - Message here
```

Components:
- **Timestamp**: ISO format with milliseconds
- **Component Name**: In brackets for easy filtering
- **Level**: INFO, WARNING, ERROR, CRITICAL
- **Message**: The actual log message

## Critical Errors and Crash Policy

When a `CRITICAL` level log is emitted, the system will:

1. Write detailed crash information to `/home/bamer/.opencode/emergent-learning/logs/CRASH.log`
2. Print crash details to stderr
3. **Exit with error code 1** (crash the system)

This ensures critical issues cannot be ignored.

### Crash Log Format

```
======================================================================
CRITICAL ERROR - SYSTEM CRASH
======================================================================
Timestamp: 2026-02-07T23:15:35.292001
Logger: my_agent
Level: CRITICAL
Message: Database corruption detected - cannot continue
======================================================================
```

## Components Using Unified Logging

The following components have been migrated to use the unified logging system:

### Core Components
- ✅ `agents/agent_manager.py`
- ✅ `agents/sentinel_monitor.py`
- ✅ `agents/alert_agent.py`
- ✅ `agents/pattern_response_handler.py`
- ✅ `orchestrator/event_bridge.py`
- ✅ `orchestrator/unified_orchestrator.py`
- ✅ `sentinel/elf_sentinel.py`
- ✅ `core/central_orchestrator.py`

### Mission Engine
- ✅ `mission-engine/mission_engine.py`
- ✅ `mission-engine/mission_live_handler.py`

### Query System
- ✅ `query/agent_config.py`
- ✅ `query/fraud_detector.py`
- ✅ `query/launch_agents.py`
- ✅ `query/migrations.py`

### Dashboard Backend
- ✅ `dashboard-app/backend/main.py`
- ✅ `dashboard-app/backend/routers/*.py`
- ✅ `dashboard-app/backend/session_index.py`
- ✅ `dashboard-app/backend/utils/*.py`

### Utilities
- ✅ `scripts/record-heuristic.py`
- ✅ `scripts/backfill-heuristic-embeddings.py`
- ✅ `timeline_dashboard/timeline_api.py`
- ✅ `utils/event_logger.py`

## Troubleshooting

### Issue: "Last log is more than 30 minutes old"

**Cause**: The component is not using the unified logging system.

**Solution**: 
1. Check if the component imports from `elf_logging`
2. Run the migration script: `python3 scripts/migrate_to_unified_logger.py`
3. Restart the component

### Issue: Logs not appearing in unified directory

**Cause**: Component using basic Python logging instead of unified logger.

**Solution**:
1. Verify the component has been migrated
2. Check for ImportError fallbacks that might be using basic logging
3. Ensure `elf_logging.py` is in the Python path

### Issue: Missing log files

**Cause**: Logger not initialized or component not started.

**Solution**:
```python
# Ensure this pattern is at the top of your file
try:
    from elf_logging import get_logger
    logger = get_logger("your_component")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("your_component")
```

## Best Practices

1. **Always use unified logger**: Never use `import logging` directly in new code
2. **Use descriptive logger names**: Use the module name (e.g., `get_logger("sentinel_monitor")`)
3. **Appropriate log levels**:
   - `INFO`: Normal operations, lifecycle events
   - `WARNING`: Issues that don't prevent operation
   - `ERROR`: Errors that impact functionality
   - `CRITICAL`: System-level failures (will crash!)
4. **Include context**: Add relevant data to log messages
   ```python
   logger.error(f"Failed to connect to {host}:{port}")
   ```
5. **Don't catch and hide critical errors**: Let them crash the system

## API Reference

### `get_logger(name: str, level: int = logging.INFO) -> logging.Logger`

Get a centralized logger for an agent or daemon.

**Args:**
- `name`: Name of the agent/daemon (used for log file)
- `level`: Logging level (default: INFO)

**Returns:**
- Configured logger instance

### `log_info(agent: str, message: str)`

Log an info message for an agent.

### `log_warning(agent: str, message: str)`

Log a warning message for an agent.

### `log_error(agent: str, message: str)`

Log an error message for an agent.

### `log_critical(agent: str, message: str, crash: bool = False)`

Log a critical message for an agent. If `crash=True`, the system will exit.

## Implementation Details

The unified logging system is implemented in:
```
/home/bamer/.opencode/emergent-learning/Open_ELF/agents/elf_logging.py
```

Key features:
- Centralized log directory
- Crash policy handler (enforces "ça marche ou ça crash")
- Duplicate handler prevention
- Automatic file rotation (via Python's logging module)

## Related Documentation

- [Agent Manager](./agents/agent_manager.md)
- [Event Bridge Logging Improvements](./EVENT_BRIDGE_LOGGING_IMPROVEMENTS.md)
- [Operations Guide](./OPERATIONS.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## Migration History

- **2026-02-07**: Migrated 35 files to unified logging system
- **Files updated**: All agents, orchestrators, dashboard backend, query system
- **Migration script**: `scripts/migrate_to_unified_logger.py`
