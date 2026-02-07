# Timeline Dashboard Integration

This module integrates the ELF Event Chronicle system with the dashboard to provide a real-time timeline view of system events.

## Features

- Real-time event streaming from Event Chronicle database
- Individual event display with proper icons and colors
- Event filtering by type and source
- Playback controls for historical events
- Integration with existing dashboard components

## Components

1. `timeline_api.py` - API endpoints for timeline data
2. `event_adapter.py` - Adapter to convert Event Chronicle database records to dashboard format
3. `timeline_events.py` - Event type definitions and configurations

## Data Source

The timeline dashboard queries directly from the SQLite database at `memory/index.db`:
- Table: `event_chronicle`
- Columns: id, timestamp, event_type, source, source_id, status, summary, data, created_at
- Total events: 200,000+ (growing)

Event types are mapped from operational types (tool_poll, message.updated, etc.) to timeline-friendly types (task_start, task_end, etc.).