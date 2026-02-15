# Emergent Learning Dashboard

An interactive real-time dashboard for monitoring and managing your Claude Code learning system.

## Features

- **Real-time Updates** - WebSocket-powered live data streaming
- **Interactive Treemap** - D3.js visualization of code hotspots
- **Heuristic Lifecycle** - Track rules from learning to golden status
- **Timeline Replay** - Step through agent activity history
- **One-Click Actions** - Promote, retry, and open in editor
- **Natural Language Query** - Ask questions about your data
- **Visual Workflow Builder** - Create automation rules
- **Anomaly Detection** - Get alerts for unusual patterns
- **Task Management** - Live task kanban with detailed views (NEW)
- **Task Actions** - Start, cancel, restart, escalate, and archive tasks (NEW)

## Quick Start

```powershell
# Run from the dashboard-app directory
./start.ps1
```

Or manually:

```powershell
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8888

# Terminal 2 - Frontend
cd frontend
bun install
bun run dev
```

## URLs

- **Dashboard**: http://localhost:3001
- **API v1**: http://localhost:8888/api/v1
- **API Docs**: http://localhost:8888/docs

## Architecture

```
dashboard-app/
├── backend/              # FastAPI server
│   ├── main.py          # API endpoints + WebSocket
│   └── requirements.txt
├── frontend/            # React + Vite app
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── hooks/       # React hooks
│   │   └── types.ts     # TypeScript types
│   └── package.json
├── start.ps1           # Startup script
└── README.md
```

## API Endpoints

### Stats & Data
- `GET /api/v1/stats` - System statistics
- `GET /api/v1/heuristics` - All heuristics
- `GET /api/v1/hotspots` - Code hotspots
- `GET /api/v1/runs` - Agent runs
- `GET /api/v1/timeline` - Event timeline
- `GET /api/v1/anomalies` - Detected anomalies
- `POST /api/v1/heuristics/{id}/promote` - Promote to golden
- `POST /api/v1/heuristics/{id}/demote` - Demote from golden
- `POST /api/v1/runs/{id}/retry` - Retry failed run
- `POST /api/v1/actions/open-editor` - Open file in VS Code
- `POST /api/v1/query` - Natural language query

### Live System (SSE)
- `GET /api/v1/live/tasks` - SSE stream for task updates
- `GET /api/v1/live/trails` - SSE stream for trail updates
- `GET /api/v1/live/sessions` - All sessions

### Task Management
- `POST /api/v1/live/task/{session_id}/{task_id}/start` - Start a pending/blocked task
- `POST /api/v1/live/task/{session_id}/{task_id}/stop` - Stop/cancel an in-progress task
- `POST /api/v1/live/task/{session_id}/{task_id}/relaunch` - Relaunch a completed/failed task
- `POST /api/v1/live/task/{session_id}/{task_id}/status` - Change task status
- `POST /api/v1/live/task/{session_id}/{task_id}/escalate` - Escalate blocked task to orchestrator (NEW)
- `POST /api/v1/live/task/{session_id}/{task_id}/archive` - Archive completed/failed task from kanban (NEW)
- `POST /api/v1/live/signal` - Send note to task

### WebSocket
- `WS /ws` - Real-time updates

## Components

### Live Panel (NEW)
Real-time task monitoring and management:
- **Task Kanban** - Visual task board with PENDING, IN PROGRESS, FAILED, COMPLETED columns
- **Task Detail Modal** - Full mission details with logs, output, dependencies, and actions
- **Task Actions**:
  - Start - Begin pending or blocked tasks
  - Cancel - Stop in-progress tasks
  - Restart - Retry blocked or error tasks
  - Escalate - Send blocked tasks to orchestrator for analysis
  - Archive - Hide completed/failed tasks from kanban (keeps in storage)
- **Trail Feed** - Live signal propagation stream
- **Agents Panel** - ELF swarm agent status
- **Mission Modal** - Create new missions with pre-built prompts

### Overview Tab
- Stats bar with key metrics
- Interactive hotspot treemap
- Anomaly alerts
- Golden rules summary

### Heuristics Tab
- Searchable/filterable list
- Lifecycle visualization
- One-click promote/demote
- Confidence tracking

### Runs Tab
- Agent execution history
- Status filtering
- File touchpoints
- Retry failed runs

### Timeline Tab
- Event-by-event history
- Playback controls
- Event type filtering
- Related context

### Query Tab
- Natural language interface
- Smart result rendering
- Query suggestions
- Search history

## License

MIT
