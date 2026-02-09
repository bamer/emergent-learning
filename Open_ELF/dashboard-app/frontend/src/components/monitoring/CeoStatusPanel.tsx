import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  User, Inbox, AlertTriangle, CheckCircle, Clock, 
  RefreshCw, Play, Square, ChevronRight, ChevronDown,
  Activity, Crown, FileText, TrendingUp, TrendingDown,
  Minus, Zap, Brain, Bell, BellOff, Shield
} from 'lucide-react';

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

interface CeoItem {
  filename: string;
  title: string;
  priority: string;
  status: string;
  date: string | null;
  summary: string;
  path: string;
}

interface CeoMetrics {
  pending: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  resolved: number;
  total: number;
}

interface CeoAnalysis {
  status: 'active' | 'idle' | 'overloaded';
  analysis: string;
  actions: string[];
  patterns: string[];
}

interface CeoCycle {
  timestamp: string;
  items_processed: number;
  decisions_made: string[];
  actions_taken: string[];
}

interface CeoStatusPanelProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

const STATUS_CONFIG = {
  active: {
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    icon: Crown,
    label: 'Active',
    emoji: '🟢'
  },
  idle: {
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
    icon: User,
    label: 'Idle',
    emoji: '⚪'
  },
  overloaded: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Overloaded',
    emoji: '🔴'
  }
};

const PRIORITY_CONFIG = {
  Critical: {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle
  },
  High: {
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
    icon: AlertTriangle
  },
  Medium: {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: Bell
  },
  Low: {
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
    icon: BellOff
  }
};

export function CeoStatusPanel({
  apiBaseUrl = '',
  refreshInterval = 30000
}: CeoStatusPanelProps) {
  const [items, setItems] = useState<CeoItem[]>([]);
  const [metrics, setMetrics] = useState<CeoMetrics | null>(null);
  const [analysis, setAnalysis] = useState<CeoAnalysis | null>(null);
  const [cycleHistory, setCycleHistory] = useState<CeoCycle[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [ceoRunning, setCeoRunning] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'items' | 'history' | 'actions'>('overview');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  
  // Refs to prevent race conditions
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  const isInitialLoadRef = useRef(true); // Track if this is the first load

  const fetchCeoStatus = useCallback(async () => {
    // Prevent updates if component is unmounted
    if (!isMountedRef.current) return;
    
    const isInitialLoad = isInitialLoadRef.current;
    
    // Only show loading state on initial load, not background refreshes
    if (isInitialLoad) {
      setLoading(true);
    }
    
    try {
      setError(null);
      
      // Fetch CEO inbox items from the correct endpoint
      const inboxResponse = await fetch(`${apiBaseUrl}/api/v1/ceo/items`);
      if (!inboxResponse.ok) {
        throw new Error(`HTTP ${inboxResponse.status}: ${inboxResponse.statusText}`);
      }
      
      const inboxData = await inboxResponse.json();
      
      // Only update state if still mounted
      if (!isMountedRef.current) return;
      
      setItems(inboxData || []);
      
      // Calculate metrics
      const pending = inboxData.filter((item: CeoItem) => item.status === 'Pending');
      const metrics: CeoMetrics = {
        pending: pending.length,
        critical: pending.filter((item: CeoItem) => item.priority.includes('Critical')).length,
        high: pending.filter((item: CeoItem) => item.priority.includes('High')).length,
        medium: pending.filter((item: CeoItem) => item.priority.includes('Medium')).length,
        low: pending.filter((item: CeoItem) => item.priority.includes('Low')).length,
        resolved: inboxData.filter((item: CeoItem) => item.status !== 'Pending').length,
        total: inboxData.length
      };
      setMetrics(metrics);
      
      // Mark initial load as complete on successful data load
      if (isInitialLoadRef.current) {
        isInitialLoadRef.current = false;
      }
      
      // Generate analysis based on metrics
      let status: 'active' | 'idle' | 'overloaded' = 'idle';
      let analysis_text = 'CEO is monitoring the system.';
      
      if (metrics.pending > 0) {
        if (metrics.critical > 2 || metrics.high > 5) {
          status = 'overloaded';
          analysis_text = `Critical backlog detected. ${metrics.critical} critical and ${metrics.high} high priority items require immediate attention.`;
        } else {
          status = 'active';
          analysis_text = `CEO is actively processing ${metrics.pending} pending escalations.`;
        }
      }
      
      setAnalysis({
        status,
        analysis: analysis_text,
        actions: metrics.pending > 0 ? ['Review pending escalations', 'Prioritize critical items'] : ['Monitor system health'],
        patterns: metrics.critical > 0 ? ['Critical escalations detected'] : []
      });
      
      // Check if CEO agent is running
      try {
        const agentResponse = await fetch(`${apiBaseUrl}/api/v1/agents/status`);
        if (agentResponse.ok) {
          const agentData = await agentResponse.json();
          const ceoAgent = agentData.agents?.find((a: any) => 
            a.agent_type === 'ceo' || a.name?.toLowerCase().includes('ceo')
          );
          setCeoRunning(ceoAgent?.status === 'running' || ceoAgent?.status === 'ready');
        }
      } catch {
        setCeoRunning(false);
      }
      
      setLastUpdate(new Date());
    } catch (err) {
      if (!isMountedRef.current) return;
      console.error('Failed to fetch CEO status:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch CEO status');
    } finally {
      // Only stop loading state on initial load
      if (!isMountedRef.current) return;
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, [apiBaseUrl]);

  // Fetch escalations
  const fetchEscalations = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/escalations?agent=ceo&limit=10`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setEscalations(data.escalations || []);
    } catch (err) {
      console.error('Failed to fetch escalations:', err);
    }
  }, [apiBaseUrl]);

  // Spawn CEO agent
  const spawnCeoAgent = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/spawn_direct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: 'ceo',
          agent_name: 'CEO',
          mission: `You are the CEO agent for the Emergent Learning Framework. Your role is to:
1. Review and prioritize escalations from the ceo-inbox
2. Make strategic decisions about system improvements
3. Coordinate with other agents when needed
4. Process pending items and mark them as resolved when appropriate
5. Generate recommendations for system optimization

Current status: ${metrics?.pending || 0} pending escalations to review.

Please check the ceo-inbox directory and process any pending items. For each item:
- Read and understand the escalation
- Make a decision or recommendation
- Update the item status if resolved
- Create action items if needed`
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to spawn CEO agent: ${response.statusText}`);
      }
      
      setCeoRunning(true);
      // Refresh status after spawning (without showing loading state)
      fetchCeoStatus();
    } catch (err) {
      console.error('Failed to spawn CEO agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to spawn CEO agent');
    }
  }, [apiBaseUrl]); // metrics not needed here (read at call time), fetchCeoStatus is stable

  useEffect(() => {
    isMountedRef.current = true;
    
    // Initial fetch
    fetchCeoStatus();
    fetchEscalations();
    
    // Setup auto-refresh
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchCeoStatus();
        fetchEscalations();
      }, refreshInterval);
    }
    
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, refreshInterval]);

  // Cleanup on unmount (extra safety)
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const toggleItemExpansion = (filename: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(filename)) {
        newSet.delete(filename);
      } else {
        newSet.add(filename);
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

  const getPriorityConfig = (priority: string) => {
    const priorityKey = priority.includes('Critical') ? 'Critical' :
                       priority.includes('High') ? 'High' :
                       priority.includes('Medium') ? 'Medium' : 'Low';
    return PRIORITY_CONFIG[priorityKey] || PRIORITY_CONFIG.Low;
  };

  const formatTime = (timestamp?: string | null) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString();
  };

  if (loading && items.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading CEO status...</span>
        </div>
      </div>
    );
  }

  const status = analysis?.status || 'idle';
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Crown className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-slate-200">CEO Status</h2>
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
          
          {/* CEO Agent Control */}
          <button
            onClick={ceoRunning ? () => {} : spawnCeoAgent}
            className={`p-1.5 rounded ${
              ceoRunning 
                ? 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10' 
                : 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10'
            }`}
            title={ceoRunning ? "CEO Agent Running" : "Start CEO Agent"}
            disabled={ceoRunning}
          >
            {ceoRunning ? <Crown className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          
          <button
            onClick={fetchCeoStatus}
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
          { id: 'items', label: 'Inbox', icon: Inbox },
          { id: 'history', label: 'History', icon: Clock },
          { id: 'actions', label: 'Actions', icon: Zap }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
              selectedTab === tab.id
                ? 'text-amber-400 border-b-2 border-amber-400 bg-amber-500/5'
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
              <h3 className="text-lg font-semibold text-red-400 mb-2">Error Loading CEO Status</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchCeoStatus}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {selectedTab === 'overview' && (
              <div className="space-y-4">
                {/* Current Status Card */}
                <div className={`p-4 rounded-lg border ${statusConfig.bgColor} ${statusConfig.borderColor}`}>
                  <div className="flex items-start gap-3">
                    <StatusIcon className={`w-6 h-6 ${statusConfig.color} flex-shrink-0`} />
                    <div className="flex-1">
                      <h3 className={`font-semibold ${statusConfig.color}`}>
                        CEO Status: {statusConfig.label}
                      </h3>
                      <p className="text-sm text-slate-300 mt-1">
                        {analysis?.analysis || 'CEO is monitoring the system.'}
                      </p>
                      {lastUpdate && (
                        <p className="text-xs text-slate-500 mt-2">
                          Last updated: {lastUpdate.toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                {metrics && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {/* Pending Items */}
                    <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                      <div className="flex items-center gap-2 mb-2">
                        <Inbox className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400">Pending</span>
                      </div>
                      <div className="text-2xl font-bold text-amber-400">
                        {metrics.pending}
                      </div>
                      <div className="text-xs text-slate-500">Items to review</div>
                    </div>

                    {/* Critical Items */}
                    <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        <span className="text-xs text-slate-400">Critical</span>
                      </div>
                      <div className="text-2xl font-bold text-red-400">
                        {metrics.critical}
                      </div>
                      <div className="text-xs text-slate-500">Urgent action needed</div>
                    </div>

                    {/* High Priority */}
                    <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                      <div className="flex items-center gap-2 mb-2">
                        <Bell className="w-4 h-4 text-orange-400" />
                        <span className="text-xs text-slate-400">High</span>
                      </div>
                      <div className="text-2xl font-bold text-orange-400">
                        {metrics.high}
                      </div>
                      <div className="text-xs text-slate-500">High priority items</div>
                    </div>

                    {/* Resolved */}
                    <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs text-slate-400">Resolved</span>
                      </div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {metrics.resolved}
                      </div>
                      <div className="text-xs text-slate-500">Completed items</div>
                    </div>
                  </div>
                )}

                {/* Priority Breakdown */}
                {metrics && metrics.pending > 0 && (
                  <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-slate-300 mb-3">Priority Breakdown</h4>
                    <div className="space-y-2">
                      {metrics.critical > 0 && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400" />
                            <span className="text-xs text-slate-300">Critical</span>
                          </div>
                          <span className="text-xs font-medium text-red-400">{metrics.critical}</span>
                        </div>
                      )}
                      {metrics.high > 0 && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-orange-400" />
                            <span className="text-xs text-slate-300">High</span>
                          </div>
                          <span className="text-xs font-medium text-orange-400">{metrics.high}</span>
                        </div>
                      )}
                      {metrics.medium > 0 && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-amber-400" />
                            <span className="text-xs text-slate-300">Medium</span>
                          </div>
                          <span className="text-xs font-medium text-amber-400">{metrics.medium}</span>
                        </div>
                      )}
                      {metrics.low > 0 && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-slate-400" />
                            <span className="text-xs text-slate-300">Low</span>
                          </div>
                          <span className="text-xs font-medium text-slate-400">{metrics.low}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions & Patterns */}
                {analysis && (analysis.actions.length > 0 || analysis.patterns.length > 0) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysis.actions.length > 0 && (
                      <div className="p-3 bg-amber-500/5 rounded-lg border border-amber-500/20">
                        <h4 className="text-sm font-semibold text-amber-400 mb-2 flex items-center gap-2">
                          <Zap className="w-4 h-4" />
                          Recommended Actions
                        </h4>
                        <ul className="space-y-1">
                          {analysis.actions.map((action, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="text-amber-400">•</span>
                              {action}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {analysis.patterns.length > 0 && (
                      <div className="p-3 bg-violet-500/5 rounded-lg border border-violet-500/20">
                        <h4 className="text-sm font-semibold text-violet-400 mb-2 flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          Detected Patterns
                        </h4>
                        <ul className="space-y-1">
                          {analysis.patterns.map((pattern, i) => (
                            <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                              <span className="text-violet-400">•</span>
                              {pattern}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* No Items Message */}
                {metrics && metrics.pending === 0 && (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-400/50" />
                    <p className="text-slate-400">No pending escalations</p>
                    <p className="text-xs text-slate-500 mt-1">System operating normally</p>
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

            {/* Items Tab */}
            {selectedTab === 'items' && (
              <div className="space-y-3">
                {items.length === 0 ? (
                  <div className="text-center text-slate-500 py-8">
                    <Inbox className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No items in CEO inbox</p>
                  </div>
                ) : (
                  items
                    .filter(item => item.status === 'Pending')
                    .map((item) => {
                      const isExpanded = expandedItems.has(item.filename);
                      const priorityConfig = getPriorityConfig(item.priority);
                      const PriorityIcon = priorityConfig.icon;

                      return (
                        <div
                          key={item.filename}
                          className={`bg-slate-800/50 rounded-lg border ${priorityConfig.borderColor} overflow-hidden`}
                        >
                          <button
                            onClick={() => toggleItemExpansion(item.filename)}
                            className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className={`${priorityConfig.bgColor} ${priorityConfig.borderColor} p-1.5 rounded`}>
                                <PriorityIcon className={`w-4 h-4 ${priorityConfig.color}`} />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="text-sm font-medium text-slate-200 truncate">
                                  {item.title}
                                </div>
                                <div className="text-xs text-slate-500">
                                  {item.date || 'No date'} • {item.filename}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`text-xs px-2 py-0.5 rounded ${priorityConfig.bgColor} ${priorityConfig.color}`}>
                                {item.priority}
                              </span>
                              {isExpanded ? (
                                <ChevronDown className="w-4 h-4 text-slate-400" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-slate-400" />
                              )}
                            </div>
                          </button>
                          
                          {isExpanded && (
                            <div className="px-4 pb-4 pt-1 border-t border-slate-700/30">
                              <div className="text-sm text-slate-300 mt-2">
                                {item.summary || 'No summary available'}
                              </div>
                              <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
                                <FileText className="w-3 h-3" />
                                <span className="truncate">{item.path}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })
                )}
              </div>
            )}

            {/* History Tab */}
            {selectedTab === 'history' && (
              <div className="space-y-3">
                {items.filter(item => item.status !== 'Pending').length === 0 ? (
                  <div className="text-center text-slate-500 py-8">
                    <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No resolved items yet</p>
                  </div>
                ) : (
                  items
                    .filter(item => item.status !== 'Pending')
                    .map((item) => {
                      const priorityConfig = getPriorityConfig(item.priority);
                      return (
                        <div
                          key={item.filename}
                          className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/30 flex items-center gap-3"
                        >
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-slate-300 truncate">
                              {item.title}
                            </div>
                            <div className="text-xs text-slate-500">
                              {item.date} • Resolved
                            </div>
                          </div>
                          <span className={`text-xs px-2 py-0.5 rounded ${priorityConfig.bgColor} ${priorityConfig.color}`}>
                            {item.priority}
                          </span>
                        </div>
                      );
                    })
                )}
              </div>
            )}

            {/* Actions Tab */}
            {selectedTab === 'actions' && (
              <div className="space-y-4">
                {/* CEO Agent Control */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                  <h4 className="text-sm font-semibold text-slate-300 mb-3">CEO Agent Control</h4>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={spawnCeoAgent}
                      disabled={ceoRunning}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        ceoRunning
                          ? 'bg-emerald-500/20 text-emerald-400 cursor-default'
                          : 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                      }`}
                    >
                      {ceoRunning ? <Crown className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      {ceoRunning ? 'CEO Agent Running' : 'Start CEO Agent'}
                    </button>
                    
                    {ceoRunning && (
                      <span className="text-xs text-emerald-400 flex items-center gap-1">
                        <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                        Active and processing
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    The CEO agent reviews escalations and makes strategic decisions.
                  </p>
                </div>

                {/* Quick Actions */}
                {metrics && metrics.pending > 0 && (
                  <div className="p-3 bg-amber-500/5 rounded-lg border border-amber-500/20">
                    <h4 className="text-sm font-semibold text-amber-400 mb-3">Quick Actions</h4>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={spawnCeoAgent}
                        className="px-3 py-1.5 bg-amber-500/10 text-amber-400 text-xs rounded border border-amber-500/20 hover:bg-amber-500/20 transition-colors"
                      >
                        Process All Escalations
                      </button>
                      <button
                        onClick={() => setSelectedTab('items')}
                        className="px-3 py-1.5 bg-slate-700 text-slate-300 text-xs rounded hover:bg-slate-600 transition-colors"
                      >
                        Review Items
                      </button>
                    </div>
                  </div>
                )}

                {/* System Integration */}
                <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                  <h4 className="text-sm font-semibold text-slate-300 mb-3">System Integration</h4>
                  <div className="space-y-2 text-xs text-slate-400">
                    <div className="flex items-center justify-between">
                      <span>CEO Inbox Directory</span>
                      <span className="text-slate-500">~/.opencode/emergent-learning/ceo-inbox/</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Sync with Alerts</span>
                      <span className="text-emerald-400">Connected</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Auto-escalation</span>
                      <span className="text-emerald-400">Enabled</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      {metrics && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span>Total: {metrics.total}</span>
              <span>Pending: {metrics.pending}</span>
              <span>Resolved: {metrics.resolved}</span>
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
