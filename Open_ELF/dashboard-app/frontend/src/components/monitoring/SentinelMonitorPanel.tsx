import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield, Activity, AlertTriangle, CheckCircle, Clock,
  TrendingUp, TrendingDown, Minus, Zap, Brain, Server,
  Database, Wifi, RefreshCw, ChevronDown, ChevronRight,
  Filter, Download, Eye, EyeOff, Bell, BellOff, Play, Pause
} from 'lucide-react';

// Types
interface SentinelMetrics {
  timestamp: string;
  services: {
    frontend: boolean;
    backend: boolean;
    overall: boolean;
  };
  data: {
    learnings: number;
    golden_rules: number;
    regular_heuristics: number;
    experiments: number;
    spike_reports: number;
    total_items: number;
  };
  activity: {
    recent_learnings: number;
    recent_heuristics: number;
    activity_score: number;
  };
  quality: {
    high_confidence_heuristics: number;
    average_confidence: number;
    quality_score: number;
  };
}

interface SentinelAnalysis {
  status: 'healthy' | 'warning' | 'critical';
  analysis: string;
  anomalies: string[];
  recommendations: string[];
  patterns: string[];
  priority_actions: string[];
}

interface SentinelCycle {
  timestamp: string;
  metrics: SentinelMetrics;
  analysis: SentinelAnalysis;
  actions_taken: string[];
  agent_executions: AgentExecutionResult[];
}

interface AgentExecutionResult {
  pattern: string;
  status: 'completed' | 'error';
  agent_analysis?: string;
  is_critical?: boolean;
  ceo_decision?: string;
  actions?: string[];
  error?: string;
}

interface PatternDetection {
  pattern_name: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  detected_at: string;
  cooldown_remaining?: number;
}

interface SentinelMonitorPanelProps {
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
    label: 'Healthy',
    emoji: '🟢'
  },
  warning: {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: AlertTriangle,
    label: 'Warning',
    emoji: '🟡'
  },
  critical: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Critical',
    emoji: '🔴'
  }
};

const SEVERITY_CONFIG = {
  info: { color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/20' },
  warning: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/20' },
  critical: { color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/20' }
};

export function SentinelMonitorPanel({ 
  apiBaseUrl = '', 
  refreshInterval = 30000 
}: SentinelMonitorPanelProps) {
  const [currentCycle, setCurrentCycle] = useState<SentinelCycle | null>(null);
  const [cycleHistory, setCycleHistory] = useState<SentinelCycle[]>([]);
  const [patterns, setPatterns] = useState<PatternDetection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [sentinelRunning, setSentinelRunning] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'cycles' | 'patterns' | 'actions'>('overview');
  const [expandedCycles, setExpandedCycles] = useState<Set<number>>(new Set());

  // Fetch current sentinel status
  const fetchSentinelStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/sentinel/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      if (data.current_cycle) {
        setCurrentCycle(data.current_cycle);
      }
      if (data.recent_cycles) {
        setCycleHistory(data.recent_cycles);
      }
      if (data.patterns) {
        setPatterns(data.patterns);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sentinel status:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to Sentinel');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchSentinelStatus();
    
    if (!autoRefresh || !sentinelRunning) return;
    
    const interval = setInterval(fetchSentinelStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchSentinelStatus, autoRefresh, sentinelRunning, refreshInterval]);

  // Toggle cycle expansion
  const toggleCycleExpansion = (index: number) => {
    setExpandedCycles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Format duration
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  // Get trend indicator
  const getTrend = (current: number, previous?: number) => {
    if (previous === undefined) return <Minus className="w-4 h-4 text-slate-400" />;
    if (current > previous) return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading Sentinel data...</span>
        </div>
      </div>
    );
  }

  const status = currentCycle?.analysis?.status || 'healthy';
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">Sentinel Monitor</h2>
          </div>
          
          {/* Status Badge */}
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
            <StatusIcon className="w-3 h-3" />
            <span>{statusConfig.emoji} {statusConfig.label}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded text-xs flex items-center gap-1 ${
              autoRefresh ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 bg-slate-700/50'
            }`}
            title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
          >
            {autoRefresh ? <Bell className="w-3 h-3" /> : <BellOff className="w-3 h-3" />}
            {autoRefresh ? 'Live' : 'Paused'}
          </button>
          
          {/* Play/Pause Button */}
          <button
            onClick={() => setSentinelRunning(!sentinelRunning)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title={sentinelRunning ? "Pause Sentinel" : "Start Sentinel"}
          >
            {sentinelRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          
          <button
            onClick={fetchSentinelStatus}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh now"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-700/50">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'cycles', label: 'Cycle History', icon: Clock },
          { id: 'patterns', label: 'Patterns', icon: Brain },
          { id: 'actions', label: 'Actions', icon: Zap }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
              selectedTab === tab.id
                ? 'text-violet-400 border-b-2 border-violet-400 bg-violet-500/5'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchSentinelStatus}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {selectedTab === 'overview' && currentCycle && (
              <div className="space-y-4">
                {/* Current Status Card */}
                <div className={`p-4 rounded-lg border ${statusConfig.bgColor} ${statusConfig.borderColor}`}>
                  <div className="flex items-start gap-3">
                    <StatusIcon className={`w-6 h-6 ${statusConfig.color} flex-shrink-0`} />
                    <div className="flex-1">
                      <h3 className={`font-semibold ${statusConfig.color}`}>
                        System Status: {statusConfig.label}
                      </h3>
                      <p className="text-sm text-slate-300 mt-1">
                        {currentCycle.analysis?.analysis || 'No analysis available'}
                      </p>
                      <p className="text-xs text-slate-500 mt-2">
                        Last updated: {formatTime(currentCycle.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {/* Service Health */}
                  <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Server className="w-4 h-4 text-slate-400" />
                      <span className="text-xs text-slate-400">Services</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">Frontend</span>
                        <span className={currentCycle.metrics?.services?.frontend ? 'text-emerald-400' : 'text-red-400'}>
                          {currentCycle.metrics?.services?.frontend ? '🟢' : '🔴'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">Backend</span>
                        <span className={currentCycle.metrics?.services?.backend ? 'text-emerald-400' : 'text-red-400'}>
                          {currentCycle.metrics?.services?.backend ? '🟢' : '🔴'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Data Inventory */}
                  <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Database className="w-4 h-4 text-slate-400" />
                      <span className="text-xs text-slate-400">Data</span>
                    </div>
                    <div className="text-2xl font-bold text-violet-400">
                      {currentCycle.metrics?.data?.total_items?.toLocaleString() || 0}
                    </div>
                    <div className="text-xs text-slate-500">Total items</div>
                  </div>

                  {/* Activity Score */}
                  <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="w-4 h-4 text-slate-400" />
                      <span className="text-xs text-slate-400">Activity (1h)</span>
                    </div>
                    <div className="text-2xl font-bold text-cyan-400">
                      {currentCycle.metrics?.activity?.activity_score || 0}
                    </div>
                    <div className="text-xs text-slate-500">
                      {currentCycle.metrics?.activity?.recent_learnings || 0} learnings,{' '}
                      {currentCycle.metrics?.activity?.recent_heuristics || 0} heuristics
                    </div>
                  </div>

                  {/* Quality Score */}
                  <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-slate-400" />
                      <span className="text-xs text-slate-400">Quality</span>
                    </div>
                    <div className="text-2xl font-bold text-emerald-400">
                      {((currentCycle.metrics?.quality?.quality_score || 0) * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-slate-500">
                      Avg confidence: {((currentCycle.metrics?.quality?.average_confidence || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Anomalies & Recommendations */}
                {(currentCycle.analysis?.anomalies?.length > 0 || 
                  currentCycle.analysis?.recommendations?.length > 0) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Anomalies */}
                    {currentCycle.analysis?.anomalies?.length > 0 && (
                      <div className="p-3 bg-red-500/5 rounded-lg border border-red-500/20">
                        <h4 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          Anomalies Detected
                        </h4>
                        <ul className="space-y-1">
                          {currentCycle.analysis.anomalies.map((anomaly, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="text-red-400">•</span>
                              {anomaly}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommendations */}
                    {currentCycle.analysis?.recommendations?.length > 0 && (
                      <div className="p-3 bg-amber-500/5 rounded-lg border border-amber-500/20">
                        <h4 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          Recommendations
                        </h4>
                        <ul className="space-y-1">
                          {currentCycle.analysis.recommendations.map((rec, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="text-amber-400">•</span>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Priority Actions */}
                {currentCycle.analysis?.priority_actions?.length > 0 && (
                  <div className="p-3 bg-violet-500/5 rounded-lg border border-violet-500/20">
                    <h4 className="text-sm font-semibold text-violet-400 mb-2 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Priority Actions
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {currentCycle.analysis.priority_actions.map((action, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-violet-500/10 text-violet-400 text-xs rounded border border-violet-500/20"
                        >
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Cycles Tab */}
            {selectedTab === 'cycles' && (
              <div className="space-y-3">
                {cycleHistory.length === 0 ? (
                  <div className="text-center text-slate-500 py-8">
                    <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No cycle history available</p>
                  </div>
                ) : (
                  cycleHistory.map((cycle, index) => {
                    const cycleStatus = cycle.analysis?.status || 'healthy';
                    const cycleConfig = STATUS_CONFIG[cycleStatus];
                    const isExpanded = expandedCycles.has(index);
                    
                    return (
                      <div
                        key={index}
                        className={`bg-slate-800/50 rounded-lg border ${cycleConfig.borderColor} overflow-hidden`}
                      >
                        <button
                          onClick={() => toggleCycleExpansion(index)}
                          className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <cycleConfig.icon className={`w-4 h-4 ${cycleConfig.color}`} />
                            <span className="text-sm font-medium text-slate-200">
                              Cycle {cycleHistory.length - index}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded ${cycleConfig.bgColor} ${cycleConfig.color}`}>
                              {cycleConfig.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500">
                              {formatTime(cycle.timestamp)}
                            </span>
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-slate-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-slate-400" />
                            )}
                          </div>
                        </button>
                        
                        {isExpanded && (
                          <div className="px-4 pb-4 border-t border-slate-700/50">
                            <p className="text-sm text-slate-300 mt-3">
                              {cycle.analysis?.analysis}
                            </p>
                            
                            {cycle.agent_executions?.length > 0 && (
                              <div className="mt-3">
                                <h5 className="text-xs font-semibold text-slate-400 mb-2">
                                  Agent Executions ({cycle.agent_executions.length})
                                </h5>
                                <div className="space-y-2">
                                  {cycle.agent_executions.map((exec, i) => (
                                    <div
                                      key={i}
                                      className={`p-2 rounded text-xs ${
                                        exec.status === 'completed'
                                          ? 'bg-emerald-500/10 border border-emerald-500/20'
                                          : 'bg-red-500/10 border border-red-500/20'
                                      }`}
                                    >
                                      <div className="flex items-center gap-2">
                                        <span className={exec.status === 'completed' ? 'text-emerald-400' : 'text-red-400'}>
                                          {exec.status === 'completed' ? '✅' : '❌'}
                                        </span>
                                        <span className="text-slate-300">{exec.pattern}</span>
                                        {exec.is_critical && (
                                          <span className="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">
                                            Critical
                                          </span>
                                        )}
                                      </div>
                                      {exec.agent_analysis && (
                                        <p className="mt-1 text-slate-400 pl-5">
                                          {exec.agent_analysis.substring(0, 100)}...
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {cycle.actions_taken?.length > 0 && (
                              <div className="mt-3">
                                <h5 className="text-xs font-semibold text-slate-400 mb-2">
                                  Actions Taken
                                </h5>
                                <div className="flex flex-wrap gap-1">
                                  {cycle.actions_taken.map((action, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded"
                                    >
                                      {action}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* Patterns Tab */}
            {selectedTab === 'patterns' && (
              <div className="space-y-3">
                {patterns.length === 0 ? (
                  <div className="text-center text-slate-500 py-8">
                    <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No patterns detected yet</p>
                    <p className="text-xs mt-1">Patterns are detected over time as the system learns</p>
                  </div>
                ) : (
                  patterns.map((pattern, index) => {
                    const severityConfig = SEVERITY_CONFIG[pattern.severity];
                    
                    return (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${severityConfig.borderColor} ${severityConfig.bgColor}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <Brain className={`w-4 h-4 ${severityConfig.color} flex-shrink-0 mt-0.5`} />
                            <div>
                              <h4 className={`text-sm font-medium ${severityConfig.color}`}>
                                {pattern.pattern_name}
                              </h4>
                              <p className="text-xs text-slate-300 mt-1">
                                {pattern.description}
                              </p>
                              <p className="text-xs text-slate-500 mt-2">
                                Detected: {formatTime(pattern.detected_at)}
                              </p>
                            </div>
                          </div>
                          <span className={`text-xs px-2 py-0.5 rounded ${severityConfig.bgColor} ${severityConfig.color}`}>
                            {pattern.severity}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* Actions Tab */}
            {selectedTab === 'actions' && (
              <div className="space-y-3">
                {currentCycle?.actions_taken?.length === 0 && cycleHistory.every(c => !c.actions_taken?.length) ? (
                  <div className="text-center text-slate-500 py-8">
                    <Zap className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No autonomous actions taken yet</p>
                    <p className="text-xs mt-1">Actions are executed automatically based on analysis</p>
                  </div>
                ) : (
                  <>
                    {/* Current Actions */}
                    {currentCycle?.actions_taken?.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-semibold text-slate-300 mb-2">Current Cycle</h4>
                        <div className="space-y-2">
                          {currentCycle.actions_taken.map((action, i) => (
                            <div
                              key={i}
                              className="p-3 bg-violet-500/10 rounded-lg border border-violet-500/20 flex items-center gap-3"
                            >
                              <Zap className="w-4 h-4 text-violet-400" />
                              <span className="text-sm text-slate-300">{action}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Historical Actions */}
                    {cycleHistory.some(c => c.actions_taken?.length > 0) && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-300 mb-2">History</h4>
                        <div className="space-y-2">
                          {cycleHistory
                            .filter(c => c.actions_taken?.length > 0)
                            .slice(0, 5)
                            .map((cycle, i) => (
                              <div key={i} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                <p className="text-xs text-slate-500 mb-2">
                                  {formatTime(cycle.timestamp)}
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {cycle.actions_taken.map((action, j) => (
                                    <span
                                      key={j}
                                      className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded"
                                    >
                                      {action}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      {currentCycle && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Cycles tracked: {cycleHistory.length}</span>
              <span>Patterns detected: {patterns.length}</span>
            </div>
            <div>
              Refresh interval: {refreshInterval / 1000}s
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
