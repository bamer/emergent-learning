import React, { useState, useEffect, useCallback } from 'react';
import {
  ScrollText, Filter, Calendar, Search, Download, RefreshCw,
  ChevronDown, ChevronRight, Clock, Tag, Database, AlertCircle,
  CheckCircle, Info, X, FileJson, History
} from 'lucide-react';

// Types
interface ChronicleEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  source: string;
  data: Record<string, any>;
  metadata?: {
    user_id?: string;
    session_id?: string;
    correlation_id?: string;
  };
}

interface ChronicleStats {
  total_events: number;
  event_types: Record<string, number>;
  sources: Record<string, number>;
  date_range: {
    earliest: string | null;
    latest: string | null;
  };
}

interface EventChronicleViewerProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

// Event type configurations
const EVENT_TYPE_CONFIG: Record<string, { color: string; bgColor: string; icon: any }> = {
  heuristic_created: { color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', icon: CheckCircle },
  failure_recorded: { color: 'text-red-400', bgColor: 'bg-red-500/10', icon: AlertCircle },
  agent_spawned: { color: 'text-violet-400', bgColor: 'bg-violet-500/10', icon: Info },
  workflow_started: { color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', icon: Info },
  sentinel_cycle: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', icon: Info },
  default: { color: 'text-slate-400', bgColor: 'bg-slate-500/10', icon: Info }
};

// Source configurations
const SOURCE_CONFIG: Record<string, { color: string }> = {
  'record-heuristic': { color: 'text-emerald-400' },
  'record-failure': { color: 'text-red-400' },
  'dashboard_sentinel': { color: 'text-amber-400' },
  'agent_execution': { color: 'text-violet-400' },
  default: { color: 'text-slate-400' }
};

export function EventChronicleViewer({ 
  apiBaseUrl = '', 
  refreshInterval = 60000 
}: EventChronicleViewerProps) {
  const [events, setEvents] = useState<ChronicleEvent[]>([]);
  const [stats, setStats] = useState<ChronicleStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [limit, setLimit] = useState(50);
  
  // Expanded events
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());

  // Fetch events
  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (selectedEventType) params.append('event_type', selectedEventType);
      if (selectedSource) params.append('source', selectedSource);
      params.append('limit', limit.toString());
      
      const response = await fetch(`${apiBaseUrl}/api/v1/chronicle/events?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setEvents(data.events || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch chronicle events:', err);
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, selectedEventType, selectedSource, limit]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/chronicle/stats`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch chronicle stats:', err);
    }
  }, [apiBaseUrl]);

  // Initial load
  useEffect(() => {
    fetchEvents();
    fetchStats();
  }, [fetchEvents, fetchStats]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchEvents();
      fetchStats();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchEvents, fetchStats]);

  // Toggle event expansion
  const toggleEventExpansion = (eventId: string) => {
    setExpandedEvents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };

  // Filter events by search query
  const filteredEvents = events.filter(event => {
    if (!searchQuery) return true;
    
    const query = searchQuery.toLowerCase();
    return (
      event.event_type.toLowerCase().includes(query) ||
      event.source.toLowerCase().includes(query) ||
      JSON.stringify(event.data).toLowerCase().includes(query)
    );
  });

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format relative time
  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Get event type config
  const getEventConfig = (eventType: string) => {
    return EVENT_TYPE_CONFIG[eventType] || EVENT_TYPE_CONFIG.default;
  };

  // Get source config
  const getSourceConfig = (source: string) => {
    return SOURCE_CONFIG[source] || SOURCE_CONFIG.default;
  };

  // Export events to JSON
  const exportEvents = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chronicle-events-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Get unique event types and sources for filters
  const eventTypes = stats ? Object.keys(stats.event_types) : [];
  const sources = stats ? Object.keys(stats.sources) : [];

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <ScrollText className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">Event Chronicle</h2>
          </div>
          
          {/* Stats */}
          {stats && (
            <div className="flex items-center gap-3 text-xs">
              <span className="text-slate-500">
                Total: <span className="text-violet-400 font-semibold">{stats.total_events.toLocaleString()}</span>
              </span>
              <span className="text-slate-500">
                Types: <span className="text-cyan-400 font-semibold">{Object.keys(stats.event_types).length}</span>
              </span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded text-xs flex items-center gap-1 ${
              autoRefresh ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 bg-slate-700/50'
            }`}
          >
            {autoRefresh ? 'Live' : 'Manual'}
          </button>
          
          <button
            onClick={exportEvents}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Export to JSON"
          >
            <Download className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => { fetchEvents(); fetchStats(); }}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="px-4 py-3 border-b border-slate-700/50 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events..."
            className="w-full pl-9 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500"
          />
        </div>

        {/* Filter Row */}
        <div className="flex gap-3">
          {/* Event Type Filter */}
          <div className="flex-1">
            <select
              value={selectedEventType}
              onChange={(e) => setSelectedEventType(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value="">All Event Types</option>
              {eventTypes.map(type => (
                <option key={type} value={type}>
                  {type} ({stats?.event_types[type] || 0})
                </option>
              ))}
            </select>
          </div>

          {/* Source Filter */}
          <div className="flex-1">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value="">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>
                  {source} ({stats?.sources[source] || 0})
                </option>
              ))}
            </select>
          </div>

          {/* Limit */}
          <div>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={250}>250</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchEvents}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-slate-500">
              <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No events found</p>
              {(searchQuery || selectedEventType || selectedSource) && (
                <p className="text-xs mt-1">Try adjusting your filters</p>
              )}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {filteredEvents.map((event) => {
              const config = getEventConfig(event.event_type);
              const sourceConfig = getSourceConfig(event.source);
              const isExpanded = expandedEvents.has(event.event_id);
              const IconComponent = config.icon;
              
              return (
                <div
                  key={event.event_id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <button
                    onClick={() => toggleEventExpansion(event.event_id)}
                    className="w-full px-4 py-3 flex items-start gap-3 text-left"
                  >
                    {/* Icon */}
                    <div className={`p-2 rounded-lg ${config.bgColor} flex-shrink-0`}>
                      <IconComponent className={`w-4 h-4 ${config.color}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-sm font-medium ${config.color}`}>
                          {event.event_type}
                        </span>
                        <span className="text-xs text-slate-500">•</span>
                        <span className={`text-xs ${sourceConfig.color}`}>
                          {event.source}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTime(event.timestamp)}
                        </span>
                        <span>({formatRelativeTime(event.timestamp)})</span>
                      </div>

                      {/* Preview of data */}
                      {!isExpanded && Object.keys(event.data).length > 0 && (
                        <p className="mt-2 text-xs text-slate-400 truncate">
                          {JSON.stringify(event.data).slice(0, 100)}...
                        </p>
                      )}
                    </div>

                    {/* Expand Icon */}
                    <div className="flex-shrink-0">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </button>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pl-14">
                      {/* Event Data */}
                      {Object.keys(event.data).length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                            <Database className="w-3 h-3" />
                            Event Data
                          </h4>
                          <pre className="p-3 bg-slate-800 rounded-lg text-xs text-slate-300 overflow-x-auto">
                            {JSON.stringify(event.data, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Metadata */}
                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            Metadata
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {event.metadata.user_id && (
                              <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded">
                                User: {event.metadata.user_id}
                              </span>
                            )}
                            {event.metadata.session_id && (
                              <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded">
                                Session: {event.metadata.session_id}
                              </span>
                            )}
                            {event.metadata.correlation_id && (
                              <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded">
                                Correlation: {event.metadata.correlation_id.slice(0, 8)}...
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Event ID */}
                      <div className="mt-3 pt-3 border-t border-slate-700/50">
                        <span className="text-xs text-slate-500">
                          Event ID: <code className="text-slate-400">{event.event_id}</code>
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-700/50">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing {filteredEvents.length} of {events.length} events
          </div>
          <div>
            {stats?.date_range.earliest && stats?.date_range.latest && (
              <span>
                Range: {formatTime(stats.date_range.earliest)} - {formatTime(stats.date_range.latest)}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
