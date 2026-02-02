# Timeline Dashboard Integration

This module integrates the ELF Event Chronicle system with the dashboard to provide a real-time timeline view of system events.

## Features

- Real-time event streaming from Event Chronicle
- Individual event display with proper icons and colors
- Event filtering by type and source
- Playback controls for historical events
- Integration with existing dashboard components

## Components

1. `timeline_api.py` - API endpoints for timeline data
2. `event_adapter.py` - Adapter to convert Event Chronicle format to dashboard format
3. `timeline_events.py` - Event type definitions and configurations