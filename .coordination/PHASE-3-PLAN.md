# Phase 3 - Dashboard Integration Plan

**Status**: Planning Phase 3
**Focus**: Display event_chronicle on dashboard
**Timeline**: Minimal implementation (focused features only)

---

## Overview

Phase 3 will display watcher & learning loop events on the dashboard in real-time.

Current State:

- ✅ event_chronicle table exists with events
- ✅ /api/chronicle endpoints ready
- ✅ Watcher writes events automatically
- ❌ Dashboard doesn't display them yet

Goal: Show unified event stream (watcher + learning events) on dashboard

---

## What to Display

### 1. Event Timeline (New Tab)

Display events in chronological order:

```
[🔍 WATCHER]  2026-01-28 10:30:45  nominal
   Agents checked: 3 | Issues: none

[📚 LEARNING]  2026-01-28 10:30:20  healthy
   Task: analyze_patterns | New heuristic: api-design

[🔍 WATCHER]  2026-01-28 10:30:15  warning
   Agent stale: worker-1 | Restarted

[📚 LEARNING]  2026-01-28 10:29:50  critical
   Task failed: migration | Error logged
```

### 2. Event Statistics

```
Last 24h:
- Watcher cycles: 2,880 (every 30s)
- Learnings recorded: 24
- Issues detected: 3
- Failures: 1
- Heuristics discovered: 2
```

### 3. Event Filters

- By event_type (watcher_cycle, learning_loop_completion, etc.)
- By status (healthy, warning, critical)
- By source (watcher, learning_hook)
- By time range (last hour, last 24h, last 7d)

### 4. Event Details

Click event to see:

- Full timestamp
- Complete status
- Data/metadata (JSON)
- Full summary

---

## Architecture

### Backend (Already Done ✅)

- `dashboard-app/backend/routers/chronicle.py` exists
- Endpoints:
  - `GET /api/chronicle/events` - Query events
  - `GET /api/chronicle/events/stats` - Statistics
  - `GET /api/chronicle/events/latest` - Latest

### Frontend (To Build)

New components:

- `EventTimelinePanel.tsx` - Main timeline view
- `EventFilters.tsx` - Filter controls
- `EventDetailsModal.tsx` - Event details popup
- `EventStatsCard.tsx` - Statistics display
- Hook: `useEvents()` - Fetch & cache events

---

## Implementation Steps

### Step 1: Create Event Hook (useEvents)

```typescript
// frontend/src/hooks/useEvents.ts
export function useEvents() {
  const [events, setEvents] = useState([])
  const [stats, setStats] = useState(null)
  const [filters, setFilters] = useState({
    event_type: null,
    source: null,
    status: null,
    hours: 24
  })

  // Load events based on filters
  useEffect(() => {
    fetchEvents(filters)
  }, [filters])

  return { events, stats, filters, setFilters }
}
```

### Step 2: Create Timeline Component

```typescript
// frontend/src/components/EventTimelinePanel.tsx
export function EventTimelinePanel() {
  const { events, filters, setFilters } = useEvents()
  
  return (
    <div>
      <EventFilters filters={filters} onChange={setFilters} />
      <EventTimeline events={events} />
    </div>
  )
}
```

### Step 3: Add Tab to Dashboard

In `App.tsx`:

```typescript
// Add to activeTab options
const [activeTab, setActiveTab] = useState<'...' | 'events' | '...'>()

// Add to tab list:
{activeTab === 'events' && <EventTimelinePanel />}

// Add button:
<button onClick={() => setActiveTab('events')}>Events</button>
```

### Step 4: Test Integration

- Verify events display
- Test filters
- Check real-time updates
- Performance with many events

---

## Minimal Implementation (MVP)

For Phase 3, focus on:

✅ **Must Have**

- Event timeline display (simple table/list)
- Basic filters (type, status)
- Event count statistics
- Last updated timestamp

⚠️ **Nice to Have**

- Event details modal
- Time range picker
- Search/grep
- Export to CSV

❌ **Skip (Phase 4+)**

- Real-time updates via WebSocket
- Advanced visualizations
- Performance optimizations
- Dashboard persistence

---

## API Usage

### Fetch Recent Events

```bash
GET /api/chronicle/events?hours=24&limit=100
```

Response:

```json
[
  {
    "id": 42,
    "timestamp": "2026-01-28T10:30:45.123456",
    "event_type": "watcher_cycle",
    "source": "watcher",
    "status": "nominal",
    "summary": "Agents checked: 3",
    "data": { ... },
    "created_at": "..."
  },
  ...
]
```

### Filter by Type

```bash
GET /api/chronicle/events?event_type=learning_loop_completion&hours=24
```

### Get Statistics

```bash
GET /api/chronicle/events/stats?hours=24
```

Response:

```json
{
  "query_hours": 24,
  "stats": {
    "watcher_cycle": { "nominal": 48, "warning": 1 },
    "learning_loop_completion": { "healthy": 24, "critical": 1 }
  }
}
```

---

## File Structure (After Phase 3)

```
dashboard-app/frontend/src/
├── hooks/
│   ├── useEvents.ts          ← NEW
│   └── (existing hooks)
├── components/
│   ├── EventTimelinePanel.tsx    ← NEW
│   ├── EventFilters.tsx          ← NEW
│   ├── EventDetailsModal.tsx      ← NEW (optional)
│   ├── EventStatsCard.tsx         ← NEW
│   └── (existing components)
└── App.tsx                   ← MODIFIED (add events tab)
```

---

## Code Samples

### useEvents Hook

```typescript
import { useState, useEffect } from 'react'
import { useAPI } from './useAPI'

export interface Event {
  id: number
  timestamp: string
  event_type: string
  source: string
  status: string
  summary: string
  data: any
  created_at: string
}

export interface EventFilters {
  event_type?: string
  source?: string
  status?: string
  hours: number
  limit: number
}

export function useEvents() {
  const api = useAPI()
  const [events, setEvents] = useState<Event[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<EventFilters>({
    hours: 24,
    limit: 100
  })

  useEffect(() => {
    loadEvents()
    loadStats()
  }, [filters])

  async function loadEvents() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.event_type) params.append('event_type', filters.event_type)
      if (filters.source) params.append('source', filters.source)
      if (filters.status) params.append('status', filters.status)
      params.append('hours', filters.hours.toString())
      params.append('limit', filters.limit.toString())

      const response = await api.get(`/api/chronicle/events?${params}`)
      setEvents(response.data)
    } catch (error) {
      console.error('Failed to load events:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadStats() {
    try {
      const response = await api.get(`/api/chronicle/events/stats?hours=${filters.hours}`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  return { events, stats, loading, filters, setFilters }
}
```

### EventTimelinePanel Component

```typescript
import React from 'react'
import { useEvents } from '../hooks/useEvents'
import { EventFilters } from './EventFilters'
import { EventStatsCard } from './EventStatsCard'

export function EventTimelinePanel() {
  const { events, stats, loading, filters, setFilters } = useEvents()

  return (
    <div className="space-y-4">
      {/* Stats */}
      {stats && <EventStatsCard stats={stats} />}

      {/* Filters */}
      <EventFilters filters={filters} onChange={setFilters} />

      {/* Timeline */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h2 className="text-xl font-bold mb-4">Event Timeline</h2>

        {loading && <p className="text-slate-400">Loading events...</p>}

        {events.length === 0 && !loading && (
          <p className="text-slate-500">No events found</p>
        )}

        {events.length > 0 && (
          <div className="space-y-2">
            {events.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EventRow({ event }: { event: Event }) {
  const iconMap = {
    watcher_cycle: '🔍',
    learning_loop_completion: '📚',
    heuristic_discovery: '💡',
    learning_discovery: '📝',
  }

  const icon = iconMap[event.event_type as keyof typeof iconMap] || '📌'
  const statusColor = {
    healthy: 'text-green-400',
    warning: 'text-yellow-400',
    critical: 'text-red-400',
  }[event.status] || 'text-slate-400'

  return (
    <div className="flex items-start space-x-3 p-3 bg-slate-900 rounded border border-slate-700">
      <span className="text-xl">{icon}</span>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="font-semibold">{event.event_type}</span>
          <span className={statusColor}>{event.status}</span>
        </div>
        <p className="text-sm text-slate-400">{event.summary}</p>
        <span className="text-xs text-slate-500">{event.timestamp}</span>
      </div>
    </div>
  )
}
```

---

## Next Steps

1. **Review current dashboard structure** ✓ (done)
2. **Create useEvents hook** (30 min)
3. **Create EventTimelinePanel component** (30 min)
4. **Add events tab to App.tsx** (15 min)
5. **Test with real events** (30 min)
6. **Optional: EventFilters & stats** (30 min)

**Total MVP time: ~2-3 hours**

---

## Testing

### Manual Testing

1. Start watcher: `./scripts/start-watcher-bigpickle.sh --interval 10`
2. Run a learning task (to generate learning_loop_completion events)
3. Check dashboard "Events" tab
4. Verify events appear in real-time

### Expected Events

```
Watcher cycles: every 30 seconds
Learning events: when tasks complete
Stats: aggregated counts
```

### Debugging

```bash
# Check events via API
curl http://localhost:8888/api/chronicle/events?hours=1

# Check database
sqlite3 memory/index.db "SELECT * FROM event_chronicle ORDER BY id DESC LIMIT 10;"
```

---

## Priorities for MVP

**Must Implement:**

1. ✅ Event timeline display (table/list)
2. ✅ Basic statistics
3. ✅ Status indicator (color coded)
4. ✅ Time range filter

**Nice to Have:**

1. ⚠️ Event type filter
2. ⚠️ Source filter
3. ⚠️ Click for details

**Skip for now:**

1. ❌ Real-time WebSocket updates
2. ❌ Advanced visualizations
3. ❌ Export/download
4. ❌ Performance optimization

---

## Success Criteria

Phase 3 is complete when:

- ✅ Dashboard displays event_chronicle events
- ✅ Events update as watcher/learning hooks run
- ✅ Basic filters work (time range, type)
- ✅ Statistics show event counts
- ✅ No breaking changes to existing dashboard

---

## Ready to Start?

Let me know and I'll:

1. Create the useEvents hook
2. Create EventTimelinePanel component
3. Integrate into App.tsx
4. Test with real watcher events

Which components would you like me to create first?
