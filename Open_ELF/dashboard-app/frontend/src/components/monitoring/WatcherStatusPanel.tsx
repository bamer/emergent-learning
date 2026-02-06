import React, { useState, useEffect, useCallback } from 'react';
import {
  Eye, Activity, AlertTriangle, CheckCircle, Clock, RefreshCw,
  ChevronRight, ChevronDown, Terminal, Zap, Shield, Server,
  Wifi, WifiOff, Play, Square, Settings, FileText
} from 'lucide-react';

// Types
interface WatcherStatus {
  is_running: boolean;
  tier: 'tier1' | 'tier2' | 'idle';
  last_check: string;
  next_check: string;
  check_interval_seconds: number;
  total_checks: number;
  escalations_count: number;
  current_status: 'healthy' | 'warning' | 'critical';
  analysis_summary?: string;
}

interface WatcherLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  message: string;
  tier?: string;
  context?: Record<string, any>;
}

interface WatcherConfig {
  tier1_interval_seconds: number;
  tier2_interval_seconds: number;
  escalation_threshold: number;
  auto_resolve: boolean;
  enabled: boolean;
}

interface WatcherStatusPanelProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

// Status configurations
const STATUS_CONFIG = {
  healthy: {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    icon: CheckCircle,
    label: 'Healthy'
  },
  warning: {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: AlertTriangle,
    label: 'Warning'
  },
  critical: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Critical'
  }
};

const TIER_CONFIG = {
  tier1: { label: 'Tier 1 (Watcher)', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  tier2: { label: 'Tier 2 (Handler)', color: 'text-violet-400', bgColor: 'bg-violet-500/10' },
  idle: { label: 'Idle', color: 'text-slate-400', bgColor: 'bg-slate-500/10' }
};

const LOG_LEVEL_CONFIG = {
  info: { color: 'text-slate-400', borderColor: 'border-slate-700' },
  warning: { color: 'text-amber-400', borderColor: 'border-amber-500/30' },
  error: { color: 'text-red-400', borderColor: 'border-red-500/30' }
};

export function WatcherStatusPanel({ 
  apiBaseUrl = '', 
  refreshInterval = 10000 
}: WatcherStatusPanelProps) {
  const [status, setStatus] = useState<WatcherStatus | null>(null);
  const [logs, setLogs] = useState<WatcherLog[]>([]);
  const [config, setConfig] = useState<WatcherConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['status']));
  const [isLaunching, setIsLaunching] = useState(false);

  // Fetch watcher status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/watcher/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setStatus(data.status_data || null);
      setLogs(data.recent_logs || []);
      setConfig(data.config || null);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch watcher status:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Control watcher
  const controlWatcher = useCallback(async (action: 'start' | 'stop' | 'restart') => {
    try {
      if (action === 'start' || action === 'restart') {
        setIsLaunching(true);
        setError(null);
      }
      const response = await fetch(`${apiBaseUrl}/api/v1/watcher/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      // Refresh status after action
      setTimeout(fetchStatus, 500);
    } catch (err) {
      console.error(`Failed to ${action} watcher:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${action} watcher`);
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

  // Format timestamp with relative time
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    const timeStr = date.toLocaleTimeString();

    // Show relative time if recent
    if (diffMins < 1) return `${timeStr} (just now)`;
    if (diffMins < 60) return `${timeStr} (${diffMins}m ago)`;
    if (diffHours < 24) return `${timeStr} (${diffHours}h ago)`;
    return `${timeStr} (${diffDays}d ago)`;
  };

  // Check if logs are stale (older than 30 minutes)
  const areLogsStale = () => {
    if (logs.length === 0) return true;
    const lastLog = logs[0];
    const diffMs = new Date().getTime() - new Date(lastLog.timestamp).getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    return diffMins > 30;
  };

  // Format duration
  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading watcher status...</span>
        </div>
      </div>
    );
  }

  const currentStatus = status?.current_status || 'healthy';
  const statusConfig = STATUS_CONFIG[currentStatus];
  const StatusIcon = statusConfig.icon;
  const tierConfig = TIER_CONFIG[status?.tier as keyof typeof TIER_CONFIG] || TIER_CONFIG.idle;

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-slate-200">Watcher Status</h2>
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
          {status?.is_running ? (
            <button
              onClick={() => controlWatcher('stop')}
              className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
              title="Stop watcher"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => controlWatcher('start')}
              className="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded"
              title="Start watcher"
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
              <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
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
              <h3 className="text-lg font-semibold text-emerald-400 mb-2">Launching watcher...</h3>
              <p className="text-slate-400 text-sm mb-4">Starting service, this can take a few seconds.</p>
            </div>
          </div>
        ) : (
          <>
            {/* Status Overview */}
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => toggleSection('status')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-200">Current Status</span>
                </div>
                {expandedSections.has('status') ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </button>
              
                {expandedSections.has('status') && status && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    {/* Running Status */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        {!!status.is_running ? (
                          <Wifi className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <WifiOff className="w-4 h-4 text-red-400" />
                        )}
                        <span className="text-xs text-slate-400">State</span>
                      </div>
                      <div className={`text-lg font-bold ${status.is_running ? 'text-emerald-400' : 'text-red-400'}`}>
                        {status.is_running ? 'Running' : 'Stopped'}
                      </div>
                    </div>

                    {/* Current Tier */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Shield className={`w-4 h-4 ${tierConfig.color}`} />
                        <span className="text-xs text-slate-400">Active Tier</span>
                      </div>
                      <div className={`text-lg font-bold ${tierConfig.color}`}>
                        {tierConfig.label}
                      </div>
                    </div>

                    {/* Total Checks */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Total Checks</span>
                      </div>
                      <div className="text-lg font-bold text-violet-400">
                        {(status.total_checks ?? 0).toLocaleString()}
                      </div>
                    </div>

                    {/* Escalations */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Escalations</span>
                      </div>
                      <div className={`text-lg font-bold ${(status.escalations_count ?? 0) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {status.escalations_count ?? 0}
                      </div>
                    </div>
                  </div>

                  {/* Analysis Summary */}
                  {status.analysis_summary && (
                    <div className="mt-3 p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <FileText className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Analysis</span>
                      </div>
                      <p className="text-sm text-slate-300">{status.analysis_summary}</p>
                    </div>
                  )}

                  {/* Timing Info */}
                  <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                    <span>Last check: {formatTime(status.last_check)}</span>
                    <span>Interval: {formatDuration(status.check_interval_seconds ?? 30)}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Configuration */}
            {config && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('config')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Settings className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Configuration</span>
                  </div>
                  {expandedSections.has('config') ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </button>
                
                {expandedSections.has('config') && (
                  <div className="px-4 pb-4 border-t border-slate-700/50">
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Tier 1 Interval</div>
                        <div className="text-sm font-medium text-slate-300">
                          {formatDuration(config.tier1_interval_seconds)}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Tier 2 Interval</div>
                        <div className="text-sm font-medium text-slate-300">
                          {formatDuration(config.tier2_interval_seconds)}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Escalation Threshold</div>
                        <div className="text-sm font-medium text-slate-300">
                          {config.escalation_threshold} issues
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Auto Resolve</div>
                        <div className={`text-sm font-medium ${config.auto_resolve ? 'text-emerald-400' : 'text-slate-400'}`}>
                          {config.auto_resolve ? 'Enabled' : 'Disabled'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Recent Logs */}
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => toggleSection('logs')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-200">Recent Logs</span>
                  {areLogsStale() && (
                    <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">{logs.length} entries</span>
                  {areLogsStale() && (
                    <span className="text-xs text-amber-400">Logs are stale</span>
                  )}
                  {expandedSections.has('logs') ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {expandedSections.has('logs') && (
                <div className="border-t border-slate-700/50">
                  {/* Log Status Banner */}
                  {logs.length === 0 ? (
                    <div className="p-4 bg-amber-500/10 border-b border-amber-500/20">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                        <div>
                          <div className="text-amber-400 font-medium text-sm">No logs found</div>
                          <div className="text-slate-400 text-xs">Watcher may not be logging to the database. Check if the unified logger is being used.</div>
                        </div>
                      </div>
                    </div>
                  ) : areLogsStale() ? (
                    <div className="p-3 bg-amber-500/10 border-b border-amber-500/20">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        <div className="text-xs text-amber-300">
                          Last log is more than 30 minutes old. The watcher may not be using the unified ELF logger properly.
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border-b border-emerald-500/20">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <div className="text-xs text-emerald-300">
                          Logs are current (last entry within 30 minutes)
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Log Entries */}
                  <div className="max-h-64 overflow-y-auto">
                    {logs.length === 0 ? (
                      <div className="p-8 text-center">
                        <Terminal className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                        <div className="text-slate-400 text-sm">No log entries available</div>
                        <div className="text-slate-500 text-xs mt-2">
                          The watcher may need to be configured to use the unified ELF logger.
                        </div>
                      </div>
                    ) : (
                      logs.map((log, index) => {
                        const levelConfig = LOG_LEVEL_CONFIG[log.level];
                        
                        return (
                          <div
                            key={index}
                            className={`px-4 py-3 border-b border-slate-700/30 last:border-0 hover:bg-slate-700/20 ${levelConfig.borderColor}`}
                          >
                            <div className="flex items-start gap-3">
                                {/* Level Badge */}
                                <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1 ${
                                  log.level === 'error' ? 'bg-red-500/20 text-red-400' :
                                  log.level === 'warning' ? 'bg-amber-500/20 text-amber-400' :
                                  'bg-slate-600/30 text-slate-400'
                                }`}>
                                  {log.level === 'error' && <AlertTriangle className="w-3 h-3" />}
                                  {log.level === 'warning' && <AlertTriangle className="w-3 h-3" />}
                                  {log.level === 'info' && <CheckCircle className="w-3 h-3" />}
                                  {log.level.toUpperCase()}
                                </span>
                              
                              {/* Message */}
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-slate-300 mb-1">{log.message}</p>
                                
                                {/* Metadata */}
                                <div className="flex items-center gap-3 text-xs text-slate-500">
                                  <Clock className="w-3 h-3" />
                                  <span>{formatTime(log.timestamp)}</span>
                                  
                                  {log.tier && (
                                    <>
                                      <Shield className="w-3 h-3" />
                                      <span className={
                                        log.tier === 'tier1' ? 'text-blue-300' :
                                        log.tier === 'tier2' ? 'text-violet-300' :
                                        'text-slate-400'
                                      }>
                                        {TIER_CONFIG[log.tier as keyof typeof TIER_CONFIG]?.label || log.tier}
                                      </span>
                                    </>
                                  )}
                                  
                                  {log.context && Object.keys(log.context).length > 0 && (
                                    <span className="text-slate-600">
                                      {Object.keys(log.context).length} context items
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      {status && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Checks: {status.total_checks ?? 0}</span>
              <span>Escalations: {status.escalations_count ?? 0}</span>
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
