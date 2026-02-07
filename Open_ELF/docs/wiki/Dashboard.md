# Dashboard Guide

## Starting the Dashboard

**On Checkin:** Claude prompts "Start Dashboard? [Y/n]" at conversation start.

**Manual Start:**
```bash
cd ~/.opencode/emergent-learning/dashboard-app
./run-dashboard.ps1  # Windows PowerShell
./run-dashboard.sh   # Mac/Linux/Git Bash
```

Open http://localhost:3001

## Dashboard Tabs

| Tab | What It Shows |
|-----|---------------|
| **Overview** | Hotspot treemap (D3.js), anomalies, golden rules |
| **Heuristics** | All patterns with confidence, promote/demote |
| **Runs** | Agent execution history, retry failed runs |
| **Timeline** | Event-by-event history with playback (200,000+ events from database) |
| **Sessions** | Browse Opencode session history - search, filter, expand conversations |
| **Query** | Natural language search |

## Sessions Tab

The Sessions tab lets you browse your Opencode session history without consuming tokens:

**Features:**
- **Search** - Filter sessions by prompt text
- **Project Filter** - Dropdown to focus on specific projects
- **Date Range** - Today, Last 7 days, Last 30 days, or All time
- **Expandable Cards** - Click any session to see the full conversation
- **User/Assistant Messages** - Clear visual distinction between prompts and responses
- **Tool Usage** - See what tools Claude used (Read, Edit, Bash, etc.)

**Data Source:** Reads from `~/.opencode/projects/*/*.jsonl` files directly.

**API Endpoints:**
- `GET /api/sessions` - List sessions with pagination/filtering
- `GET /api/sessions/{id}` - Load full session content
- `GET /api/projects` - List projects with session counts
- `GET /api/sessions/stats` - Session statistics

## Timeline Tab

The Timeline tab displays a chronological stream of system events from the EL Event Chronicle:

**Features:**
- **Live Updates**: Shows latest events from the database (200,000+ events total)
- **Event Types**: Displays mapped event types with proper icons and colors
  - Task Started/Completed (tool usage, agent lifecycle)
  - Heuristic Consulted/Validated/Violated
  - Failure Recorded, Golden Promotion
- **Filtering**: Filter by event type (Mission Launched, Mission Complete, Neural Sync, etc.)
- **Playback Controls**: Adjust playback speed (0.5x, 1x, 2x, 5x)
- **Time Navigation**: Browse events chronologically with timestamps

**Data Source:** Queries `memory/index.db` event_chronicle table directly (9 columns: id, timestamp, event_type, source, source_id, status, summary, data, created_at)

**Event Type Mapping:** Operational events are converted to timeline-friendly types:
- `tool_poll`, `message.updated`, `watcher_check` → task_start
- `agent_started`, `agent_stopped` → task_start/task_end
- `heuristic_created` → heuristic_consulted
- `session.idle`, `session.status` → task_end
- `server.heartbeat` → task_start

**API Endpoints:**
- `GET /api/v1/timeline/events` - List timeline events with pagination/filtering
- `GET /api/v1/timeline/stats` - Timeline statistics
- `GET /api/v1/timeline/event-types` - Available event types
- `GET /api/v1/timeline/recent` - Recent events

## Stats Bar

The top bar shows real-time metrics:

- **Total Runs** - Click to see history
- **Success Rate** - Percentage of successful runs
- **Heuristics** - Total patterns learned
- **Golden Rules** - Constitutional principles
- **Hotspots** - High-activity code locations
- **Queries** - Building queries made

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Backend:** FastAPI (Python) with WebSocket updates
- **Visualization:** D3.js for treemaps
- **Database:** Reads from `~/.opencode/emergent-learning/memory/index.db`
- **Themes:** 10 cosmic themes (black-hole, nebula, aurora, etc.)

The dashboard operates **without consuming API tokens** - it reads directly from your local SQLite database.
