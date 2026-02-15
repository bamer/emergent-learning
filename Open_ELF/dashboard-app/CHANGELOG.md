# ELF Dashboard Changelog

All notable changes to the ELF Dashboard will be documented in this file.

## [2026-02-16] - Task Management UX Improvements

### Added
- **Task Detail Modal** (TaskDetailModal.tsx)
  - Full mission details view with description, active state, logs, and output/error display
  - Restart button for blocked and error tasks
  - Escalate to Orchestrator button for blocked tasks
  - Archive button to remove completed/failed/error tasks from kanban
  - Clean slide-in modal design with proper z-index handling (z-[9999])

- **TaskKanban Enhancements**
  - Renamed "Stop" button to "Cancel" for clarity
  - Added View Details (eye icon) button for completed, failed, and error tasks
  - Added support for XCircle, failed, and error statuses
  - Integrated TaskDetailModal with proper state management
  - Added handlers: handleEscalate, handleArchive, handleRestart

### Changed
- **Task Detail Modal Layout** - Changed from fixed 800px slide-in panel to centered modal with max-width 5120px (better use of screen space)
- **Archive Button Visibility** - Added Archive button to TaskCard for quick access without opening detail modal
- **Task Filtering** - Archived tasks are now automatically filtered out from dashboard display

### Fixed
- **Task Detail Modal** (TaskDetailModal.tsx)
  - Full mission details view with description, active state, logs, and output/error display
  - Restart button for blocked and error tasks
  - Escalate to Orchestrator button for blocked tasks
  - Archive button to remove completed/failed/error tasks from kanban
  - Clean slide-in modal design with proper z-index handling (z-[9999])

- **TaskKanban Enhancements**
  - Renamed "Stop" button to "Cancel" for clarity
  - Added View Details (eye icon) button for completed, failed, and error tasks
  - Added support for XCircle, failed, and error statuses
  - Integrated TaskDetailModal with proper state management
  - Added handlers: handleEscalate, handleArchive, handleRestart

### Fixed
- **Daemon Syntax Errors**
  - Fixed 3 corrupted lines in `semantic/daemon.py` where `cursor\1` was replaced with `cursor.fetchall()`
  - Lines affected: 172, 340, 418

- **Agent Discovery**
  - Added `plugins/` to DEFAULT_AGENTS_DIRS in `agent_manager.py`
  - Changed glob pattern to recursive (`**/*.md`) to discover agents in subdirectories

- **Session Indexing**
  - Created `sessions-index.json` for elf_missions session metadata
  - Dashboard now properly indexes and displays ELF Swarm missions

### Modified Files
- `/home/bamer/.opencode/emergent-learning/Open_ELF/agents/agent_manager.py` - Plugin discovery
- `/home/bamer/.opencode/emergent-learning/Open_ELF/semantic/daemon.py` - Syntax fixes
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/frontend/src/components/live/TaskKanban.tsx` - UX improvements
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/frontend/src/components/live/LivePanel.tsx` - Handler propagation

### Created Files
- `/home/bamer/.opencode/projects/elf_missions/sessions-index.json` - Session metadata
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/frontend/src/components/live/TaskDetailModal.tsx` - Modal component
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/CHANGELOG.md` - This changelog

### Documentation Updates
- Recorded heuristics:
  - Always use proper modal component for detailed views rather than expanding cards (dashboard domain)
  - Never merge large file modifications in single write operations (dashboard domain)

### Known Issues
- Duplicate key "sentinel" warning in AgentsPanel.tsx (non-critical)

---

## [2026-02-12] - Initial Dashboard

### Added
- Live Panel with real-time task monitoring
- Task Kanban view with drag-and-drop capability
- Trail Feed for signal propagation
- Agent status tracking
- Mission creation modal

### Features
- Real-time SSE (Server-Sent Events) for live updates
- Multi-session task management
- Signal input for sending notes and changing status
- Sentinel monitoring and control
