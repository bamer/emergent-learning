import React, { useState, useEffect } from 'react';
import { Eye, Clock, FileText, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface WatcherEvent {
  id: number;
  timestamp: string;
  display_type: string;
  display_time: string;
  display_message: string;
  event_type?: string;
  source?: string;
  summary?: string;
}

interface WatcherEventHistoryProps {
  apiBaseUrl?: string;
}

export function WatcherEventHistory({ apiBaseUrl = '' }: WatcherEventHistoryProps) {
  const [events, setEvents] = useState<WatcherEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/watcher/events`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        setEvents(data.events || []);
        setLastUpdate(new Date());
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Failed to fetch watcher events:', err);
      setError(err instanceof Error ? err.message : 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchEvents, 30000);
    
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const getEventIcon = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case 'file_change':
      case 'file_modification':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'file_creation':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'file_deletion':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'watcher_status':
        return <Eye className="w-4 h-4 text-purple-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/50 border border-slate-700/50 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-slate-200">Watcher Event History</h3>
        </div>
        
        <div className="flex items-center gap-2">
          {lastUpdate && (
            <span className="text-xs text-slate-400">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchEvents}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && events.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="flex items-center gap-2 text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Loading events...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-400 text-sm mb-2">{error}</p>
              <button
                onClick={fetchEvents}
                className="px-3 py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded text-sm transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : events.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <Eye className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-sm">No watcher events found</p>
              <p className="text-slate-500 text-xs mt-1">
                Events will appear here when the watcher detects file changes
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className="flex items-start gap-3 p-3 bg-slate-800/30 hover:bg-slate-800/50 rounded-lg border border-slate-700/30 transition-colors"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getEventIcon(event.display_type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-slate-300 bg-slate-700/50 px-2 py-0.5 rounded">
                      {event.display_type}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </div>
                  
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {event.display_message}
                  </p>
                  
                  {event.source && (
                    <p className="text-xs text-slate-500 mt-1">
                      Source: {event.source}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-900/50">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>{events.length} events</span>
          <span>Auto-refresh: 30s</span>
        </div>
      </div>
    </div>
  );
}