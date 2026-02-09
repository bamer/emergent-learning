import React, { useState, useEffect, useCallback } from 'react';
import {
  Eye, Activity, AlertTriangle, CheckCircle, Clock,
  TrendingUp, TrendingDown, Zap, RefreshCw,
  Bell, BellOff, Play, Pause, Minus
} from 'lucide-react';

// Types
interface Escalation {
  id: string;
  agent: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  context?: Record<string, any>;
  timestamp: string;
  response?: string;
  action_taken?: string;
  status: 'pending' | 'acknowledged' | 'resolved';
}

interface WatcherStatusData {
  is_running: boolean;
  current_status: 'healthy' | 'warning' | 'critical';
  total_checks: number;
  last_check: string;
  analysis_summary: string;
}

interface WatcherStatusResponse {
  status: string;
  status_data: WatcherStatusData;
  recent_logs: Array<{
    timestamp: string;
    level: string;
    message: string;
  }>;
}

interface WatcherMonitorPanelProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

// Status configurations - Human-readable with clear labels
const STATUS_CONFIG = {
  healthy: {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    icon: CheckCircle,
    label: 'All Good',
    emoji: '✅',
    description: 'System operating normally'
  },
  warning: {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: AlertTriangle,
    label: 'Needs Attention',
    emoji: '⚠️',
    description: 'Some issues detected'
  },
  critical: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Action Required',
    emoji: '🚨',
    description: 'Critical issues need immediate action'
  }
};

// Helper to format time ago
function formatTimeAgo(timestamp: string): string {
  if (!timestamp) return 'Never';
  
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now.getTime() - time.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return time.toLocaleDateString();
}

export function WatcherMonitorPanel({ 
  apiBaseUrl = '', 
  refreshInterval = 30000 
}: WatcherMonitorPanelProps) {
  const [statusData, setStatusData] = useState<WatcherStatusData | null>(null);
  const [recentLogs, setRecentLogs] = useState<Array<{timestamp: string; level: string; message: string}>>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [watcherRunning, setWatcherRunning] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'logs' | 'escalations'>('overview');

  const baseUrl = apiBaseUrl || 'http://localhost:4096';

  // Fetch watcher status from backend
  const fetchWatcherStatus = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/watcher/status`);
      if (!response.ok) throw new Error('Failed to fetch watcher status');
      const data: WatcherStatusResponse = await response.json();
      
      setStatusData(data.status_data);
      setRecentLogs(data.recent_logs || []);
      setWatcherRunning(data.status_data?.is_running || false);
      setError(null);
    } catch (err) {
      console.error('Error fetching watcher status:', err);
      setError('Unable to connect to watcher service');
    }
  }, [baseUrl]);

  // Fetch escalations from backend
  const fetchEscalations = useCallback(async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/escalations?agent=watcher&limit=10`);
      if (!response.ok) throw new Error('Failed to fetch escalations');
      const data = await response.json();
      
      const escalationList: Escalation[] = (data.escalations || []).map((e: any) => ({
        id: e.id,
        agent: e.agent || 'watcher',
        severity: e.severity || 'low',
        message: e.summary || e.display_message || 'No message',
        context: e.data || {},
        timestamp: e.timestamp,
        response: undefined,
        action_taken: undefined,
        status: e.requires_action ? 'pending' : 'resolved'
      }));
      
      setEscalations(escalationList);
    } catch (err) {
      console.error('Error fetching escalations:', err);
    }
  }, [baseUrl]);

  // Initial load and auto-refresh
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchWatcherStatus(),
        fetchEscalations()
      ]);
      setLoading(false);
    };
    
    loadData();
    
    if (!autoRefresh || !watcherRunning) return;
    
    const interval = setInterval(() => {
      fetchWatcherStatus();
      fetchEscalations();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchWatcherStatus, fetchEscalations, autoRefresh, watcherRunning, refreshInterval]);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get log level badge color
  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'text-red-400 bg-red-500/10';
      case 'warning': return 'text-amber-400 bg-amber-500/10';
      case 'info': return 'text-blue-400 bg-blue-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading Watcher data...</span>
        </div>
      </div>
    );
  }

  const status = statusData?.current_status || 'healthy';
  const statusConfig = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.healthy;
  const StatusIcon = statusConfig.icon;

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-slate-200">Watcher Monitor</h2>
          </div>
          
          {/* Status Badge */}
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
            <StatusIcon className="w-3 h-3" />
            <span>{statusConfig.emoji} {statusConfig.label}</span>
          </div>
          
          {/* Running Status */}
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs ${watcherRunning ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'}`}>
            {watcherRunning ? <Activity className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {watcherRunning ? 'Active' : 'Stopped'}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded text-xs flex items-center gap-1 ${autoRefresh ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 bg-slate-700/50'}`}
            title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
          >
            {autoRefresh ? <Bell className="w-3 h-3" /> : <BellOff className="w-3 h-3" />}
            {autoRefresh ? 'Live' : 'Paused'}
          </button>
          
          <button
            onClick={() => setWatcherRunning(!watcherRunning)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title={watcherRunning ? 'Pause Watcher' : 'Start Watcher'}
          >
            {watcherRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          
          <button
            onClick={fetchWatcherStatus}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh now"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-700/50">
        {(['overview', 'logs', 'escalations'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-4 py-2 text-xs font-medium capitalize transition-colors ${
              selectedTab === tab
                ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-400/5'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {selectedTab === 'overview' && (
          <div className="space-y-4">
            {/* Status Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Total Checks</div>
                <div className="text-xl font-semibold text-slate-200">{statusData?.total_checks || 0}</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Last Check</div>
                <div className="text-sm text-slate-200">{formatTimeAgo(statusData?.last_check || '')}</div>
              </div>
            </div>

            {/* Analysis Summary */}
            <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
              <div className="text-xs text-slate-400 mb-2">Analysis</div>
              <div className="text-sm text-slate-200">{statusData?.analysis_summary || 'No analysis available'}</div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center bg-slate-800/30 rounded-lg p-2 border border-slate-700/30">
                <div className="text-lg font-semibold text-emerald-400">{recentLogs.length}</div>
                <div className="text-xs text-slate-400">Recent Logs</div>
              </div>
              <div className="text-center bg-slate-800/30 rounded-lg p-2 border border-slate-700/30">
                <div className="text-lg font-semibold text-amber-400">{escalations.filter(e => e.status === 'pending').length}</div>
                <div className="text-xs text-slate-400">Pending</div>
              </div>
              <div className="text-center bg-slate-800/30 rounded-lg p-2 border border-slate-700/30">
                <div className="text-lg font-semibold text-cyan-400">{statusData?.is_running ? 'Yes' : 'No'}</div>
                <div className="text-xs text-slate-400">Running</div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'logs' && (
          <div className="space-y-2">
            {recentLogs.length === 0 ? (
              <div className="text-center text-slate-400 py-8">No recent logs</div>
            ) : (
              recentLogs.map((log, index) => (
                <div key={index} className="flex items-start gap-2 bg-slate-800/30 rounded-lg p-2 border border-slate-700/30">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${getLogLevelColor(log.level)}`}>
                    {log.level}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-slate-400">{formatTimeAgo(log.timestamp)}</div>
                    <div className="text-sm text-slate-200 truncate">{log.message}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'escalations' && (
          <div className="space-y-2">
            {escalations.length === 0 ? (
              <div className="text-center text-slate-400 py-8">No escalations</div>
            ) : (
              escalations.map((escalation) => (
                <div key={escalation.id} className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      escalation.severity === 'critical' ? 'text-red-400 bg-red-500/10' :
                      escalation.severity === 'high' ? 'text-amber-400 bg-amber-500/10' :
                      'text-blue-400 bg-blue-500/10'
                    }`}>
                      {escalation.severity}
                    </span>
                    <span className="text-xs text-slate-400">{formatTimeAgo(escalation.timestamp)}</span>
                  </div>
                  <div className="text-sm text-slate-200">{escalation.message}</div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
