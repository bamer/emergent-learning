# Timeline Dashboard Integration Guide

## Overview

This guide provides step-by-step instructions for integrating the Event Chronicle system with the dashboard to display individual events in the timeline view instead of aggregated data.

## Directory Structure

```
Open_ELF/
└── timeline_dashboard/
    ├── __init__.py
    ├── README.md
    ├── timeline_events.py      # Event type definitions
    ├── event_adapter.py        # Chronicle ↔ Dashboard conversion
    ├── timeline_api.py         # FastAPI endpoints
    ├── demo_integration.py     # Integration example
    ├── test_integration.py     # Test suite
    └── frontend_integration.md # Frontend update guide
```

## Backend Integration

### 1. Add Integration to Main Application

In `dashboard-app/backend/main.py`, add the following:

```python
# Add this import near the top with other imports
from Open_ELF.timeline_dashboard.demo_integration import integrate_with_dashboard

# In the startup_event function, add this line after other initialization:
integrate_with_dashboard(app)
```

### 2. New API Endpoints

After integration, these endpoints will be available:

- `GET /api/v1/timeline/events` - Get individual timeline events
- `GET /api/v1/timeline/stats` - Get chronicle statistics
- `GET /api/v1/timeline/recent` - Get recent events
- `GET /api/v1/timeline/event-types` - Get available event types

### 3. Event Format

Events returned by `/api/v1/timeline/events` will have this format:

```json
{
  "status": "ok",
  "events": [
    {
      "id": "uuid-string",
      "timestamp": "2026-02-02T10:30:00Z",
      "event_type": "heuristic_validated",
      "description": "Heuristic validated: Always validate inputs at system boundaries",
      "metadata": {
        "user_id": "test-user",
        "session_id": "session-123"
      },
      "source": "record-heuristic.sh",
      "domain": "testing"
    }
  ],
  "count": 1
}
```

## Supported Event Types

The integration supports these event types with proper icons and colors:

- `task_start` - Task Started
- `task_end` - Task Completed
- `heuristic_consulted` - Heuristic Consulted
- `heuristic_validated` - Heuristic Validated
- `heuristic_violated` - Heuristic Violated
- `failure_recorded` - Failure Recorded
- `golden_promoted` - Golden Promotion
- `agent_spawned` - Agent Spawned
- `workflow_started` - Workflow Started
- `session_started` - Session Started
- `session_ended` - Session Ended

### Event Type Mapping

Operational event types from the database are mapped to timeline-friendly types:
- `agent_started`, `agent_stopped` → `task_start`, `task_end`
- `heuristic_created` → `heuristic_consulted`
- `tool_poll`, `message.updated`, `watcher_check` → `task_start`
- `session.idle`, `session.status` → `task_end`
- `server.heartbeat` → `task_start`
- All unknown types → `task_start` with auto-generated label

The `original_event_type` field is preserved for reference and debugging.

## Frontend Integration

### 1. Update Data Hooks

Modify `useDashboardData.ts` to fetch individual events:

```typescript
// Replace timeline state
const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);

// Update loadData function
const loadData = useCallback(async () => {
  try {
    const [eventsData] = await Promise.all([
      api.get('/api/v1/timeline/events?limit=100').catch(() => []),
    ]);
    setTimelineEvents(eventsData?.events || []);
  } catch (err) {
    console.error('Failed to load timeline events:', err);
  }
}, [api]);
```

### 2. Update TimelineView Component

Update the TimelineView to work with individual events:

```typescript
interface TimelineViewProps {
  events: TimelineEvent[];  // Individual events instead of aggregated data
  heuristics: Heuristic[];
  onEventClick: (event: TimelineEvent) => void;
}
```

## Testing the Integration

### 1. Run Integration Tests

```bash
cd /home/bamer/.opencode/emergent-learning/Open_ELF/timeline_dashboard
python test_integration.py
```

### 2. Verify API Endpoints

Start the dashboard backend and check:

```bash
curl http://localhost:8888/api/v1/timeline/event-types
curl http://localhost:8888/api/v1/timeline/stats
```

### 3. Check Event Chronicle

Verify events are being recorded in the database:

```bash
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM event_chronicle"
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT timestamp, event_type FROM event_chronicle ORDER BY timestamp DESC LIMIT 10"
```

## Troubleshooting

### Common Issues

1. **Empty Timeline**: Check that events are being recorded in the chronicle
2. **API Errors**: Verify the integration was added to main.py
3. **Frontend Not Updating**: Ensure the frontend is calling the new endpoints
4. **Missing Event Types**: Check that event_chronicle.py is functioning

### Debug Commands

```bash
# Check database has events
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT COUNT(*) FROM event_chronicle"
sqlite3 ~/.opencode/emergent-learning/memory/index.db "SELECT timestamp, event_type FROM event_chronicle ORDER BY timestamp DESC LIMIT 10"

# Test event_adapter directly
python3 -c "
import sys
sys.path.insert(0, '/home/bamer/.opencode/emergent-learning/Open_ELF')
from timeline_dashboard.event_adapter import get_chronicle_events
events = get_chronicle_events(limit=5)
print(f'Events returned: {len(events)}')
for e in events:
    print(f'{e[\"timestamp\"][:19]} | {e[\"event_type\"]} | {e[\"source\"][:50]}')
"

# Test API endpoints
curl -v http://localhost:8888/api/v1/timeline/events?limit=5
```

## Extending the Integration

### Adding New Event Types

1. Add new entry to `EVENT_CONFIGS` in `timeline_events.py`
2. The frontend will automatically display the new event type with proper styling

### Custom Event Processing

Modify `convert_chronicle_event_to_timeline_event` in `event_adapter.py` to customize how events are processed.

## Benefits

1. **Real-time Events**: See individual events as they happen
2. **Rich Information**: Access to file paths, line numbers, and metadata
3. **Better Filtering**: Filter by event type and source
4. **Extensible**: Easy to add new event types
5. **Consistent**: Uses the standard ELF Event Chronicle system