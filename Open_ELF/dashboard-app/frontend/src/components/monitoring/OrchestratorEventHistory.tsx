import React, { useState, useEffect } from 'react';
import { Cpu, MessageCircle, MessageSquare, Clock, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';

interface OrchestratorEvent {
  id: number;
  timestamp: string;
  event_type: string;
  display_type: string;
  display_time: string;
  display_message: string;
  event_category: 'question' | 'response';
  source?: string;
  summary?: string;
}

interface OrchestratorEventHistoryProps {
  apiBaseUrl?: string;
}

export function OrchestratorEventHistory({ apiBaseUrl = '' }: OrchestratorEventHistoryProps) {
  const [events, setEvents] = useState<OrchestratorEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [questionCount, setQuestionCount] = useState(0);
  const [responseCount, setResponseCount] = useState(0);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/orchestrator/events`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        setEvents(data.events || []);
        setQuestionCount(data.question_count || 0);
        setResponseCount(data.response_count || 0);
        setLastUpdate(new Date());
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Failed to fetch orchestrator events:', err);
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

  const getEventIcon = (eventCategory: string, eventType: string) => {
    if (eventCategory === 'question') {
      return <MessageCircle className="w-4 h-4 text-orange-400" />;
    } else {
      return <CheckCircle className="w-4 h-4 text-green-400" />;
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
          <Cpu className="w-5 h-5 text-green-400" />
          <h3 className="text-lg font-semibold text-slate-200">Orchestrator Event History</h3>
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

      {/* Stats Bar */}
      <div className="px-4 py-2 bg-slate-800/30 border-b border-slate-700/30">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-1">
            <MessageCircle className="w-4 h-4 text-orange-400" />
            <span className="text-slate-300">
              Questions: <span className="text-orange-400 font-medium">{questionCount}</span>
            </span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-slate-300">
              Responses: <span className="text-green-400 font-medium">{responseCount}</span>
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300">
              Total: <span className="text-slate-400 font-medium">{events.length}</span>
            </span>
          </div>
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
              <Cpu className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-sm">No orchestrator events found</p>
              <p className="text-slate-500 text-xs mt-1">
                Events will appear here when the orchestrator processes questions and responses
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                  event.event_category === 'question'
                    ? 'bg-orange-900/20 border-orange-700/30 hover:bg-orange-900/30'
                    : 'bg-green-900/20 border-green-700/30 hover:bg-green-900/30'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getEventIcon(event.event_category, event.event_type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      event.event_category === 'question'
                        ? 'text-orange-300 bg-orange-700/50'
                        : 'text-green-300 bg-green-700/50'
                    }`}>
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