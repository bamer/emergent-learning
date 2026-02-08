# Changelog

All notable changes to the Emergent Learning Framework will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.3] - 2026-02-08

### Added
- **Tier-Based AI Analysis System** - Optimized AI usage with configurable timing intervals
  - **Watcher**: AI analysis every 10 minutes (basic checks every 60s)
  - **Sentinel**: AI analysis every 5 minutes (basic checks every 30s)
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
  - Added startup functions for: Unified Orchestrator, Sentinel Monitor, CEO Inbox Monitor
  - Fixed orchestrator to use `start` argument
  - All 6 services now start in correct order with proper dependencies

- **Check-in Workflow** - Fixed bugs and improved reliability
  - Fixed wrong path: `src/query/query.py` → `query/query.py`
  - Fixed wrong port: UnifiedOrchestrator 9999 → process detection via pgrep
  - Fixed wrong port: Dashboard Frontend 5173 → 3001
  - Added Sentinel detection in architecture status check
  - Updated to use OpenCode AgentManager instead of haiku Task tool

- **Configuration Updates** - Claude configuration files
  - `.claude/CLAUDE.md`: Removed haiku references, added AgentManager integration
  - `.opencode/commands/checkin.md`: Updated session summarization workflow
  - `.opencode/skills/agent-coordination/`: Fixed skill path references

### Fixed
- **Session Summarization** - Fixed workflow for automatic session memory
  - Now uses OpenCode AgentManager with researcher agent
  - Removed deprecated haiku Task tool references
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
    - All database event functions: `log_event()`, `log_watcher_check()`, `log_file_event()`, `log_orchestrator_event()`, `get_recent_events()`
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

- **WatcherStatusPanel React Rendering Error**: Fixed undefined component rendering causing crashes
  - Changed from dynamic icon lookup to safe conditional rendering (lines 507-512)
  - Prevented React error: "Element type is invalid: expected a string but got: object"

- **EventBridge Event Logger Import Path**: Fixed sys.path to correctly locate event_logger module
  - Updated ELFWatchdogMixin to use correct Open_ELF directory path (`~/.opencode/emergent-learning/Open_ELF`)
  - Resolved "No module named 'Open_ELF'" warning

- **Watch Health Endpoints**: Added two new health check endpoints for monitoring
  - `/api/v1/health/mission_bridge` - Returns mission bridge status, hooks_executed counter
  - `/api/v1/health/sentinel_monitor` - Returns sentinel monitor status, events_monitored counter
  - Watcher now correctly shows "healthy" status for all 3 services

- **Watcher Log Messages**: Enhanced log summaries with analysis details
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
- **Watcher Module Installation** - Tiered watcher system now properly installed
  - src/watcher/ copied to ~/.opencode/emergent-learning/watcher/
  - start-watcher.sh updated to use correct installed paths
  - Fixes "launcher.py not found" error when starting watcher

## [0.2.0] - 2025-12-16

### Added
- **Async Query Engine** - Complete migration to async architecture using peewee-aio
- **ELF MCP Server** - Native MCP integration for claude-flow
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
