import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu, Activity, CheckCircle, AlertTriangle, RefreshCw,
  ChevronRight, ChevronDown, Clock, Play, Square
} from 'lucide-react';

interface OrchestratorStatusData {
  running: boolean;
  missions_count: number;
  last_check?: string;
  status_url?: string;
}

interface OrchestratorMission {
  id: string;
  agent_type: string;
  status: string;
  start_time?: string | null;
  end_time?: string | null;
}

interface OrchestratorStatusResponse {
  status: string;
  status_data: OrchestratorStatusData;
  missions: OrchestratorMission[];
}

interface OrchestratorStatusPanelProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

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
    icon: AlertTriangle,
    label: 'Stopped'
  }
};

export function OrchestratorStatusPanel({
  apiBaseUrl = '',
  refreshInterval = 10000
}: OrchestratorStatusPanelProps) {
  const [status, setStatus] = useState<OrchestratorStatusData | null>(null);
  const [missions, setMissions] = useState<OrchestratorMission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/orchestrator/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: OrchestratorStatusResponse = await response.json();
      setStatus(data.status_data || null);
      setMissions(data.missions || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch orchestrator status:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  const controlOrchestrator = useCallback(async (action: 'start' | 'stop' | 'restart') => {
    try {
      if (action === 'start' || action === 'restart') {
        setIsLaunching(true);
        setError(null);
      }
      const response = await fetch(`${apiBaseUrl}/api/v1/orchestrator/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setTimeout(fetchStatus, 500);
    } catch (err) {
      console.error(`Failed to ${action} orchestrator:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${action} orchestrator`);
    } finally {
      if (action === 'start' || action === 'restart') {
        setTimeout(() => setIsLaunching(false), 1500);
      }
    }
  }, [apiBaseUrl, fetchStatus]);

  useEffect(() => {
    fetchStatus();
    if (!autoRefresh) return;
    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, autoRefresh, refreshInterval]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const formatTime = (timestamp?: string | null) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading orchestrator status...</span>
        </div>
      </div>
    );
  }

  const isRunning = status?.running ?? false;
  const statusConfig = isRunning ? STATUS_CONFIG.running : STATUS_CONFIG.stopped;
  const StatusIcon = statusConfig.icon;

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">Orchestrator</h2>
          </div>
          {status && (
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
              <StatusIcon className="w-3 h-3" />
              <span>{statusConfig.label}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {status?.running ? (
            <button
              onClick={() => controlOrchestrator('stop')}
              className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded"
              title="Stop orchestrator"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => controlOrchestrator('start')}
              className="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded"
              title="Start orchestrator"
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
              <h3 className="text-lg font-semibold text-emerald-400 mb-2">Launching orchestrator...</h3>
              <p className="text-slate-400 text-sm mb-4">Starting service, this can take a few seconds.</p>
            </div>
          </div>
        ) : (
          <>
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
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="text-xs text-slate-400 mb-1">State</div>
                      <div className={`text-lg font-bold ${isRunning ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isRunning ? 'Running' : 'Stopped'}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="text-xs text-slate-400 mb-1">Missions</div>
                      <div className="text-lg font-bold text-violet-400">
                        {status.missions_count ?? 0}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last check: {formatTime(status.last_check)}
                  </div>
                </div>
              )}
            </div>

            {missions.length > 0 && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('missions')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Active Missions</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{missions.length} entries</span>
                    {expandedSections.has('missions') ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {expandedSections.has('missions') && (
                  <div className="border-t border-slate-700/50">
                    <div className="max-h-64 overflow-y-auto">
                      {missions.map((mission) => (
                        <div
                          key={mission.id}
                          className="px-4 py-2 flex items-center justify-between border-b border-slate-700/30 last:border-0 hover:bg-slate-700/20"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500">{mission.agent_type}</span>
                            <span className="text-sm text-slate-300">{mission.status}</span>
                          </div>
                          <div className="text-xs text-slate-500">
                            {formatTime(mission.start_time)}
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
    </div>
  );
}
