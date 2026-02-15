# Task Management Enhancement - 2026-02-16

## Overview

Enhanced the ELF Dashboard's task management capabilities with improved controls for viewing details, restarting blocked tasks, escalating issues, and archiving completed tasks.

## Changes Made

### 1. Task Detail Modal (New Component) - Updated Layout

**File:** `frontend/src/components/live/TaskDetailModal.tsx`

A comprehensive modal component for viewing detailed mission information:

**Layout Update (Fixed):**
- Changed from fixed 800px slide-in panel to **centered modal** with max-width 5120px
- Modal now uses full screen width properly with centered positioning
- Better responsive design that adapts to different screen sizes
- Rounded corners and border for polished appearance

**Features:**
- Full mission description and active state display
- Execution log timeline with chronological notes
- Output/error display with syntax highlighting (monospace font)
- Blocked-by and blocking dependencies visualization
- Action buttons:
  - **Restart** - Relaunch blocked or error tasks
  - **Escalate to Orchestrator** - Request orchestrator analysis for blocked tasks
  - **Archive from Kanban** - Remove completed/failed/error tasks from the kanban view

**UI Design:**
- Centered modal with max-w-5xl constraint
- High z-index (9999) to appear above everything
- Scrollable content area with sticky header/footer
- Status-specific color coding (emerald for completed, amber for blocked, red for failed)
- Responsive button states based on task status

**File:** `frontend/src/components/live/TaskDetailModal.tsx`

A comprehensive modal component for viewing detailed mission information:

**Features:**
- Full mission description and active state display
- Execution log timeline with chronological notes
- Output/error display with syntax highlighting (monospace font)
- Blocked-by and blocking dependencies visualization
- Action buttons:
  - **Restart** - Relaunch blocked or error tasks
  - **Escalate to Orchestrator** - Request orchestrator analysis for blocked tasks
  - **Archive from Kanban** - Remove completed/failed/error tasks from the kanban view

**UI Design:**
- Slide-in from right panel (800px width)
- High z-index (9999) to appear above everything
- Scrollable content area with sticky header/footer
- Status-specific color coding (emerald for completed, amber for blocked, red for failed)
- Responsive button states based on task status

### 2. TaskKanban Improvements

**File:** `frontend/src/components/live/TaskKanban.tsx`

**Changes:**
- Renamed "Stop" button → "Cancel" for clarity
- Added **Archive** button to TaskCard for quick access (no need to open detail modal first)
  - Visible for completed, failed, error, and cancelled tasks
  - Uses Archive icon with same styling as other action buttons
- Added View Details (eye icon) button for completed, failed, and error tasks
- Added support for XCircle, failed, and error statuses
- Integrated TaskDetailModal with proper state management:
  - `selectedTaskForDetails` state controls modal visibility
  - `handleDetailsClick` opens modal for selected task
  - `handleArchiveFromCard` allows quick archiving without modal
  - `handleEscalate`, `handleArchive`, `handleRestart` propagate modal actions
- Updated TypeScript interfaces to include:
  - `archived?: boolean` - Flag to filter archived tasks
  - `archived_at?: string` - Timestamp of archiving

**Component Flow:**
```
LivePanel (handlers: onEscalate, onArchive, onRestart)
    ↓ (props)
TaskKanban (state: selectedTaskForDetails, handlers: handleEscalate/Archive/Restart)
    ↓ (onDetailsClick, onArchiveClick)
TaskCard (Archive, Details buttons)
    ↓
TaskDetailModal (shows detailed view)
```

**File:** `frontend/src/components/live/TaskKanban.tsx`

**Changes:**
- Renamed "Stop" button → "Cancel" for clarity
- Added **View Details** (eye icon) button for completed, failed, and error tasks
- Added support for `XCircle`, `failed`, and `error` statuses
- Integrated TaskDetailModal with proper state management:
  - `selectedTaskForDetails` state controls modal visibility
  - `handleDetailsClick` opens modal for selected task
  - `handleEscalate`, `handleArchive`, `handleRestart` propagate actions
- Updated TypeScript interfaces to include new handler props

**Component Flow:**
```
LivePanel (handlers: onEscalate, onArchive, onRestart)
    ↓ (props)
TaskKanban (state: selectedTaskForDetails, handlers: handleEscalate/Archive/Restart)
    ↓ (onDetailsClick)
TaskCard (Details button → handleDetailsClick)
    ↓
TaskDetailModal (shows detailed view)
```

### 3. LivePanel Handler Integration (Updated)

**File:** `frontend/src/components/live/LivePanel.tsx`

**Enhanced:**
- Added **archive filtering** in SSE message handler
  - When receiving task updates, filters out tasks with `archived: true`
  - Tasks are immediately removed from kanban after archiving
  - Uses `TaskSessions` type with filtering loop

**Existing Handlers:**
- `handleEscalateToOrchestrator(taskId)` - Finds task in all sessions, calls `/api/v1/live/task/{sessionId}/{taskId}/escalate`
- `handleArchiveTask(taskId)` - Finds task, calls `/api/v1/live/task/{sessionId}/{taskId}/archive`
- `handleRestartTask(taskId)` - Finds task, calls relaunch endpoint (restart = relaunch for blocked/error tasks)

**Implementation Notes:**
- All handlers use `useCallback` with proper dependencies
- Helper function to find task across all sessions
- Error handling with console logging
- Cleanup: closes modal after action completes

**Archive Filtering:**
```typescript
if (data.type === 'initial' || data.type === 'update') {
  // Filter out archived tasks from the display
  const filteredSessions: TaskSessions = {}
  for (const [sessionId, tasks] of Object.entries(data.sessions || {})) {
    filteredSessions[sessionId] = tasks.filter((task: Task) => !task.archived)
  }
  setTaskSessions(filteredSessions)
}
```

**File:** `frontend/src/components/live/LivePanel.tsx`

**New Handlers:**
- `handleEscalateToOrchestrator(taskId)` - Finds task in all sessions, calls `/api/v1/live/task/{sessionId}/{taskId}/escalate`
- `handleArchiveTask(taskId)` - Finds task, calls `/api/v1/live/task/{sessionId}/{taskId}/archive`
- `handleRestartTask(taskId)` - Finds task, calls relaunch endpoint (restart = relaunch for blocked/error tasks)

**Implementation Notes:**
- All handlers use `useCallback` with proper dependencies
- Helper function to find task across all sessions
- Error handling with console logging
- Cleanup: closes modal after action completes

### 4. Daemon Syntax Fixes

**File:** `semantic/daemon.py`

Fixed 3 syntax errors where `cursor\1` was corrupted instead of `cursor.fetchall()`:
- Line 172 - In vector search results handling
- Line 340 - In metadata query results
- Line 418 - In embedding query results

### 5. Agent Discovery Enhancement

**File:** `agents/agent_manager.py`

**Changes:**
- Added `plugins/` to `DEFAULT_AGENTS_DIRS`
- Changed glob pattern from non-recursive (`*.md`) to recursive (`**/*.md`)
- Now discovers agents in subdirectories like `plugins/python-development/agents/`

### 6. Session Indexing

**Created:** `projects/elf_missions/sessions-index.json`

Session metadata file enabling dashboard to index ELF Swarm missions:
- Contains session IDs, names, creation dates
- Enables proper display in Live Panel → Tasks and Trails kanban
- Maps session IDs to user-friendly names

## API Endpoints (Expected)

These endpoints should exist in the backend for full functionality:

```python
POST /api/v1/live/task/{session_id}/{task_id}/escalate
POST /api/v1/live/task/{session_id}/{task_id}/archive
POST /api/v1/live/task/{session_id}/{task_id}/relaunch  # Already exists
```

**Note:** If these endpoints don't exist yet, they need to be created in `backend/routers/live.py`.

## Testing Checklist

- [ ] Verify TaskDetailModal opens correctly for completed tasks
- [ ] Verify TaskDetailModal opens correctly for failed tasks
- [ ] Verify TaskDetailModal opens correctly for error tasks
- [ ] Test Restart button on blocked tasks
- [ ] Test Restart button on error tasks
- [ ] Test Escalate button on blocked tasks
- [ ] Test Archive button on completed tasks
- [ ] Test Archive button on failed tasks
- [ ] Test Archive button on error tasks
- [ ] Verify modal closes after action completes
- [ ] Verify archived tasks are removed from kanban
- [ ] Verify semantic search daemon runs without errors
- [ ] Verify ELF Swarm missions appear in dashboard
- [ ] Verify agent discovery includes plugins/ subdirectories

## Known Issues

1. **Duplicate key warning**: `AgentsPanel.tsx` has duplicate "sentinel" key (line 60-62). Non-critical, doesn't affect functionality.

2. **Backend endpoints**: Escalate and Archive endpoints may not exist yet in backend.

## Future Enhancements

1. [ ] Add enhanced prompts to MissionModal.tsx (10 categories, 20+ prompts each) - needs incremental addition to avoid file corruption
2. [ ] Implement backend API endpoints for escalate and archive
3. [ ] Add filtering/sorting options in TaskDetailModal
4. [ ] Add export functionality for task details
5. [ ] Fix duplicate key warning in AgentsPanel.tsx

## Heuristics Recorded

1. **Dashboard Domain (Success)**: Always use proper modal component for detailed views rather than expanding cards in kanban
2. **Dashboard Domain (Failure)**: Never merge large file modifications in single write operations
3. **Dashboard Domain (Success)**: Use recursive glob patterns for discovering resources in subdirectories

## Technical Notes

### Modal z-index Handling
TaskDetailModal uses `z-[9999]` to ensure it appears above all other elements, including the 3D scene and other modals.

### State Management Pattern
```
Parent (LivePanel) - Defines handler logic
    ↓ (pass handlers)
Child (TaskKanban) - Adds state for modal, forwards handlers
    ↓ (pass handlers + state)
Grandchild (TaskDetailModal) - Receives task and handlers, emits callbacks
```

### Type Safety
All interfaces properly extended to include new handler types:
```typescript
interface TaskKanbanProps {
  // ...
  onEscalate?: (taskId: string) => void
  onArchive?: (taskId: string) => void
  onRestart?: (taskId: string) => void
}
```

Related Files:
- `/home/bamer/.opencode/emergent-learning/Open_ELF/dashboard-app/CHANGELOG.md`
- `/home/bamer/.opencode/emergent-learning/memory/heuristics/dashboard.md`
