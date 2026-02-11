# Changelog

All notable changes to the Emergent Learning Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

### Added

### Removed

### Fixed

## [0.5.11] - 2026-02-11

### Changed
- **Event Bridge v2**: Added singleton lock to prevent multiple instances
- **Event Bridge v2**: Enabled HTTP status server (/status, /api/v1/health)
- **Experiment Analyzer**: Migrated from EventBridgeClient to AgentManager
- **Agents**: Should use AgentManager instead of Event Bridge for AI calls
- **CEO Inbox Monitor**: Increased AgentManager timeout to 1800s (30 min) for CEO agent strategic decisions
- **CEO Inbox Monitor**: Simplified CEO agent prompt for faster processing
- **CEO Inbox Monitor**: Updated pattern matching to accept any .md file in CEO inbox

### Removed
- **Event Bridge v1**: Deleted `Open_ELF/orchestrator/event_bridge.py` (old version)
- **Event Bridge Client**: Deleted `agents/Fail_event_bridge_client.py` (obsolete)

### Fixed
- **Event Bridge Duplication**: Stopped v1 process, now only v2 runs
- **API Endpoints**: Restored /status and /api/v1/health endpoints in v2
- **CEO Monitor Timeout**: Fixed timeout issue by increasing timeout to 1800s and simplifying prompt
- **CEO Monitor Pattern Matching**: Fixed to accept all .md files in CEO inbox, not just specific patterns

- **CEO Monitor History Tab** - Fixed empty history in Dashboard → Monitoring → CEO Status
  - Updated `/api/v1/ceo/cycles` endpoint to read from correct log locations
  - Now checks `/logs/ceo_inbox_monitor.log` (unified logging) first, then `/coordination/ceo-monitor.log` (legacy)
  - Added parsing for both old and new CEO monitor log formats
  - Extracts CEO 60-min analysis results:
    - Golden rule promotion candidates
    - Active experiments count
    - Recent learnings count
    - Degraded golden rules
    - Unresolved alerts
    - Golden rule violations
  - History tab now displays CEO's hourly analysis cycles with full details
  - Updated `CeoStatusPanel.tsx` History tab to show CEO cycles instead of archived inbox items

### Technical Notes
- All production-level logging uses `get_logger()`, `log_info()`, `log_error()`, `log_warning()`, `log_debug()`
- Test sections (`if __name__ == "__main__":`) may still use `print()` for console output
- Unified logger provides: centralized log location (`/logs/`), database event logging, crash policy enforcement, consistent formatting
- The unified logger is imported from `Open_ELF.utils.elf_logging` with graceful fallback to standard logging

## [0.5.9] - 2026-02-11

### Added
- **Semantic Daemon** - Fully integrated semantic search daemon into startup script (v0.5.5)
  - MANDATORY component for semantic search across learnings, heuristics, and golden rules
  - Automatically starts via `start-elf-system.sh` in all-mode, no-opencode-mode, and test-mode
  - Port 5001 with health endpoint at `http://localhost:5001/health`
  - Supports endpoints: `/embed`, `/store`, `/search`, `/health`, `/stats`

- **Unified Logging Integration** - All components now use `Open_ELF.utils.elf_logging`
  - Semantic daemon logs to `/home/bamer/.opencode/emergent-learning/logs/semantic-daemon.log`
  - Format: `YYYY-MM-DD HH:MM:SS - elf.semantic-daemon - LEVEL - message`
  - Crash policy integration for CRITICAL errors
  - Centralized log rotation (10 MB, 5 backups, 7 day retention)

- **Flask with Async Support** - Requirements updated
  - Added `Flask[async]>=3.0.0` to requirements.txt
  - Added `flask-cors>=4.0.0` to requirements.txt
  - Enables async/await pattern for semantic daemon endpoints (MANDATORY per ELF guidelines)
  - All HTTP requests now use aiohttp with relaxed timeouts (120 seconds)

- **New Heuristics Saved to ELF Memory** - 5 development patterns recorded
  - Always use unified logging (infrastructure, confidence: 0.95)
  - Never use polling for event streaming (infrastructure, confidence: 0.95)
  - Use relaxed timeouts (python, confidence: 0.95)
  - Always use async/await for all new development (python, confidence: 1.00)
  - Handle FTS5 shadow table corruption (database, confidence: 0.90)

### Fixed
- **FTS5 Database Corruption** - Automatic corruption detection and repair
  - Fixed orphaned shadow table issue after crashes in `semantic/daemon.py`
  - Enhanced `init_database()` with automatic repair logic
  - Detects and cleans up inconsistent FTS5 tables
  - System now recovers automatically from FTS5 corruption

- **EventBridge SSE Endpoint** - Fixed wrong endpoint path
  - Changed from `/event` to `/global/event` (OpenCode real SSE endpoint)
  - Changed from `/` to `/global/health` for health check
  - SSE stream now works correctly with proper event format

- **Tool Output Extraction** - Fixed empty tool_output in LearningProcessor
  - `tool_output` was always empty `{}` in synthesized tool events
  - Now correctly extracts `state.output` from OpenCode tool parts
  - LearningProcessor can now analyze tool outputs for heuristics and trails

- **Bash Path Extraction** - Improved file path extraction from bash commands
  - Added pattern for Python modules/scripts (`/[...].py`, `[...].py`)
  - Fixed bash command parsing to extract more file paths
  - Paths now properly recorded in pheromone_trails table

- **Log Noise Reduction** - Reduced verbose logging in EventBridge v2
  - Removed repetitive "Processing tool event" and "LearningProcessor processed" logs
  - Removed verbose debug logs showing full event/part structures
  - Changed polling summary from INFO to DEBUG level
  - EventBridge now logs only errors and important status changes

- **Event Chronicle Recording** - Fixed event logging to metrics table
  - Added `_log_event()` call in `_process_tool_event()` for tool events
  - Events now properly recorded in `metrics` table with type, name, and data
  - 7438+ tool events now logged per hour vs. 0 before fix

- **Database Noise Cleanup** - Removed 24,104 noise events from event_chronicle (60% reduction)
  - Removed auto-save noise: message.updated (11,153), session.status (5,674), session.updated (3,618), session.diff (2,677)
  - Removed session state noise: session.compacted, session.idle
  - Removed connection noise: server.connected, server.instance.disposed
  - Removed LSP noise: lsp.client.diagnostics
  - Kept only important/informative events: tool, health checks, file changes, permissions, commands

- **Test Entries Removed** - Cleaned test data from knowledge base
  - Removed 20 test/maintenance heuristics (domain: test, testing, test-fix)
  - Removed 6 test learning entries (type: test, workflow test runs)
  - Removed 5 test embeddings
  - Removed 13 noise metrics (auto-generated indexes, test metrics)
  - Database size reduced: event_chronicle 40,484→16,380, metrics 34,105→34,092

- **Event Filtering Policy** - Established what to record vs discard
  - KEEP: tool executions, health checks, file changes, permissions, commands, missions
  - DISCARD: auto-save, session state noise, connection events, LSP diagnostics
  - Events now stored in human-readable and user-friendly format

### Changed
- **EventBridge Architecture** - SSE-only streaming mode (polling removed)
  - SSE stream on `/global/event` for real-time events
  - Removed polling backup (caused excessive connections and system failures)
  - Relaxed timeout settings: minimum 20 seconds, maximum 10 minutes for async operations
  - All new components MUST use async/await pattern

- **Startup Script** - Updated to v0.5.5
  - MANDATORY semantic daemon integration
  - Added semantic daemon to status display and cleanup

- **Documentation** - Updated with async/await and timeout guidelines
  - `docs/DEVELOPMENT_GUIDELINES.md` (NEW) - Comprehensive async patterns
  - `docs/ARCHITECTURE-EventBridge.md` - SSE-only architecture documented
  - `CHANGELOG.md` - Removed polling references
  - Integrated semantic daemon as MANDATORY component
  - Updated status display to show semantic daemon health
  - Added semantic daemon to cleanup sequence

### Status (2026-02-11)
- **Trails**: ✅ WORKING (38,378 total, ~1000/hour)
- **Pheromone Trails**: ✅ WORKING (697 total, tracked per file)
- **Tool Events**: ✅ WORKING (16,000+ in last hour)
- **Heuristics**: ⚠️ PARTIAL (115 total, need manual extraction or explicit markers)
- **Learnings**: ⚠️ PARTIAL (421 total, mostly from manual records)

## [0.5.8] - 2026-02-10

### Added
- **Integrated Learning Loop in EventBridge** - Decentralized heuristic and trail learning
  - Added `_extract_and_record_learnings()` method to directly capture heuristics from tool output
  - Added `_extract_and_record_trails()` method to capture file paths from tool operations
  - Both methods triggered automatically on successful tool execution in `_handle_tool_event()`
  - Eliminates dependency on external PostToolUse hooks - learning now flows through EventBridge event stream
  - Heuristic extraction identifies sentences with keywords: "should", "always", "never", "must", "best practice", "lesson", "insight", etc.
  - Trail recording captures read/write operations with appropriate scent strength (0.5 for reads, 0.9 for writes)
  - Proper UPSERT logic: new heuristics inserted with confidence 0.7, existing ones updated with validation count + 0.05 confidence boost

- **Orchestrator L2→L3 Escalation Forwarding** - Connected Sentinel (L1) escalations to CEO (L3)
  - Added `_forward_to_ceo_inbox()` method in UnifiedOrchestrator to forward escalations to CEO inbox
  - Escalations flow: Sentinel (L1) → `.coordination/escalations/` → Orchestrator (L2) → `ceo-inbox/inbox/` → CEO (L3)
  - Archives original escalations after forwarding to maintain audit trail
  - Adds severity header to help CEO prioritize escalations

- **CEO Inbox Monitor Escalation Processing** - Fixed escalation pattern matching
  - Updated `get_pending_escalations()` to recognize all escalation patterns: sentinel_esc_*, sentinel_esc_*, ceo_escalation_*, orchestrator_*
  - CEO monitor now correctly detects and processes escalations from L2 forwarding
  - Integrated 60-minute autonomous system analysis with graceful handling of missing database tables
  - Archives processed escalations with results

### Fixed
- **Heuristic Recording** - Fixed database constraint issue
  - Changed from ON CONFLICT clause (requires UNIQUE constraint) to explicit SELECT/INSERT/UPDATE logic
  - Now properly handles duplicate detection by querying existing heuristics before insert
  - All required columns populated: times_validated, times_violated, is_golden set to defaults
  - Database transactions properly committed/rolled back on errors

- **CEO 60-min Analysis** - Fixed alerts table dependency
  - Wrapped alerts query in try/except to gracefully handle missing table
  - System analysis now completes successfully even if alerts table doesn't exist
  - All other metrics still collected and reported

## [0.5.7] - 2026-02-10

### Removed
- **Legacy Code Files Permanently Deleted** - Clean codebase without old hooks or components
  - Deleted `hooks/post_tool_use/post_tool_learning.py` (replaced by LearningProcessor)
  - Deleted `hooks/post_tool_use/record_pheromone.py` (replaced by LearningProcessor)
  - Deleted `archived_components/` directory (entire archive removed)
  - NO backup or restoration path - final cleanup as per user requirements

### Fixed
- **LearningProcessor Import Path** - Fixed silent import failure in EventBridge
  - Changed `from learning_processor import` to `from core.learning_processor import`
  - Fixed incorrect `logger.warning()` that hid import errors
  - Changed to `logger.error()` with `exc_info=True` for proper error logging

- **All Silent Catch Blocks Fixed** - No more swallowed errors
  - Every `except:` or `except Exception:` block now either logs OR raises
  - Files affected:
    - `core/event_bridge_v2.py` (lines 95, 479)
    - `core/learning_processor.py` (lines 100, 133, 293, 314, multiple others)
    - `core/sentinel.py` (lines 113, 123)
    - `core/monitoring_api.py` (lines 82, 89, 108, 132, 192)
  - All errors now logged with `logger.error(..., exc_info=True)` or re-raised

- **Trail Recording Bug** - Fixed `trails_recorded: 0` issue
  - Root cause: Wrong data structure path in EventBridge
  - Changed `part.get("input", {})` to `part.get("state", {}).get("input", {})`
  - Fixed in two locations:
    - Line 298: `_handle_message_part_updated_event()`
    - Line 365: `_poll_sessions()`
  - Result: Trails now record correctly (`trails_recorded: 2` instead of `0`)

### Changed
- **Unified Logger Enforcement** - All logging now uses ELF unified logger
  - Replaced ALL `print()` statements with `logger.info/warning/error/debug()`
  - Files affected:
    - `core/event_bridge_v2.py` (lines 479, 481; line 477 is user output)
    - `core/init_golden_rules.py` (all print statements for status/error/info)
    - `core/learning_processor.py` (all `print(..., file=sys.stderr)` error statements)
  - CLI final output (e.g., "Done!") still uses print as per exception
  - Error messages now use `logger.error(..., exc_info=True)` for stack traces

- **HTTP Connection Pooling** - Better performance with `requests.Session()`
  - Added `self.http_session = requests.Session()` in EventBridge `__init__`
  - Added `self.http_session = requests.Session()` in Sentinel `__init__`
  - Replaced all `requests.get()` calls with `self.http_session.get()`
  - Added `stop()` method to EventBridge to properly close session
  - Benefits:
    - Connection pooling reuses TCP connections
    - Better performance (avoids TCP handshake overhead)
    - Resource efficiency (reduces open file descriptors)
    - Cookie persistence for session state

### Added
- **Two New Golden Rules** (promoted to `is_golden=1`, confidence 1.0)
  
  **Rule #145 (infrastructure)**: "Always use the unified ELF logger (Open_ELF.utils.elf_logging) for ALL logging. NEVER use print() or exotic loggers."
  - Explanation: Using print() or exotic loggers defeats the purpose of a unified logging system. The ELF unified logger ensures all logs go to the same location, have consistent formatting, and can be tracked in the database.

  **Rule #146 (error-handling)**: "NEVER silently ignore errors. Every error MUST be either logged with the unified ELF logger OR raised (or both). Use logger.error() with exc_info=True for exception details. Bare 'except:' or 'except Exception:' blocks without logging are strictly forbidden."
  - Explanation: Silently swallowing errors makes debugging impossible and hides real problems. The 'ça marche ou ça crash' philosophy means we should either handle errors properly with logging or let the system crash visibly.

## [0.5.6] - 2026-02-10

### Added
- **Semantic Memory Integration** - Task-aware search through learnings and heuristics
  - Integrated semantic search into context building pipeline
  - Minimal mode now includes top 3 semantic matches for provided tasks
  - Standard/deep modes include full semantic search results
  - Semantic memory shows relevance percentages and confidence scores
  - Automatic indexing of heuristics and learnings for semantic matching

- **Database-First Golden Rules** - Golden rules now sourced from database
  - Golden rules stored in `heuristics` table with `is_golden=1`
  - Automatic indexing in semantic memory
  - Confidence and validation count tracking
  - Fallback to golden-rules.md file if database is empty
  - 5-minute caching TTL per session

### Changed
- **Context Query System Enhanced** - New depth levels for context building
  - `--context` (minimal): Golden rules + semantic memory notice + top 3 matches
  - `--context --depth standard`: Golden rules + semantic results + heuristics/learnings
  - `--context --depth deep`: Full context + semantic search + experiments + ADRs
  - Task-aware semantic search: `--context "your task description"`
  - Domain-specific search: `--context --domain debugging --depth standard`

- **Command Documentation Updated**
  - `/checkin` now documents semantic memory queries
  - `/checkout` emphasizes automatic semantic memory indexing
  - `/search` now combines session history + semantic memory search
  - Updated examples for all semantic query patterns

- **Logging Cleanup** - Suppressed verbose initialization messages
  - Migration messages suppressed in production output
  - Peewee connection logs hidden by default
  - Warnings only shown when --debug flag used
  - Query output now clean and agent-friendly

### Fixed
- **Golden Rules Implementation** - Resolved dual implementation conflict
  - Disabled old `get_golden_rules` in queries/heuristics.py (file-based)
  - ContextBuilderMixin now provides authoritative database-first implementation
  - Category matching now supports substring matching (e.g., "core" matches "core-principles")
  - Empty category filter results fallback to full content instead of placeholder

### Technical Details
- **Semantic Search Configuration**
  - Embeddings: Ollama nomic-embed-text (768-dimensional)
  - Fallbacks: OpenAI embeddings or keyword-based matching
  - Storage: BLOB float32 vectors in SQLite
  - Indexing: Full-text search for candidates + cosine similarity for ranking
  - Thresholds: 0.5 (minimal mode, broad), 0.6 (standard/deep, focused)

- **Performance**
  - Semantic search only runs if within token budget
  - Caching prevents redundant embeddings
  - Top-K limiting (3 minimal, 5 standard, 10 deep)
  - Graceful degradation if models unavailable

## [0.5.5] - 2026-02-10

### Fixed
- **Dashboard Frontend Port Corrected** - Vite config port restored to 3001
  - The vite.config.ts incorrectly had `port: 5173` (Vite's default)
  - Corrected back to `port: 3001` (original, historically documented port)
  - Previous version had correct 3001, was accidentally changed to 5173
  - Start script ishare-elf-system.sh now correctly checks `http://localhost:3001`
  - Verified via git history: commit 00dd570 had `port: 3001`, current had `port: 5173`

### Added
- **Complete Learning Workflow Refactoring** - Major architecture simplification
  - Created 3 new consolidated components replacing 8+ over-engineered files:
    - `core/sentinel.py` (500 lines) - Level 1 Agent (merged Sentinel + Sentinel)
    - `core/learning_processor.py` (700 lines) - All learning + trails centralized
    - `core/event_bridge_v2.py` (300 lines) - Simplified event routing
    - `core/__init__.py` - Core module initialization
  - **72% code reduction**: ~5,300 → ~1,500 lines while preserving 100% functionality

- **New Dashboard Agent Hierarchy Panel** - Visual 3-level monitoring architecture
  - `Open_ELF/dashboard-app/frontend/src/components/monitoring/AgentHierarchyPanel.tsx`
  - Real-time status for each agent level (Sentinel, Orchestrator, CEO)
  - Escalation flow visualization
  - Cycle counts, AI analyses, and escalation metrics per level
  - Clear indicators showing merged Sentinel + Sentinel functionality

- **Archive Script for Deprecated Files** - Clean codebase management
  - `ARCHIVE_DEPRECATED_FILES.sh` - Script to archive old components
  - All deprecated files moved to `archived_components/20260209/`:
    - `agents/sentinel_monitor.py` → archived (merged into Sentinel)
    - `Open_ELF/sentinel/elf_sentinel.py` → archived (replaced by core/sentinel.py)
    - `Open_ELF/orchestrator/event_bridge.py` → archived (replaced by v2)
    - `hooks/learning-loop/*.py` → archived (consolidated into LearningProcessor)
    - `conductor/conductor.py` → archived (trails moved to LearningProcessor)
    - `pattern_response_handler.py` → archived (integrated into LearningProcessor)
  - Deprecation stubs created in original locations (can be removed for clean codebase)

### Changed
- **Escalation Hierarchy Fixed** - Corrected agent-to-agent escalation flow
  - **BEFORE (Incorrect)**: Sentinel → Escalated directly to CEO
  - **AFTER (Correct)**:
    - Sentinel (L1) → Escalates to Orchestrator (L2) on warning/critical
    - Orchestrator (L2) → Escalates to CEO (L3) only on critical
    - CEO (L3) → Handles critical escalations with strategic decisions
  - Updated `core/sentinel.py` escalation logic with proper file format
  - Escalation files now include "Orchestrator Instructions" for autonomous processing

- **Startup Script Updated** - Uses new refactored components
  - `start-elf-system.sh` updated:
    - Event Bridge: Now uses `core/event_bridge_v2.py` instead of old `orchestrator/event_bridge.py`
    - Sentinel: Now uses `core/sentinel.py` (merged Sentinel + Sentinel)
    - Logs show "Sentinel v3.0 (Level 1 Agent)" with merged functionality
    - Sentinel monitor disabled (merged into Sentinel)
  - Fallback support for backward compatibility during transition

- **Documentation Completely Updated** - Clear migration path for users
  - `ARCHITECTURE.md` - Complete rewrite with:
    - New 3-level hierarchy diagram (Sentinel → Orchestrator → CEO)
    - Migration guide from old to new components
    - Troubleshooting section for common issues
    - Quick start guide with usage examples
  - `REFACTORING_SUMMARY.md` - Detailed implementation summary
  - `ARCHIVE_DEPRECATED_FILES.sh` with `MANIFEST.md` for archived files

### Removed
- **Complete File Cleanup** - All old components fully removed from active codebase
  - Deleted deprecation stubs (were keeping empty placeholder files)
  - Only new refactored components remain in `core/` directory
  - Old `hooks/`, `conductor/`, `Open_ELF/sentinel/` directories cleaned
  - Archived files preserved in `archived_components/20260209/` for restoration if needed

### Fixed
- **System Test Verification** - All new components compile and run correctly
  - `./start-elf-system.sh all` successfully starts all services
  - Sentinel v3.0 (Level 1 Agent) running with PID tracking
  - Event Bridge v2.0 running and ready
  - Dashboard Frontend accessible at http://localhost:3001
  - Learning Capture Service active
  - CEO Inbox Monitor processing escalations

## [0.5.4] - 2026-02-09
- **Dashboard Monitoring Alignment** - Complete monitoring system update for post-refactoring alignment
  - Fixed orchestrator port: 9999 → 9998 in dashboard backend (`orchestrator.py`)
  - CEO monitoring router created: 8 new endpoints for CEO inbox, metrics, monitor status
  - Mission monitoring router created: 7 new endpoints for Mission Engine monitoring
  - System services router created: 4 new endpoints replacing outdated agent registry
  - Coordinator system monitoring added: 6 new endpoints for agents, messages, tasks
  - AI analysis monitoring corrected: Now correctly tracks Sentinel + Orchestrator (Sentinel merged)
  - Pheromone trails monitoring added: 2 new endpoints for hotspots and recent entries

- **AI Analysis Configuration (Corrected)** - Sentinel merged into Sentinel
  - **Sentinel** (merged system, replaces old Sentinel + Sentinel): AI analysis every 300s (5min), basic checks every 60s
  - **Unified Orchestrator**: AI analysis every 900s (15min), basic checks every 10s
  - **Removed**: Separate Sentinel monitoring (merged into Sentinel)
  - Note: Old CHANGELOG v0.5.3 incorrectly listed separate Sentinel intervals (this is corrected)

### Added
- **Dashboard Monitoring API Endpoints** - 27 new monitoring endpoints created
  - CEO: `/api/v1/ceo/*` (8 endpoints)
  - Missions: `/api/v1/missions/*` (7 endpoints)
  - System Services: `/api/v1/system/*` (4 endpoints)
  - Coordinator: `/api/v1/monitoring/coordinator/*` (6 endpoints)
  - AI Analysis: `/api/v1/monitoring/ai-analysis/*` (2 endpoints)
  - Pheromone Trails: `/api/v1/monitoring/trails/*` (2 endpoints)

- **Documentation** - `MONITORING_UPDATE_SUMMARY.md` created
  - Complete overview of all monitoring changes
  - API endpoint inventory with testing instructions
  - Frontend integration guide

### Fixed
- **CHANGELOG Inconsistency** - Corrected AI analysis intervals post-Sentinel merge
  - Updated to reflect ARCHITECTURE.md accurate state: Sentinel merged into Sentinel
  - Removed incorrect separate Sentinel schedule references

## [0.5.3] - 2026-02-08 (CORRECTED IN v0.5.4)

### ⚠️ IMPORTANT CORRECTION (Fixed in v0.5.4)
The v0.5.3 entries below contain an error that has been corrected in v0.5.4:
- **AI Analysis Error**: Listed separate Sentinel intervals but Sentinel was already merged into Sentinel in v0.5.3
- **Correct Intervals**: Sentinel (merged) = AI every 5min, basic every 60s | Orchestrator = AI every 15min, basic every 10s
- **Original Incorrect Text**: Listed Sentinel (10min), Sentinel (5min), Orchestrator (15min) as separate systems

### Added
- **Tier-Based AI Analysis System** - Optimized AI usage with configurable timing intervals
  - **Sentinel** (merged system, now handles Sentinel + Sentinel responsibilities): AI analysis every 5 minutes (CORRECTED from 10min), basic checks every 60s
  - **Sentinel**: Merged into Sentinel (no longer separate system)
  - **Unified Orchestrator**: AI analysis every 15 minutes (basic checks every 10s)
  - Added `_analyze_with_ai()` method using AgentManager for deep analysis
  - Added `basic_analysis()` method for non-AI cycle checks
  - Significantly reduces token costs while maintaining system awareness

- **CEO Inbox Monitor** - Autonomous escalation processing agent
  - New `ceo_inbox_monitor.py` script for autonomous CEO escalation handling
  - Checks every 5 minutes for new escalations
  - Uses OpenCode AgentManager to invoke CEO agent for processing
  - Archives processed escalations automatically
  - Start script: `scripts/start-ceo-monitor.sh`
  - Reduces manual intervention for CEO-level decisions

- **Pheromone Trail Recording Hook** - Fixed and re-enabled file tracking
  - Created new `record_trails.py` hook in `~/.opencode/hooks/PostToolUse/`
  - Added `after_apply()` function to `post_tool_learning.py` hook
  - Hooks now properly registered with OpenCode (export `after_apply` function)
  - Tracks Read, edit_file, create_file, Write, Bash, and Grep operations
  - Uses `trail_helper.lay_trails()` for hotspot analysis

### Changed
- **System Startup Script** - Updated `start-elf-system.sh` to launch all services
  - Added startup functions for: Unified Orchestrator, Sentinel (now merged system), CEO Inbox Monitor
  - Fixed orchestrator to use `start` argument
  - All 4 services now start in correct order with proper dependencies

- **Check-in Workflow** - Fixed bugs and improved reliability
  - Fixed wrong path: `src/query/query.py` → `query/query.py`
  - Fixed wrong port: UnifiedOrchestrator 9999 → process detection via pgrep
  - Fixed wrong port: Dashboard Frontend 5173 → 3001
  - Added Sentinel detection (now includes merged Sentinel functionality) in architecture status check
  - Updated to use OpenCode AgentManager instead of nvidia/qwen/qwen3-next-80b-a3b-instruct Task tool

- **Configuration Updates** - Claude configuration files
  - `.opencode/CLAUDE.md`: Removed nvidia/qwen/qwen3-next-80b-a3b-instruct references, added AgentManager integration
  - `.opencode/commands/checkin.md`: Updated session summarization workflow
  - `.opencode/skills/agent-coordination/`: Fixed skill path references

### Fixed
- **Session Summarization** - Fixed workflow for automatic session memory
  - Now uses OpenCode AgentManager with researcher agent
  - Removed deprecated nvidia/qwen/qwen3-next-80b-a3b-instruct Task tool references
  - Properly saves summaries to `memory/sessions/` directory

- **Pheromone Trails Not Recording** - Root cause was missing OpenCode hook registration
  - Previous hooks in `PostToolUse/` were missing `after_apply()` function
  - OpenCode hooks must export `after_apply(tool_name, args, output, session)` to be called
  - Added proper `after_apply()` function to `post_tool_learning.py`
  - Created dedicated `record_trails.py` hook for file tracking
  - Now correctly records to `trails` table on every tool execution

- **Learning Workflow Broken** - Learning extraction was not working since Jan 31st
  - Root cause: `after_apply()` function was missing from hooks, so OpenCode never called them
  - Added `after_apply()` function to `post_tool_learning.py` with full learning extraction
  - Fixed output handling to properly wrap string output in dict format
  - Now correctly extracts `[LEARNED:domain] markers` and creates heuristics
  - Test confirmed: 2 new heuristics created from test markers

- **Logger Consolidation** - Merged duplicate logging modules into single unified system
  - **Before**: Two logging modules existed:
    1. `Open_ELF/agents/elf_logging.py` - File-based logging (83 imports)
    2. `Open_ELF/utils/event_logger.py` - Database event logging (4 imports)
  - **After**: Single unified logging system `Open_ELF/utils/elf_logging.py`
    - All file-based logging functions: `get_logger()`, `log_info()`, `log_warning()`, `log_error()`, `log_critical()`
    - All database event functions: `log_event()`, `log_sentinel_check()`, `log_file_event()`, `log_orchestrator_event()`, `get_recent_events()`
    - Event types dictionary included for consistency
  - Updated all import statements across the codebase
  - Simplified import: `from Open_ELF.utils.elf_logging import get_logger, log_event, ...`
  - `event_logger.py` deleted (functionality merged into elf_logging.py)

## [0.5.2] - 2026-02-07

### Fixed
- **Timeline Panel Showing Only One Event**: Fixed timeline to display all events from database instead of single test event
  - Changed `event_adapter.py` to query SQLite database instead of JSONL files
  - Fixed database query to match actual table schema (removed non-existent `metadata` column)
  - Added `EVENT_TYPE_MAPPING` to convert operational event types (tool_poll, message.updated, etc.) to timeline-friendly types (task_start, task_end, etc.)
  - Frontend added fallback event config for unknown event types
  - Result: Timeline now correctly shows 100 events from 216,459 total database records

- **SentinelStatusPanel React Rendering Error**: Fixed undefined component rendering causing crashes
  - Changed from dynamic icon lookup to safe conditional rendering (lines 507-512)
  - Prevented React error: "Element type is invalid: expected a string but got: object"

- **EventBridge Event Logger Import Path**: Fixed sys.path to correctly locate event_logger module
  - Updated ELFWatchdogMixin to use correct Open_ELF directory path (`~/.opencode/emergent-learning/Open_ELF`)
  - Resolved "No module named 'Open_ELF'" warning

- **Watch Health Endpoints**: Added two new health check endpoints for monitoring
  - `/api/v1/health/mission_bridge` - Returns mission bridge status, hooks_executed counter
  - `/api/v1/health/sentinel_monitor` - Returns sentinel monitor status, events_monitored counter
  - Sentinel now correctly shows "healthy" status for all 3 services

- **Sentinel Log Messages**: Enhanced log summaries with analysis details
  - Changed from generic "Cycle X completed - Status: warning" to include specific analysis
  - Example: "Cycle 43 completed - healthy: Tous les systèmes opérationnels"

### Changed
- **Timeline Event Adapter**: Complete rewrite to use SQLite as single source of truth
  - Previously read from non-existent JSONL files in `/event_chronicle/`
  - Now queries `memory/index.db` event_chronicle table (9 columns: id, timestamp, event_type, source, source_id, status, summary, data, created_at)
  - Event types mapped to 7 core timeline types: task_start, task_end, heuristic_consulted, heuristic_validated, heuristic_violated, failure_recorded, golden_promoted
  - Uses `summary` field for event descriptions instead of formatted descriptions

- **Frontend Event Type Handling**: Added graceful fallback for unknown event types
  - `getEventConfig()` in CosmicTimelineView.tsx now generates labels from event_type strings
  - Auto-capitalizes and formats event types (e.g., "mission_launched" → "Mission Launched")
  - Uses FileText icon and neutral color for unknown event types

### Documentation
- **Updated EventBridge Architecture**: Documented new health check endpoints and hooks_executed counter

## [0.5.1] - 2026-02-07

## [0.5.0] - 2026-01-22

### Fixed
- **Documentation Path Errors** - Corrected `query.py` path in all documentation
  - Path was `query/query.py` but actual location is `src/query/query.py`
  - Fixed in: Migration.md, Architecture.md, Installation.md, IMPROVEMENT_ROADMAP.md, issue-43-analysis.md
  - Users following docs no longer get "file not found" errors
- **Hook Path Errors** - Installers now prefer `src/hooks/` over symlinks
  - Symlinks in `hooks/learning-loop/` may not work reliably with Opencode
  - Both install.sh and install.ps1 updated to use actual files first
- **Golden Rules Not Seeded on Fresh Install** - New users now get golden rules automatically
  - install.sh: Added copy of `templates/golden-rules.md` to `memory/` directory
  - install.sh: Added `seed_golden_rules()` function called in all install modes
  - install.ps1: Added seeding step after database initialization
  - 12 foundational golden rules now populated on first install

## [0.4.4] - 2026-01-16

### Changed
- **Automated /checkout** - No more prompts at session end
  - Auto-detects session activity (commits, files modified, domains)
  - Counts heuristics recorded in last 4 hours
  - Shows summary and exits - no questions asked
  - Philosophy: record learnings during sessions, checkout just summarizes

### Fixed
- **Checkin state expiry** - State now expires after 4 hours
  - New conversations trigger dashboard/model prompts
  - Old state files without timestamps treated as expired
- **Unicode banner restoration** - Better-looking ELF banner with box-drawing chars
  - Added UTF-8 output encoding for Windows compatibility
- **Type hints cleanup** - Fixed Pyright warnings in checkin.py

## [0.4.3] - 2026-01-15

### Added
- **Golden Rules Auto-Sync Infrastructure** - Automatic database synchronization with markdown source
  - `scripts/sync-golden-rules.py` - Manual sync script for golden rules markdown to database
  - `scripts/verify-hooks.py` - Hook verification and auto-installation utility
  - `scripts/install-hooks.py` - Hook template installation from `.hooks-templates/`
  - `.hooks-templates/` - Versioned hook templates for distribution and auto-install
  - `.hooks-templates/PostToolUse/sync-golden-rules.py` - Post-tool hook for auto-sync
  - `.hooks-templates/README.md` - Hook development and troubleshooting documentation
- **Hook Auto-Installation for New Users** - Seamless hook setup during first install
  - Hooks automatically installed from templates during setup
  - `/checkin` command verifies hooks are present and auto-installs if missing
  - Zero manual configuration needed for new users
- **Checkin Integration** - Hook verification integrated into checkin workflow
  - Added `verify_hooks()` method as Step 1b in checkin process
  - Auto-installs missing hooks with [OK] status message
  - Safety net ensures framework hooks always present

### Fixed
- **Golden Rules Synchronization Lag** - Markdown and database now stay in sync
  - Previously markdown had 30 golden rules but database had stale count (55)
  - Post-tool hook now detects changes and syncs automatically
  - Database is updated after each tool execution if markdown changed

## [0.3.12] - 2026-01-05

### Added
- **Game Leaderboard** - Full leaderboard system for the space shooter game
  - `GET /api/game/leaderboard` - Top N scores with pagination and user info
  - `GET /api/game/leaderboard/around-me` - Scores centered on current user
  - React `Leaderboard.tsx` component with sci-fi styling
  - Crown/Medal icons for top 3, user highlighting, loading states
  - Anti-cheat filtering with configurable MAX_VALID_SCORE
  - Performance index `idx_game_state_score_desc` for fast queries
- **Comprehensive API Reference** - Complete documentation for all public APIs
  - `docs/api/index.md` - API overview and quick start guide
  - `docs/api/QuerySystem.md` - All 30+ async query methods with examples
  - `docs/api/Models.md` - Documentation for all 22 database models
  - `docs/api/Hooks.md` - Hook development guide with 28 security patterns
  - `docs/api/Conductor.md` - Workflow orchestration and swarm coordination
- **Database Schema Documentation** - `docs/database/schema.md` with 50+ tables, ERD, and migration notes
- **Developer Guides**
  - `docs/guides/testing.md` - Test organization, fixtures, coverage requirements
  - `docs/guides/performance.md` - Query optimization, indexing, token cost analysis
  - `docs/guides/extensions.md` - Custom hooks, mixins, personas, dashboard plugins
- **CONTRIBUTING.md** - Developer onboarding, code style guide, PR workflow
- **Test Infrastructure** - Test files for critical bugs (WebSocket stress, auto-capture rollback, broadcast race)

### Fixed
- **SQL Injection Vulnerability** - Added whitelist-based validation in `main.py`
  - `ALLOWED_TABLE_CONFIGS` dictionary with valid tables, columns, and order_by fields
  - `_validate_query_params()` function with O(1) frozenset lookups
  - Blocks all SQL injection attempts in dynamic query building
- **Path Traversal Vulnerability** - Hardened `admin.py` file access
  - `_is_path_allowed()` validates paths against allowed directories
  - Symlink resolution with `strict=True` for security
  - Defense-in-depth for `/ceo-inbox/{filename}` endpoint
- **Python 3.14 Test Compatibility** - Fixed `test_auto_capture_rollback.py`
  - Added `@contextmanager` decorator to mock context functions
  - Removed monkey-patching of read-only sqlite3 attributes
  - Added `gc.collect()` retry loop for Windows file locking in `conftest.py`

### Changed
- **Documentation Organization** - Moved analysis docs to `docs/analysis/`
  - CRITICAL_BUGS_QUICKREF.md, DEBUG_ANALYSIS_REPORT.md
  - DOCUMENTATION_ARCHITECTURE_ANALYSIS.md, TEST_SUMMARY.md
- **Gitignore** - Added `**/rembg_env/` pattern for Python virtual environments

## [0.3.11] - 2026-01-05

### Fixed
- **Exponential Backoff in Auto-Capture** - Added backoff (2^n up to 300s) on consecutive errors to prevent tight error loops
- **Session ID Validation** - UUID format validation before subprocess calls in summarizer
- **Fraud Detector Error Propagation** - `_store_fraud_report` now returns bool; response actions only execute on successful storage
- **Thread-Safe Session Index** - Added `threading.RLock` protecting `_index` across all methods (scan, list, get)
- **Timeline Event Type Validation** - Validate `event_type` against enum before TypeScript cast
- **Subprocess Timeout Handling** - Explicit `TimeoutExpired` handling with specific error messages in summarizers
- **Session Corruption Tracking** - New `is_partial` and `corruption_count` fields in `SessionMetadata` for JSON parse errors
- **SQLite JSON Queries** - Replaced fragile `LIKE '%"outcome": "unknown"%'` with `json_extract(output_json, '$.outcome')`
- **Editor Error Toast** - Show notification when "open in editor" fails instead of silent failure

## [0.3.10] - 2026-01-05

### Added
- **Heuristic Validation Tracking** - New `scripts/validate-heuristic.py` script
  - Track when heuristics are validated (worked) or violated (failed)
  - `--validate` / `--violate` flags to record outcomes
  - `--recalc` to adjust confidence based on validation ratio
  - `--list` to view all heuristics with validation stats

### Fixed
- **Unicode Encoding Error (Windows)** - Added `encoding='utf-8'` to file operations in `record-heuristic.py`
- **Package Manager Fallback** - `start.ps1` now detects bun first, falls back to npm if unavailable
- **Windows Rollup Dependency** - Added platform-specific Rollup binaries to `optionalDependencies` in frontend `package.json`

## [0.3.9] - 2026-01-04

### Changed
- **Swarm Skill** - Complete rewrite with full agent pool (~100+ specialized agents)
  - Replaced 4-agent pattern (Researcher/Architect/Creative/Skeptic) with domain-based selection
  - Added `ultrathink` mode: 15-25 agents for maximum depth analysis
  - Added `focused` mode: 4-8 agents for targeted domain analysis
  - Added `quick` mode: 2-4 agents for fast surveys
  - Domain-to-agent mapping table (Python, TypeScript, Security, Databases, etc.)
  - Async-first execution rules documented
  - Anti-patterns section to prevent common mistakes

## [0.3.2] - 2025-12-28

### Fixed
- **Checkin Skill** - Use Python for session summarization to avoid MSYS bash escaping issues
  - Added database health check display
  - Added last session summary display
  - ELF banner and dashboard prompt on first checkin

## [0.3.1] - 2025-12-25

### Fixed
- **Windows Installer** - Fixed PowerShell Join-Path syntax errors for new users
  - Join-Path now correctly uses 2 parameters instead of 3
  - Fixed venv Python path, pip path, and hook path resolution
  - Database validation now uses venv Python with all dependencies
- **Python Script Installation** - Installer now copies all 21 Python scripts from tools/scripts/
  - Fixes pre-commit hook failures (check-invariants.py missing)
  - Ensures recording scripts (record-heuristic.py, etc.) are available
- **Sentinel Module Installation** - Tiered sentinel system now properly installed
  - src/sentinel/ copied to ~/.opencode/emergent-learning/sentinel/
  - start-sentinel.sh updated to use correct installed paths
  - Fixes "launcher.py not found" error when starting sentinel

## [0.2.0] - 2025-12-16

### Added
- **Async Query Engine** - Complete migration to async architecture using peewee-aio
- **ELF MCP Server** - Native MCP integration for opencode-flow
- **Step-file Workflows** - Resumable task architecture with frontmatter state
- **Party Definitions** - Agent team compositions for complex tasks
- **Golden Rule Categories** - Filter rules by domain/category
- **Customization Layer** - User-specific config overrides
- **Update System** - Simple update.sh/update.ps1 with database migrations

### Changed
- Cosmic view now default (persisted to localStorage)
- Modular query system architecture (Phase 1-6 refactor)
- Zustand store with persistence middleware

### Fixed
- Windows compatibility (ASCII-only CLI output)
- Clean exit when dashboard servers already running
- Workflow engine import handling
- Hook directory structure

## [0.1.2] - 2025-12-14

### Added
- Dashboard UI overhaul with cosmic theme
- Learning pipeline automation
- File operations tracking for hotspot analysis

## [0.1.1] - 2025-12-13

### Added
- Initial dashboard application
- Golden rules and heuristics system
- CEO escalation workflow

## [0.1.0] - 2025-12-12

### Added
- Initial release
- Core ELF framework
- Installation scripts
- Basic query system

---

## Versioning Policy

- **Major (X.0.0)**: Breaking changes to database schema or configuration
- **Minor (0.X.0)**: New features, backward-compatible
- **Patch (0.0.X)**: Bug fixes, documentation updates
