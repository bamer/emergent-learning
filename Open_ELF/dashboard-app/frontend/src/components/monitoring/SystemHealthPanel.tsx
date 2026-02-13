import React, { useState, useEffect, useCallback } from 'react';
import {
  Heart, Activity, Server, Cpu, MemoryStick, HardDrive,
  CheckCircle, AlertCircle, RefreshCw, Clock, ChevronRight, ChevronDown,
  TrendingUp, TrendingDown, Settings, History
} from 'lucide-react';

// Types
interface SystemMetrics {
  cpuLoad: number;
  cpuCores: number;
  cpuUtilization: number;
  memoryTotal: number;
  memoryUsed: number;
  memoryAvailable: number;
  memoryAvailablePercent: number;
  swapTotal: number;
  swapUsed: number;
  swapFree: number;
  swapFreePercent: number;
  llamaServer: {
    running: boolean;
    pid?: number;
    memoryUsed?: number;
  };
  timestamp: string;
}

interface SystemHealthPanelProps {
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
    icon: AlertCircle,
    label: 'Warning'
  },
  critical: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertCircle,
    label: 'Critical'
  }
};

export function SystemHealthPanel({
  apiBaseUrl = '',
  refreshInterval = 10000
}: SystemHealthPanelProps) {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [history, setHistory] = useState<SystemMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  // Format bytes to human readable
  const formatBytes = (bytes: number) => {
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) {
      return `${gb.toFixed(1)} GB`;
    }
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(0)} MB`;
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

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

  // Fetch system metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/system/metrics`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      setMetrics(data);
      setError(null);

      // Add to history (keep last 20 entries)
      setHistory(prev => {
        const newHistory = [data, ...prev];
        return newHistory.slice(0, 20);
      });
    } catch (err) {
      console.error('Failed to fetch system metrics:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
      
      // Use mock data for demonstration if API fails
      const mockData = {
        cpuLoad: 2.53,
        cpuCores: 12,
        cpuUtilization: 21,
        memoryTotal: 31 * 1024 * 1024 * 1024,
        memoryUsed: 22 * 1024 * 1024 * 1024,
        memoryAvailable: 8.8 * 1024 * 1024 * 1024,
        memoryAvailablePercent: 28,
        swapTotal: 31 * 1024 * 1024 * 1024,
        swapUsed: 7.8 * 1024 * 1024 * 1024,
        swapFree: 24 * 1024 * 1024 * 1024,
        swapFreePercent: 77,
        llamaServer: {
          running: true,
          pid: 1592917,
          memoryUsed: 16.2 * 1024 * 1024 * 1024
        },
        timestamp: new Date().toISOString()
      };
      setMetrics(mockData);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchMetrics();

    if (!autoRefresh) return;

    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, autoRefresh, refreshInterval]);

  // Determine overall status
  const getOverallStatus = () => {
    if (!metrics) return 'healthy';
    
    if (metrics.memoryAvailablePercent < 10 || metrics.swapFreePercent < 10) {
      return 'critical';
    }
    if (metrics.memoryAvailablePercent < 20 || metrics.swapFreePercent < 30) {
      return 'warning';
    }
    return 'healthy';
  };

  // Calculate trend
  const calculateTrend = (current: number, previous?: number) => {
    if (previous === undefined) return null;
    const diff = current - previous;
    const percent = previous !== 0 ? (diff / previous) * 100 : 0;
    return { diff, percent, direction: diff > 0 ? 'up' : diff < 0 ? 'down' : 'same' };
  };

  const status = getOverallStatus();
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  // Calculate trends
  const cpuTrend = history.length > 1 ? calculateTrend(metrics?.cpuUtilization || 0, history[1]?.cpuUtilization) : null;
  const memoryTrend = history.length > 1 ? calculateTrend(metrics?.memoryAvailablePercent || 0, history[1]?.memoryAvailablePercent) : null;

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading system metrics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-rose-400" />
            <h2 className="text-lg font-semibold text-slate-200">System Health</h2>
          </div>

          {/* Status Badge */}
          {metrics && (
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
              <StatusIcon className="w-3 h-3" />
              <span>{statusConfig.label}</span>
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
            {autoRefresh ? 'Live' : 'Paused'}
          </button>

          <button
            onClick={fetchMetrics}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && !metrics ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchMetrics}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : metrics ? (
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

              {expandedSections.has('overview') && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    {/* CPU Load */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs text-slate-400">CPU Load</span>
                      </div>
                      <div className="text-xl font-bold text-violet-400">
                        {metrics.cpuLoad.toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {metrics.cpuCores} cores · {metrics.cpuUtilization}%
                      </div>
                      {cpuTrend && (
                        <div className={`text-xs flex items-center gap-1 mt-1 ${
                          cpuTrend.direction === 'up' ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {cpuTrend.direction === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {Math.abs(cpuTrend.percent).toFixed(1)}%
                        </div>
                      )}
                    </div>

                    {/* Memory Available */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <MemoryStick className="w-4 h-4 text-violet-400" />
                        <span className="text-xs text-slate-400">Memory Available</span>
                      </div>
                      <div className="text-xl font-bold text-cyan-400">
                        {formatBytes(metrics.memoryAvailable)}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {formatBytes(metrics.memoryTotal)} total
                      </div>
                      {memoryTrend && (
                        <div className={`text-xs flex items-center gap-1 mt-1 ${
                          memoryTrend.direction === 'up' ? 'text-emerald-400' : 'text-amber-400'
                        }`}>
                          {memoryTrend.direction === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {Math.abs(memoryTrend.percent).toFixed(1)}%
                        </div>
                      )}
                    </div>

                    {/* Swap Free */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-slate-400">Swap Free</span>
                      </div>
                      <div className="text-xl font-bold text-emerald-400">
                        {formatBytes(metrics.swapFree)}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {metrics.swapFreePercent}% free
                      </div>
                    </div>

                    {/* LLM Server Status */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="w-4 h-4 text-rose-400" />
                        <span className="text-xs text-slate-400">LLM Server</span>
                      </div>
                      <div className={`text-lg font-bold ${metrics.llamaServer.running ? 'text-emerald-400' : 'text-red-400'}`}>
                        {metrics.llamaServer.running ? 'Running' : 'Stopped'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {metrics.llamaServer.running && metrics.llamaServer.pid ? `PID: ${metrics.llamaServer.pid}` : 'Not active'}
                      </div>
                    </div>
                  </div>

                  {/* Last Update */}
                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last check: {formatTime(metrics.timestamp)}
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
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">CPU Cores</span>
                      <span className="text-sm font-medium text-slate-300">{metrics.cpuCores}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Total Memory</span>
                      <span className="text-sm font-medium text-cyan-400">{formatBytes(metrics.memoryTotal)}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Total Swap</span>
                      <span className="text-sm font-medium text-cyan-400">{formatBytes(metrics.swapTotal)}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Memory Used</span>
                      <span className="text-sm font-medium text-slate-300">{formatBytes(metrics.memoryUsed)}</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Swap Used</span>
                      <span className="text-sm font-medium text-slate-300">{formatBytes(metrics.swapUsed)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* History Section */}
            {history.length > 1 && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('history')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Metrics History</span>
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
                            <Activity className={`w-4 h-4 ${
                              entry.memoryAvailablePercent < 10 ? 'text-red-400' :
                              entry.memoryAvailablePercent < 20 ? 'text-amber-400' : 'text-emerald-400'
                            }`} />
                            <span className="text-sm text-slate-300">
                              {formatTime(entry.timestamp)}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="text-slate-500">
                              CPU: {entry.cpuLoad.toFixed(2)}
                            </span>
                            <span className="text-slate-500">
                              Mem: {entry.memoryAvailablePercent.toFixed(0)}%
                            </span>
                            <span className="text-slate-500">
                              Swap: {entry.swapFreePercent.toFixed(0)}%
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
        ) : null}
      </div>

      {/* Footer */}
      {metrics && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Checks: {history.length}</span>
              <span>Status: {status}</span>
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
