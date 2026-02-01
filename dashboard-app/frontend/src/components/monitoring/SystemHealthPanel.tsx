import React, { useState, useEffect, useCallback } from 'react';
import {
  Heart, Activity, Database, HardDrive, GitBranch, Lock,
  TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle,
  Clock, RefreshCw, Server, Cpu, MemoryStick, Wifi, WifiOff,
  ChevronRight, ChevronDown, Terminal
} from 'lucide-react';

// Types
interface SystemHealth {
  id: number;
  timestamp: string;
  status: 'healthy' | 'warning' | 'critical';
  db_integrity: string;
  db_size_mb: number;
  disk_free_mb: number;
  git_status: string;
  stale_locks: number;
  details?: string;
}

interface HealthMetrics {
  avg_response_time_ms: number;
  error_rate: number;
  uptime_percentage: number;
  total_requests: number;
  failed_requests: number;
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
  refreshInterval = 30000 
}: SystemHealthPanelProps) {
  const [currentHealth, setCurrentHealth] = useState<SystemHealth | null>(null);
  const [healthHistory, setHealthHistory] = useState<SystemHealth[]>([]);
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  // Fetch health data
  const fetchHealthData = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/health/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setCurrentHealth(data.current);
      setHealthHistory(data.history || []);
      setMetrics(data.metrics || null);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch health data:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchHealthData();
    
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchHealthData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchHealthData, autoRefresh, refreshInterval]);

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

  // Format bytes
  const formatBytes = (mb: number) => {
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Calculate trend
  const calculateTrend = (current: number, previous?: number) => {
    if (previous === undefined) return null;
    const diff = current - previous;
    const percent = previous !== 0 ? (diff / previous) * 100 : 0;
    return { diff, percent, direction: diff > 0 ? 'up' : diff < 0 ? 'down' : 'same' };
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading health data...</span>
        </div>
      </div>
    );
  }

  const status = currentHealth?.status || 'healthy';
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  // Calculate trends
  const dbSizeTrend = healthHistory.length > 1 
    ? calculateTrend(currentHealth?.db_size_mb || 0, healthHistory[1]?.db_size_mb)
    : null;
  const diskFreeTrend = healthHistory.length > 1
    ? calculateTrend(currentHealth?.disk_free_mb || 0, healthHistory[1]?.disk_free_mb)
    : null;

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
          {currentHealth && (
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
            onClick={fetchHealthData}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchHealthData}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
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
              
              {expandedSections.has('overview') && currentHealth && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                    {/* Database Size */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Database</span>
                      </div>
                      <div className="text-xl font-bold text-violet-400">
                        {formatBytes(currentHealth.db_size_mb)}
                      </div>
                      {dbSizeTrend && (
                        <div className={`text-xs flex items-center gap-1 mt-1 ${
                          dbSizeTrend.direction === 'up' ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {dbSizeTrend.direction === 'up' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {dbSizeTrend.percent.toFixed(1)}%
                        </div>
                      )}
                    </div>

                    {/* Disk Free */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Disk Free</span>
                      </div>
                      <div className="text-xl font-bold text-cyan-400">
                        {formatBytes(currentHealth.disk_free_mb)}
                      </div>
                      {diskFreeTrend && (
                        <div className={`text-xs flex items-center gap-1 mt-1 ${
                          diskFreeTrend.direction === 'down' ? 'text-red-400' : 'text-emerald-400'
                        }`}>
                          {diskFreeTrend.direction === 'down' ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                          {Math.abs(diskFreeTrend.percent).toFixed(1)}%
                        </div>
                      )}
                    </div>

                    {/* Stale Locks */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Lock className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Stale Locks</span>
                      </div>
                      <div className={`text-xl font-bold ${
                        currentHealth.stale_locks > 0 ? 'text-red-400' : 'text-emerald-400'
                      }`}>
                        {currentHealth.stale_locks}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {currentHealth.stale_locks > 0 ? 'Cleanup needed' : 'All clear'}
                      </div>
                    </div>

                    {/* Git Status */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <GitBranch className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Git</span>
                      </div>
                      <div className="text-sm font-medium text-slate-300 truncate">
                        {currentHealth.git_status || 'Unknown'}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        Repository status
                      </div>
                    </div>
                  </div>

                  {/* Last Check */}
                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last check: {formatTime(currentHealth.timestamp)}
                  </div>
                </div>
              )}
            </div>

            {/* Database Integrity Section */}
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => toggleSection('database')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-slate-200">Database Integrity</span>
                </div>
                <div className="flex items-center gap-2">
                  {currentHealth?.db_integrity && (
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      currentHealth.db_integrity === 'ok' 
                        ? 'bg-emerald-500/10 text-emerald-400' 
                        : 'bg-red-500/10 text-red-400'
                    }`}>
                      {currentHealth.db_integrity}
                    </span>
                  )}
                  {expandedSections.has('database') ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>
              
              {expandedSections.has('database') && (
                <div className="px-4 pb-4 border-t border-slate-700/50">
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Integrity Check</span>
                      <span className={`text-sm font-medium ${
                        currentHealth?.db_integrity === 'ok' ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {currentHealth?.db_integrity === 'ok' ? '✅ Passed' : '❌ Failed'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Database Size</span>
                      <span className="text-sm font-medium text-slate-300">
                        {currentHealth ? formatBytes(currentHealth.db_size_mb) : '-'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                      <span className="text-sm text-slate-400">Free Disk Space</span>
                      <span className={`text-sm font-medium ${
                        (currentHealth?.disk_free_mb || 0) < 1000 ? 'text-red-400' : 'text-slate-300'
                      }`}>
                        {currentHealth ? formatBytes(currentHealth.disk_free_mb) : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Performance Metrics Section */}
            {metrics && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('performance')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Performance</span>
                  </div>
                  {expandedSections.has('performance') ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </button>
                
                {expandedSections.has('performance') && (
                  <div className="px-4 pb-4 border-t border-slate-700/50">
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Avg Response Time</div>
                        <div className="text-lg font-bold text-violet-400">
                          {metrics.avg_response_time_ms.toFixed(0)}ms
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Error Rate</div>
                        <div className={`text-lg font-bold ${
                          metrics.error_rate > 0.05 ? 'text-red-400' : 'text-emerald-400'
                        }`}>
                          {(metrics.error_rate * 100).toFixed(2)}%
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Uptime</div>
                        <div className="text-lg font-bold text-cyan-400">
                          {metrics.uptime_percentage.toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Total Requests</div>
                        <div className="text-lg font-bold text-slate-300">
                          {metrics.total_requests.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Health History */}
            {healthHistory.length > 0 && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('history')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Recent History</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{healthHistory.length} entries</span>
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
                      {healthHistory.slice(0, 10).map((entry, index) => {
                        const entryStatus = entry.status;
                        const entryConfig = STATUS_CONFIG[entryStatus];
                        
                        return (
                          <div
                            key={entry.id}
                            className="px-4 py-2 flex items-center justify-between border-b border-slate-700/30 last:border-0 hover:bg-slate-700/20"
                          >
                            <div className="flex items-center gap-3">
                              <entryConfig.icon className={`w-4 h-4 ${entryConfig.color}`} />
                              <span className="text-sm text-slate-300">
                                {formatTime(entry.timestamp)}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 text-xs">
                              <span className="text-slate-500">
                                DB: {formatBytes(entry.db_size_mb)}
                              </span>
                              <span className="text-slate-500">
                                Disk: {formatBytes(entry.disk_free_mb)}
                              </span>
                              {entry.stale_locks > 0 && (
                                <span className="text-red-400">
                                  {entry.stale_locks} locks
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      {currentHealth && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Checks: {healthHistory.length}</span>
              <span>Status: {currentHealth.status}</span>
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
