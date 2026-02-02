# Quick Start: Timeline Dashboard Integration

## 1. Integration with Dashboard Backend

Add these lines to `dashboard-app/backend/main.py`:

```python
# Near the top with other imports
from Open_ELF.timeline_dashboard.demo_integration import integrate_with_dashboard

# In the startup_event function, add this line:
integrate_with_dashboard(app)
```

## 2. New API Endpoints

After integration, these endpoints will be available:

- `GET /api/v1/timeline/events` - Get individual timeline events
- `GET /api/v1/timeline/stats` - Get chronicle statistics
- `GET /api/v1/timeline/recent` - Get recent events
- `GET /api/v1/timeline/event-types` - Get available event types

## 3. Test the Integration

```bash
# Test that events are returned
curl http://localhost:8888/api/v1/timeline/events

# Should return something like:
{
  "status": "ok",
  "events": [
    {
      "id": "uuid-string",
      "timestamp": "2026-02-02T10:30:00Z",
      "event_type": "heuristic_validated",
      "description": "Heuristic validated: Always validate inputs at system boundaries",
      "metadata": {
        "user_id": "test-user"
      },
      "source": "record-heuristic.sh",
      "domain": "testing"
    }
  ],
  "count": 1
}
```

## 4. Frontend Update (Brief)

Update `useDashboardData.ts`:

```typescript
// Replace the timeline data loading with:
const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);

// In loadData function:
const timelineEventsData = await api.get('/api/v1/timeline/events?limit=100').catch(() => []);

// Update state:
setTimelineEvents(timelineEventsData?.events || []);
```

## 5. Done!

Your timeline view should now show individual events with proper icons and colors instead of being empty.

For detailed instructions, see:
- `INTEGRATION_GUIDE.md` - Complete integration guide
- `frontend_integration.md` - Frontend update details
- `test_integration.py` - Run tests to verify everything works