# Frontend Integration Guide

This guide explains how to update the dashboard frontend to use the new timeline API endpoints.

## 1. Update the useDashboardData Hook

Modify `/dashboard-app/frontend/src/hooks/useDashboardData.ts` to use the new timeline endpoint:

```typescript
// Replace this line:
const [timeline, setTimeline] = useState<TimelineData | null>(null);

// With individual events state:
const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
```

```typescript
// In the loadData function, replace:
const [statsData, hotspotsData, runsData, timelineData, anomaliesData, eventsData] = await Promise.all([
  // ...
  api.get('/api/v1/timeline').catch(() => null), // OLD
  // ...
])

// With:
const [statsData, hotspotsData, runsData, timelineEventsData, anomaliesData, eventsData] = await Promise.all([
  // ...
  api.get('/api/v1/timeline/events?limit=100').catch(() => []), // NEW
  // ...
])

// And update the setter:
setTimelineEvents(timelineEventsData?.events || []);
```

## 2. Update TimelineView Component Props

Update the TimelineView component to receive individual events:

```typescript
interface TimelineViewProps {
  events: TimelineEvent[];  // This should now be individual events, not aggregated data
  heuristics: Heuristic[];
  onEventClick: (event: TimelineEvent) => void;
}
```

## 3. Update TimelineView Data Fetching

In the component that uses TimelineView, update to fetch from the new endpoint:

```typescript
// In the parent component of TimelineView
useEffect(() => {
  const loadTimelineEvents = async () => {
    try {
      const response = await api.get('/api/v1/timeline/events?limit=100');
      setTimelineEvents(response.events || []);
    } catch (err) {
      console.error('Failed to load timeline events:', err);
    }
  };
  
  loadTimelineEvents();
  
  // Optional: Set up polling for real-time updates
  const interval = setInterval(loadTimelineEvents, 30000); // Every 30 seconds
  
  return () => clearInterval(interval);
}, [api]);
```

## 4. Add Event Type Filtering

The new API provides event types that can be used for filtering:

```typescript
// Fetch available event types
useEffect(() => {
  const loadEventTypes = async () => {
    try {
      const types = await api.get('/api/v1/timeline/event-types');
      setAvailableEventTypes(types);
    } catch (err) {
      console.error('Failed to load event types:', err);
    }
  };
  
  loadEventTypes();
}, [api]);
```

## 5. Example Updated TimelineView Usage

```tsx
// In the parent component
const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
const [filteredEventType, setFilteredEventType] = useState<string | null>(null);

// Filter events by type
const filteredEvents = useMemo(() => {
  if (!filteredEventType) return timelineEvents;
  return timelineEvents.filter(event => event.event_type === filteredEventType);
}, [timelineEvents, filteredEventType]);

return (
  <TimelineView 
    events={filteredEvents} 
    heuristics={heuristics}
    onEventClick={handleEventClick}
  />
);
```

## 6. Benefits of the New Integration

1. **Individual Events**: Each event is displayed separately with proper icons and colors
2. **Real-time Updates**: Events stream in as they happen
3. **Better Filtering**: Filter by specific event types and sources
4. **Rich Metadata**: Access to file paths, line numbers, and other contextual information
5. **Extensible**: Easy to add new event types and display properties

## 7. Testing the Integration

1. Start the dashboard backend
2. Verify the new endpoints are available:
   - `GET /api/v1/timeline/events`
   - `GET /api/v1/timeline/stats`
   - `GET /api/v1/timeline/event-types`
3. Check that events are returned in the correct format
4. Verify the frontend displays events properly in the TimelineView

## 8. Troubleshooting

If the timeline is still empty:

1. Check that events are being recorded in the Event Chronicle
2. Verify the chronicle directory exists and has files: `~/.opencode/emergent-learning/event_chronicle/`
3. Confirm the API endpoints are returning data
4. Check browser console for any JavaScript errors
5. Ensure the frontend is calling the correct API endpoints