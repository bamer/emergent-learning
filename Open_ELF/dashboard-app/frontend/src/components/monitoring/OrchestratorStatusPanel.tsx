import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu, Activity, CheckCircle, AlertTriangle, RefreshCw,
  ChevronRight, ChevronDown, Clock, Play, Square, FolderOpen,
  TrendingUp, Server, MessageCircle, MessageSquare
} from 'lucide-react';

interface OrchestratorStatusData {
  running: boolean;
  missions_count: number;
  last_check?: string;
  status_url?: string;
  hooks_dir?: string;
  opencode_server?: string;
  opencode_status?: string;
  uptime_seconds?: number;
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
  },
  error: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Error'
  }
};

export function OrchestratorStatusPanel({
  apiBaseUrl = '',
  refreshInterval = 10000
}: OrchestratorStatusPanelProps) {
  const [status, setStatus] = useState<OrchestratorStatusData | null>(null);
  const [missions, setMissions] = useState<OrchestratorMission[]>([]);
  const [history, setHistory] = useState<OrchestratorStatusData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const [isLaunching, setIsLaunching] = useState(false);
  
  // Event stats
  const [questionCount, setQuestionCount] = useState(0);
  const [responseCount, setResponseCount] = useState(0);
  const [totalEvents, setTotalEvents] = useState(0);

  const fetchStatus = useCallback(async () => {
    try {
      // Fetch status
      const statusResponse = await fetch(`${apiBaseUrl}/api/v1/orchestrator/status`);
      if (!statusResponse.ok) throw new Error(`HTTP ${statusResponse.status}`);
      const data: OrchestratorStatusResponse = await statusResponse.json();
      setStatus(data.status_data || null);
      setMissions(data.missions || []);
      
      // Add to history (keep last 20 entries)
      setHistory(prev => {
        const newHistory = [{ ...(data.status_data || {}), last_check: new Date().toISOString() }, ...prev];
        return newHistory.slice(0, 20);
      });
      
      // Fetch event stats
      try {
        const eventsResponse = await fetch(`${apiBaseUrl}/api/v1/monitoring/orchestrator/events`);
        if (eventsResponse.ok) {
          const eventsData = await eventsResponse.json();
          if (eventsData.status === 'ok') {
            setQuestionCount(eventsData.question_count || 0);
            setResponseCount(eventsData.response_count || 0);
            setTotalEvents(eventsData.events?.length || 0);
          }
        }
      } catch (eventsErr) {
        // Silently fail for events - status is more important
        console.debug('Failed to fetch orchestrator events:', eventsErr);
      }
      
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

  // Calculate missions per second
  const calculateMissionsPerSecond = () => {
    if (history.length < 2) return null;
    const current = status?.missions_count || 0;
    const previous = history[1]?.missions_count || 0;
    const timeDiff = (new Date().getTime() - new Date(history[1].last_check || '').getTime()) / 1000;
    if (timeDiff <= 0) return null;
    return (current - previous) / timeDiff;
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

  const missionsPerSecond = calculateMissionsPerSecond();

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {isRunning ? (
              <Cpu className="w-5 h-5 text-violet-400" />
            ) : (
              <Cpu className="w-5 h-5 text-slate-500" />
            )}
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
                  {/* Event Stats */}
                  <div className="flex items-center gap-4 mt-3 mb-3 text-xs bg-slate-700/30 p-2 rounded-lg">
                    <div className="flex items-center gap-1 text-slate-400">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-message-circle w-3 h-3 text-orange-400">
                        <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"></path>
                      </svg>
                      <span>Questions:</span>
                      <span className="text-orange-400 font-medium">{questionCount}</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-400">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-check-circle w-3 h-3 text-green-400">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <path d="m9 11 3 3L22 4"></path>
                      </svg>
                      <span>Responses:</span>
                      <span className="text-green-400 font-medium">{responseCount}</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-400">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-message-square w-3 h-3 text-slate-500">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                      </svg>
                      <span>Total:</span>
                      <span className="text-slate-300 font-medium">{totalEvents}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {/* Missions Count */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-4 h-4 text-violet-400" />
                        <span className="text-xs text-slate-400">Missions</span>
                      </div>
                      <div className="text-xl font-bold text-violet-400">
                        {status.missions_count?.toLocaleString() || 0}
                      </div>
                      {missionsPerSecond !== null && (
                        <div className="text-xs text-emerald-400 flex items-center gap-1 mt-1">
                          <TrendingUp className="w-3 h-3" />
                          {missionsPerSecond.toFixed(1)} missions/s
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
                    {status.opencode_status && (
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
                    )}

                    {/* Uptime */}
                    {status.uptime_seconds !== undefined && (
                      <div className="p-3 bg-slate-700/30 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Clock className="w-4 h-4 text-slate-400" />
                          <span className="text-xs text-slate-400">Uptime</span>
                        </div>
                        <div className="text-lg font-bold text-cyan-400">
                          {formatUptime(status.uptime_seconds)}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          Service uptime
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Last Update */}
                  <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last check: {formatTime(status.last_check)}
                  </div>
                </div>
              )}
            </div>

            {/* Configuration Section */}
            {(status?.hooks_dir || status?.opencode_server) && (
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
                      {status.hooks_dir && (
                        <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                          <span className="text-sm text-slate-400">Hooks Directory</span>
                          <span className="text-sm font-medium text-slate-300 truncate max-w-[200px]">
                            {status.hooks_dir}
                          </span>
                        </div>
                      )}
                      {status.opencode_server && (
                        <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                          <span className="text-sm text-slate-400">OpenCode Server</span>
                          <span className="text-sm font-medium text-cyan-400">
                            {status.opencode_server}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center justify-between p-2 bg-slate-700/30 rounded">
                        <span className="text-sm text-slate-400">Orchestrator URL</span>
                        <span className="text-sm font-medium text-slate-300">
                          {`${apiBaseUrl}/api/v1/orchestrator/status`}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Mission History */}
            {history.length > 1 && (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                <button
                  onClick={() => toggleSection('history')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-200">Status History</span>
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
                              <Cpu className="w-4 h-4 text-violet-400" />
                            ) : (
                              <Cpu className="w-4 h-4 text-slate-500" />
                            )}
                            <span className="text-sm text-slate-300">
                              {formatTime(entry.last_check)}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="text-violet-400">
                              {entry.missions_count?.toLocaleString() || 0} missions
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Active Missions */}
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
        
        {/* Footer */}
      {status && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Checks: {history.length}</span>
              <span>URL: {`${apiBaseUrl}/api/v1/orchestrator/status`}</span>
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
