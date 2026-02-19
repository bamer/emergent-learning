import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield, Activity, AlertTriangle, CheckCircle, Clock,
  TrendingUp, TrendingDown, Zap, Brain, Server,
  Database, RefreshCw, ChevronDown, ChevronRight,
  Bell, BellOff, Play, Pause, Eye, Target, ZapOff, Minus
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

interface AIAnalysisSchedule {
  agents: {
    sentinel: {
      last_analysis: string | null;
      next_analysis: string | null;
      last_check: string | null;
      ai_used_in_last_analysis: boolean;
      config: {
        analysis_interval: number;
        basic_check_interval: number;
        note: string;
      };
    };
    orchestrator: {
      last_analysis: string | null;
      next_analysis: string | null;
      last_check: string | null;
      ai_used_in_last_analysis: boolean;
      config: {
        analysis_interval: number;
        basic_check_interval: number;
        note: string;
      };
    };
  };
}

interface SentinelMonitorPanelProps {
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
  },
  nominal: {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    icon: CheckCircle,
    label: 'Nominal',
    emoji: '✅',
    description: 'Running as expected'
  },
  stale: {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: Clock,
    label: 'Stale',
    emoji: '⏰',
    description: 'No recent updates'
  },
  error: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Error',
    emoji: '❌',
    description: 'Error state detected'
  },
  stopped: {
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
    icon: Pause,
    label: 'Stopped',
    emoji: '⏹️',
    description: 'Service not running'
  }
};

const SEVERITY_CONFIG = {
  info: { color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/20', emoji: 'ℹ️' },
  warning: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/20', emoji: '⚠️' },
  critical: { color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/20', emoji: '🚨' }
};

// Helper to format intervals in human-readable format
function formatInterval(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

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

export function SentinelMonitorPanel({ 
  apiBaseUrl = '', 
  refreshInterval = 30000 
}: SentinelMonitorPanelProps) {
  const [currentCycle, setCurrentCycle] = useState<SentinelCycle | null>(null);
  const [cycleHistory, setCycleHistory] = useState<SentinelCycle[]>([]);
  const [patterns, setPatterns] = useState<PatternDetection[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [aiSchedule, setAISchedule] = useState<AIAnalysisSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [sentinelRunning, setSentinelRunning] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'cycles' | 'patterns' | 'actions' | 'ai'>('overview');
  const [expandedCycles, setExpandedCycles] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  const baseUrl = apiBaseUrl || 'http://localhost:4096';

  // Fetch current sentinel status
  const fetchSentinelStatus = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch real sentinel status from backend API
      const response = await fetch(`${baseUrl}/api/v1/sentinel/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Transform backend data to match frontend types
      const transformedCycle: SentinelCycle = {
        timestamp: data.current_cycle?.timestamp || new Date().toISOString(),
        metrics: {
          timestamp: data.current_cycle?.timestamp || new Date().toISOString(),
          services: {
            frontend: true, // Assume frontend is always running
            backend: true,  // Assume backend is always running
            overall: data.status !== 'critical'
          },
          data: {
            learnings: data.current_cycle?.metrics?.data?.learnings || 0,
            golden_rules: data.current_cycle?.metrics?.data?.golden_rules || 0,
            regular_heuristics: data.current_cycle?.metrics?.data?.regular_heuristics || 0,
            experiments: data.current_cycle?.metrics?.data?.experiments || 0,
            spike_reports: data.current_cycle?.metrics?.data?.spike_reports || 0,
            total_items: data.current_cycle?.metrics?.data?.total_items || 0
          },
          activity: {
            recent_learnings: data.current_cycle?.metrics?.activity?.recent_learnings || 0,
            recent_heuristics: data.current_cycle?.metrics?.activity?.recent_heuristics || 0,
            activity_score: data.current_cycle?.metrics?.activity?.activity_score || 0
          },
          quality: {
            high_confidence_heuristics: data.current_cycle?.metrics?.quality?.high_confidence_heuristics || 0,
            average_confidence: data.current_cycle?.metrics?.quality?.average_confidence || 0,
            quality_score: data.current_cycle?.metrics?.quality?.quality_score || 0
          }
        },
        analysis: {
          status: data.status || 'nominal',
          analysis: data.current_cycle?.analysis?.analysis || 'System status monitoring active.',
          anomalies: data.current_cycle?.analysis?.anomalies || [],
          recommendations: data.current_cycle?.analysis?.recommendations || [],
          patterns: data.current_cycle?.analysis?.patterns || [],
          priority_actions: data.current_cycle?.analysis?.priority_actions || []
        },
        actions_taken: data.current_cycle?.actions_taken || [],
        agent_executions: data.current_cycle?.agent_executions || []
      };

      setCurrentCycle(transformedCycle);
      setCycleHistory(prev => [transformedCycle, ...(prev || [])].slice(0, 50));
      setPatterns(data.patterns || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching sentinel status:', err);
      setError(`Unable to connect to sentinel service: ${err instanceof Error ? err.message : String(err)}`);
      
      // Fallback to mock data if API fails
      const mockCycle: SentinelCycle = {
        timestamp: new Date().toISOString(),
        metrics: {
          timestamp: new Date().toISOString(),
          services: {
            frontend: true,
            backend: true,
            overall: false
          },
          data: {
            learnings: 0,
            golden_rules: 0,
            regular_heuristics: 0,
            experiments: 0,
            spike_reports: 0,
            total_items: 0
          },
          activity: {
            recent_learnings: 0,
            recent_heuristics: 0,
            activity_score: 0
          },
          quality: {
            high_confidence_heuristics: 0,
            average_confidence: 0,
            quality_score: 0
          }
        },
        analysis: {
          status: 'critical',
          analysis: 'Cannot connect to Sentinel monitoring service',
          anomalies: [`Connection failed: ${err instanceof Error ? err.message : String(err)}`],
          recommendations: ['Check if Sentinel service is running'],
          patterns: [],
          priority_actions: ['Restart Sentinel service']
        },
        actions_taken: [],
        agent_executions: []
      };

      setCurrentCycle(mockCycle);
      setCycleHistory([mockCycle]);
      setPatterns([]);
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  // Fetch escalations from backend
  const fetchEscalations = useCallback(async () => {
    try {
      // Mock escalations for demonstration
      setEscalations([]);
    } catch (err) {
      console.error('Error fetching escalations:', err);
    }
  }, [baseUrl]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchSentinelStatus();
    fetchEscalations();
    
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchSentinelStatus();
      fetchEscalations();
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchSentinelStatus, fetchEscalations, autoRefresh, refreshInterval]);

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

  if (loading && !currentCycle) {
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
  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.healthy;
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

                {/* Recent Escalations */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                  <button
                    onClick={() => toggleSection('escalations')}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      <span className="font-medium text-slate-200">Recent Escalations</span>
                      {escalations.length > 0 && (
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          escalations.some(e => e.severity === 'critical') ? 'bg-red-500/20 text-red-400' :
                          escalations.some(e => e.severity === 'high') ? 'bg-amber-500/20 text-amber-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {escalations.length}
                        </span>
                      )}
                    </div>
                    {expandedSections.has('escalations') ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </button>

                  {expandedSections.has('escalations') && (
                    <div className="border-t border-slate-700/50">
                      {escalations.length === 0 ? (
                        <div className="p-4 text-center">
                          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-50" />
                          <div className="text-slate-400 text-sm">No recent escalations</div>
                          <div className="text-slate-500 text-xs mt-1">System operating normally</div>
                        </div>
                      ) : (
                        <div className="max-h-64 overflow-y-auto">
                          {escalations.map((escalation, index) => {
                            const severityColors = {
                              critical: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400' },
                              high: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400' },
                              medium: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400' },
                              low: { bg: 'bg-slate-500/10', border: 'border-slate-500/20', text: 'text-slate-400' }
                            };
                            const colors = severityColors[escalation.severity] || severityColors.low;
                            
                            return (
                              <div
                                key={escalation.id || index}
                                className={`px-4 py-3 border-b border-slate-700/30 last:border-0 ${colors.bg} ${colors.border}`}
                              >
                                <div className="flex items-start gap-3">
                                  <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}>
                                    {escalation.severity.toUpperCase()}
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm text-slate-300 mb-1">{escalation.message}</p>
                                    
                                    {/* Response or Action */}
                                    {(escalation.response || escalation.action_taken) && (
                                      <div className="mt-2 p-2 bg-slate-700/30 rounded text-xs">
                                        {escalation.response && (
                                          <div className="mb-1">
                                            <span className="text-emerald-400 font-medium">Response:</span>
                                            <span className="text-slate-300 ml-1">{escalation.response}</span>
                                          </div>
                                        )}
                                        {escalation.action_taken && (
                                          <div>
                                            <span className="text-violet-400 font-medium">Action:</span>
                                            <span className="text-slate-300 ml-1">{escalation.action_taken}</span>
                                          </div>
                                        )}
                                      </div>
                                    )}
                                    
                                    {/* Metadata */}
                                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-2">
                                      <Clock className="w-3 h-3" />
                                      <span>{formatTime(escalation.timestamp)}</span>
                                      <span className={`px-1.5 py-0.5 rounded ${
                                        escalation.status === 'resolved' ? 'bg-emerald-500/20 text-emerald-400' :
                                        escalation.status === 'acknowledged' ? 'bg-blue-500/20 text-blue-400' :
                                        'bg-amber-500/20 text-amber-400'
                                      }`}>
                                        {escalation.status}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
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
                    const cycleConfig = STATUS_CONFIG[cycleStatus] || STATUS_CONFIG.healthy;
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
