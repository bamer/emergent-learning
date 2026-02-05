import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap, Activity, FolderOpen, Server, CheckCircle, XCircle,
  AlertCircle, RefreshCw, Clock, ChevronRight, ChevronDown,
  TrendingUp, ZapOff, Play, Square
} from 'lucide-react';

// Types
interface EventBridgeStatus {
  running: boolean;
  events_processed: number;
  hooks_dir: string;
  opencode_server: string;
  opencode_status?: string;
  uptime_seconds?: number;
  last_event_time?: string;
}

interface EventBridgeStatusPanelProps {
  apiBaseUrl?: string;
  eventBridgeUrl?: string;
  refreshInterval?: number;
}

// Status configurations
const STATUS_CONFIG = {
  running: {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    icon: CheckCircle,
    label: 'Running'
  },
  stopped: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: XCircle,
    label: 'Stopped'
  },
  error: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertCircle,
    label: 'Error'
  }
};

export function EventBridgeStatusPanel({
  apiBaseUrl = '',
  refreshInterval = 5000
}: EventBridgeStatusPanelProps) {
  const [status, setStatus] = useState<EventBridgeStatus | null>(null);
  const [history, setHistory] = useState<EventBridgeStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [isLaunching, setIsLaunching] = useState(false);

  // Fetch status data
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/event-bridge/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setStatus(data);
      setError(null);

      // Add to history (keep last 20 entries)
      setHistory(prev => {
        const newHistory = [{ ...data, last_event_time: new Date().toISOString() }, ...prev];
        return newHistory.slice(0, 20);
      });
    } catch (err) {
      console.error('Failed to fetch Event Bridge status:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  const controlBridge = useCallback(async (action: 'start' | 'stop' | 'restart') => {
    try {
      if (action === 'start' || action === 'restart') {
        setIsLaunching(true);
        setError(null);
      }
      const response = await fetch(`${apiBaseUrl}/api/v1/event-bridge/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      setTimeout(fetchStatus, 500);
    } catch (err) {
      console.error(`Failed to ${action} event bridge:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${action} event bridge`);
    } finally {
      if (action === 'start' || action === 'restart') {
        setTimeout(() => setIsLaunching(false), 1500);
      }
    }
  }, [apiBaseUrl, fetchStatus]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchStatus();

    if (!autoRefresh) return;

    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, autoRefresh, refreshInterval]);

  // Toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Format uptime
  const formatUptime = (seconds?: number) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  // Calculate events per second
  const calculateEventsPerSecond = () => {
    if (history.length < 2) return null;
    const current = status?.events_processed || 0;
    const previous = history[1]?.events_processed || 0;
    const timeDiff = (new Date().getTime() - new Date(history[1].last_event_time || '').getTime()) / 1000;
    if (timeDiff <= 0) return null;
    return (current - previous) / timeDiff;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading Event Bridge status...</span>
        </div>
      </div>
    );
  }

  const isRunning = status?.running ?? false;
  const statusConfig = isRunning ? STATUS_CONFIG.running : STATUS_CONFIG.stopped;
  const StatusIcon = statusConfig.icon;

  const eventsPerSecond = calculateEventsPerSecond();

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {isRunning ? (
              <Zap className="w-5 h-5 text-amber-400" />
            ) : (
              <ZapOff className="w-5 h-5 text-slate-500" />
            )}
            <h2 className="text-lg font-semibold text-slate-200">Event Bridge</h2>
          </div>

          {/* Status Badge */}
          {status && (
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
              <StatusIcon className="w-3 h-3" />
              <span>{statusConfig.label}</span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {status?.running ? (
            <button
              onClick={() => controlBridge('stop')}
              className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
              title="Stop event bridge"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => controlBridge('start')}
              className="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded"
              title="Start event bridge"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded text-xs flex items-center gap-1 ${
              autoRefresh ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 bg-slate-700/50'
            }`}
          >
            {autoRefresh ? 'Live' : 'Paused'}
          </button>

          <button
            onClick={fetchStatus}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && !isLaunching ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchStatus}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : isLaunching ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <RefreshCw className="w-12 h-12 text-emerald-400 mx-auto mb-3 animate-spin" />
              <h3 className="text-lg font-semibold text-emerald-400 mb-2">Launching event bridge...</h3>
              <p className="text-slate-400 text-sm mb-4">Starting service, this can take a few seconds.</p>
            </div>
          </div>
        ) : (
          <>
            {/* Overview Section */}
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => toggleSection('overview')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-200">Overview</span>
                </div>
                {expandedSections.has('overview') ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </button>

              {expandedSections.has('overview') && status && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    {/* Events Processed */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-amber-400" />
                        <span className="text-xs text-slate-400">Events Processed</span>
                      </div>
                      <div className="text-xl font-bold text-violet-400">
                        {status.events_processed.toLocaleString()}
                      </div>
                      {eventsPerSecond !== null && (
                        <div className="text-xs text-emerald-400 flex items-center gap-1 mt-1">
                          <TrendingUp className="w-3 h-3" />
                          {eventsPerSecond.toFixed(1)} events/s
                        </div>
                      )}
                    </div>

                    {/* Running Status */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Status</span>
                      </div>
                      <div className={`text-lg font-bold ${isRunning ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isRunning ? 'Running' : 'Stopped'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        Service status
                      </div>
                    </div>

                    {/* OpenCode Health */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">OpenCode</span>
                      </div>
                      <div className={`text-lg font-bold ${status.opencode_status === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {status.opencode_status === 'ok' ? 'Healthy' : 'Down'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {status.opencode_server}
                      </div>
                    </div>
                  </div>

                  {/* Last Update */}
                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last check: {formatTime(new Date().toISOString())}
                  </div>
                </div>
              )}
            </div>

            {/* Configuration Section */}
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => toggleSection('config')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-200">Configuration</span>
                </div>
                {expandedSections.has('config') ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </button>

              {expandedSections.has('config') && status && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Hooks Directory</span>
                      <span className="text-sm font-medium text-slate-300 truncate max-w-[200px]">
                        {status.hooks_dir}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">OpenCode Server</span>
                      <span className="text-sm font-medium text-cyan-400">
                        {status.opencode_server}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Event Bridge URL</span>
                       <span className="text-sm font-medium text-slate-300">
                        {`${apiBaseUrl}/api/v1/event-bridge/status`}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Event History */}
            {history.length > 1 && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('history')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Event History</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{history.length} entries</span>
                    {expandedSections.has('history') ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {expandedSections.has('history') && (
                  <div className="border-t border-slate-700/50">
                    <div className="max-h-64 overflow-y-auto">
                      {history.slice(0, 10).map((entry, index) => (
                        <div
                          key={index}
                          className="px-4 py-2 flex items-center justify-between border-b border-slate-700/30 last:border-0 hover:bg-slate-700/20"
                        >
                          <div className="flex items-center gap-3">
                            {entry.running ? (
                              <Zap className="w-4 h-4 text-amber-400" />
                            ) : (
                              <ZapOff className="w-4 h-4 text-slate-500" />
                            )}
                            <span className="text-sm text-slate-300">
                              {formatTime(entry.last_event_time || '')}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="text-violet-400">
                              {entry.events_processed.toLocaleString()} events
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      {status && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Checks: {history.length}</span>
                <span>URL: {`${apiBaseUrl}/api/v1/event-bridge/status`}</span>
            </div>
            <div>
              Refresh: {refreshInterval / 1000}s
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
