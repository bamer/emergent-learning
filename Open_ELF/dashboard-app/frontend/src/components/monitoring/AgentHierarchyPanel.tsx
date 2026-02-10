import React, { useState, useEffect, useCallback } from 'react';
import { 
  Eye, Brain, Crown, Activity, AlertTriangle, CheckCircle, 
  Clock, ChevronDown, ChevronRight, RefreshCw, Server
} from 'lucide-react';

interface AgentStatus {
  level: number;
  name: string;
  status: 'healthy' | 'warning' | 'critical' | 'inactive';
  is_running: boolean;
  last_check: string;
  metrics: {
    cycle_count?: number;
    escalations_count?: number;
    ai_analyses_count?: number;
  };
  analysis_summary?: string;
}

interface Escalation {
  id: string;
  from_agent: string;
  to_agent: string;
  severity: 'warning' | 'critical';
  status: 'pending' | 'acknowledged' | 'resolved';
  created_at: string;
  summary: string;
}

interface AgentHierarchyPanelProps {
  apiBaseUrl?: string;
}

const AGENT_CONFIG = {
  sentinel: {
    name: 'Sentinel (Level 1)',
    icon: Eye,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    description: 'Health monitoring, pattern detection, AI analysis every 5min',
  },
  orchestrator: {
    name: 'Orchestrator (Level 2)',
    icon: Brain,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    description: 'Service management, auto-restart, mission coordination',
  },
  ceo: {
    name: 'CEO (Level 3)',
    icon: Crown,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    description: 'Strategic decisions, critical escalation processing',
  },
};

const STATUS_CONFIG = {
  healthy: {
    label: 'Healthy',
    emoji: '✅',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: CheckCircle,
  },
  warning: {
    label: 'Warning',
    emoji: '⚠️',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: AlertTriangle,
  },
  critical: {
    label: 'Critical',
    emoji: '🚨',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    icon: AlertTriangle,
  },
  inactive: {
    label: 'Inactive',
    emoji: '⚪',
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: Clock,
  },
};

export function AgentHierarchyPanel({ apiBaseUrl = '' }: AgentHierarchyPanelProps) {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set(['sentinel']));

  const fetchAgentStatus = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch all agent statuses
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/hierarchy`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setAgents(data.agents || []);
      
      // Fetch recent escalations
      const escResponse = await fetch(`${apiBaseUrl}/api/v1/escalations?limit=10`);
      if (escResponse.ok) {
        const escData = await escResponse.json();
        setEscalations(escData.escalations || []);
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch agent hierarchy:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchAgentStatus();
    
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchAgentStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchAgentStatus, autoRefresh]);

  const toggleAgent = (agentId: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  };

  const formatTime = (timestamp: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (loading && agents.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-slate-500 mx-auto mb-2 animate-spin" />
          <p className="text-slate-400">Loading agent hierarchy...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            Agent Hierarchy
          </h2>
          <p className="text-sm text-slate-400">3-Level monitoring architecture</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-2 rounded-lg text-xs ${autoRefresh ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}
            title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          >
            {autoRefresh ? '⟳ 30s' : '⏸'}
          </button>
          <button
            onClick={fetchAgentStatus}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded-lg"
            title="Refresh now"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">
          <AlertTriangle className="w-4 h-4 inline mr-1" />
          {error}
        </div>
      )}

      {/* Agent Hierarchy */}
      <div className="space-y-3">
        {Object.entries(AGENT_CONFIG).map(([agentId, config]) => {
          const agent = agents.find(a => {
    const nameLower = a.name.toLowerCase();
    if (agentId === 'sentinel') {
      return nameLower.includes('sentinel') || nameLower.includes('sentinel');
    }
    return nameLower.includes(agentId);
  });
          const status = agent?.status || 'inactive';
          const statusConfig = STATUS_CONFIG[status];
          const isExpanded = expandedAgents.has(agentId);
          const Icon = config.icon;
          const StatusIcon = statusConfig.icon;

          // Find escalations for this agent
          const agentEscalations = escalations.filter(
            e => {
              const fromMatch = e.from_agent === agentId || 
                (agentId === 'sentinel' && (e.from_agent === 'sentinel' || e.from_agent === 'sentinel'));
              const toMatch = e.to_agent === agentId || 
                (agentId === 'sentinel' && (e.to_agent === 'sentinel' || e.to_agent === 'sentinel'));
              return fromMatch || toMatch;
            }
          );

          return (
            <div 
              key={agentId}
              className={`rounded-lg border overflow-hidden ${config.bgColor} ${config.borderColor}`}
            >
              {/* Agent Header */}
              <button
                onClick={() => toggleAgent(agentId)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${config.bgColor}`}>
                    <Icon className={`w-5 h-5 ${config.color}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-slate-200">{config.name}</div>
                    <div className="text-xs text-slate-400">{config.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Status Badge */}
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}>
                    <StatusIcon className="w-3 h-3" />
                    <span>{statusConfig.emoji} {statusConfig.label}</span>
                  </div>
                  
                  {/* Escalation Count */}
                  {agentEscalations.length > 0 && (
                    <div className="px-2 py-1 rounded-full text-xs bg-amber-500/20 text-amber-400">
                      {agentEscalations.length} escalations
                    </div>
                  )}
                  
                  {/* Expand/Collapse */}
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {/* Expanded Content */}
              {isExpanded && agent && (
                <div className="px-4 pb-4 border-t border-slate-700/30">
                  {/* Metrics */}
                  <div className="grid grid-cols-3 gap-3 mt-3">
                    <div className="p-2 bg-slate-800/50 rounded text-center">
                      <div className="text-lg font-bold text-slate-200">
                        {agent.metrics?.cycle_count?.toLocaleString() || 0}
                      </div>
                      <div className="text-xs text-slate-500">Cycles</div>
                    </div>
                    <div className="p-2 bg-slate-800/50 rounded text-center">
                      <div className="text-lg font-bold text-slate-200">
                        {agent.metrics?.ai_analyses_count?.toLocaleString() || 0}
                      </div>
                      <div className="text-xs text-slate-500">AI Analyses</div>
                    </div>
                    <div className="p-2 bg-slate-800/50 rounded text-center">
                      <div className={`text-lg font-bold ${agent.metrics?.escalations_count ? 'text-amber-400' : 'text-slate-200'}`}>
                        {agent.metrics?.escalations_count || 0}
                      </div>
                      <div className="text-xs text-slate-500">Escalations</div>
                    </div>
                  </div>

                  {/* Analysis Summary */}
                  {agent.analysis_summary && (
                    <div className="mt-3 p-3 bg-slate-800/50 rounded-lg">
                      <div className="text-xs text-slate-500 mb-1">Latest Analysis</div>
                      <p className="text-sm text-slate-300">{agent.analysis_summary}</p>
                    </div>
                  )}

                  {/* Escalations */}
                  {agentEscalations.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs text-slate-500 mb-2">Recent Escalations</div>
                      <div className="space-y-2">
                        {agentEscalations.slice(0, 3).map((esc) => (
                          <div 
                            key={esc.id}
                            className="p-2 bg-slate-800/50 rounded text-sm"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-slate-300 truncate">{esc.summary}</span>
                              <span className={`px-1.5 py-0.5 rounded text-xs ${
                                esc.severity === 'critical' 
                                  ? 'bg-red-500/20 text-red-400' 
                                  : 'bg-amber-500/20 text-amber-400'
                              }`}>
                                {esc.severity}
                              </span>
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {esc.from_agent} → {esc.to_agent} • {formatTime(esc.created_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Last Check */}
                  <div className="mt-3 text-xs text-slate-500">
                    Last check: {formatTime(agent.last_check)}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Escalation Flow Legend */}
      <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
        <div className="text-sm font-medium text-slate-300 mb-2">Escalation Flow</div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-purple-400">Sentinel (L1)</span>
          <span className="text-slate-500">→</span>
          <span className="text-blue-400">Orchestrator (L2)</span>
          <span className="text-slate-500">→</span>
          <span className="text-amber-400">CEO (L3)</span>
        </div>
        <div className="text-xs text-slate-500 mt-2">
          Sentinel escalates on warning/critical. Orchestrator escalates to CEO only on critical.
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Auto-refresh: {autoRefresh ? '30s' : 'OFF'}</span>
        <span>{agents.length} agents monitored</span>
      </div>
    </div>
  );
}

export default AgentHierarchyPanel;
