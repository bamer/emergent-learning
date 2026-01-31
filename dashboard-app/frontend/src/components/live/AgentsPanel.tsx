// File: AgentsPanel.tsx - Unified Agent Dashboard with ELF + OpenCode Agents
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, RefreshCw, Wifi, WifiOff, Play, Square, Crown, Search, Lightbulb, 
  HelpCircle, Building, Info, X, MessageSquare, Sparkles, Brain, Bot,
  FileSearch, PlusCircle, Users, Zap, Cpu
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  type: string;
  system: 'elf' | 'opencode';
  status: string;
  icon: string;
  role?: string;
  is_primary?: boolean;
  session_id?: string | null;
  last_activity?: string | null;
  start_time?: string | null;
  error_count?: number;
  can_spawn?: boolean;
}

interface AgentStatusResponse {
  timestamp: string;
  orchestrator: {
    running: boolean;
    uptime_seconds: number;
    stats?: {
      total_sessions_created?: number;
      total_messages_sent?: number;
      agents_started?: number;
      agents_stopped?: number;
      errors_handled?: number;
    };
  };
  agents: Agent[];
}

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  provider_id: string;
  is_default: boolean;
  status: string;
}

interface MissionResult {
  status: string;
  mode: string;
  agent_type?: string;
  mission: string;
  response_preview?: string;
  heuristics_count: number;
  execution_time_ms: number;
}

interface AgentsPanelProps {
  apiBaseUrl?: string;
}

const AGENT_ICONS: Record<string, React.ComponentType<any>> = {
  orchestrator: Building,
  sentinel: Search,
  watcher: Activity,
  researcher: FileSearch,
  architect: Lightbulb,
  skeptic: HelpCircle,
  creative: Sparkles,
  ceo: Crown,
  'multi-agent-coordinator': Users,
  'learning-extractor': Brain,
  'swarm-orchestrator': Users,
  default: Bot,
};

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  starting: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  busy: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  error: 'bg-red-500/10 text-red-400 border-red-500/20',
  stopping: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  ready: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  idle: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
};

const STATUS_DISPLAY: Record<string, { text: string; emoji: string }> = {
  running: { text: 'Running', emoji: '🟢' },
  starting: { text: 'Starting', emoji: '🟡' },
  stopped: { text: 'Stopped', emoji: '⚪' },
  busy: { text: 'Busy', emoji: '🔵' },
  error: { text: 'Error', emoji: '🔴' },
  stopping: { text: 'Stopping', emoji: '🟡' },
  ready: { text: 'Ready', emoji: '🔵' },
  idle: { text: 'Idle', emoji: '⚪' },
  completed: { text: 'Completed', emoji: '✅' },
};

// Mission templates
const MISSION_TEMPLATES = [
  { label: 'Clear', icon: X, text: '' },
  { label: 'Analysis', icon: FileSearch, text: 'Analyze the current system state and identify areas for improvement. Provide detailed findings and recommendations.' },
  { label: 'Investigation', icon: Search, text: 'Investigate recent issues or anomalies in the system. Find root causes and propose solutions.' },
  { label: 'New Feature', icon: PlusCircle, text: 'Design and plan a new feature for the system. Include architecture, implementation steps, and potential challenges.' },
  { label: 'Brainstorming', icon: Brain, text: 'Generate creative ideas and innovative approaches for current challenges. Think outside the box and propose unconventional solutions.' },
  { label: 'Swarm', icon: Users, text: 'swarm: Design and implement a complete solution with multi-agent collaboration' },
];

export function AgentsPanel({ apiBaseUrl = '' }: AgentsPanelProps) {
  const [allAgents, setAllAgents] = useState<Agent[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [callingAgent, setCallingAgent] = useState<string | null>(null);
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [missionText, setMissionText] = useState('');
  const [showMissionModal, setShowMissionModal] = useState(false);
  const [executionMode, setExecutionMode] = useState<'smart' | 'auto' | 'swarm' | 'manual'>('smart');
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<MissionResult | null>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // Fetch available models
  const fetchModels = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/models`);
      if (response.ok) {
        const data = await response.json();
        const models = data.models || [];
        setAvailableModels(models);
        
        // Set default model if none selected
        if (!selectedModel && models.length > 0) {
          const defaultModel = models.find((m: ModelInfo) => m.is_default) || models[0];
          setSelectedModel(defaultModel.id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  }, [apiBaseUrl, selectedModel]);

  // Fetch all agents (ELF + OpenCode)
  const fetchAgents = useCallback(async (silent = false) => {
    try {
      // Only show loading on initial load, not on refresh
      if (!silent && isInitialLoad) {
        setLoading(true);
      }
      
      // Fetch ELF agents status
      const statusResponse = await fetch(`${apiBaseUrl}/api/v1/agents/status`);
      let elfAgents: Agent[] = [];
      let statusData: AgentStatusResponse | null = null;
      
      if (statusResponse.ok) {
        statusData = await statusResponse.json();
        setAgentStatus(statusData);
        
        // Get ELF agents from status - map all fields correctly
        elfAgents = (statusData.agents || []).map((agent: any) => ({
          id: agent.agent_type || agent.type || agent.id,
          name: agent.name || agent.display_name || agent.agent_type,
          display_name: agent.display_name || agent.name || agent.agent_type,
          description: agent.description || `${agent.agent_type} agent`,
          type: agent.agent_type || agent.type,
          system: 'elf' as const,
          status: agent.status || 'idle',
          icon: agent.agent_type || agent.type,
          role: agent.role || agent.agent_type,
          is_primary: agent.is_primary,
          session_id: agent.session_id,
          last_activity: agent.last_activity,
          start_time: agent.start_time,
          error_count: agent.error_count || 0,
          can_spawn: agent.status === 'stopped' || agent.status === 'idle' || agent.status === 'completed',
        }));
      }
      
      // Fetch OpenCode agents
      const openCodeResponse = await fetch(`${apiBaseUrl}/api/v1/agents/opencode/list`);
      let openCodeAgents: Agent[] = [];
      
      if (openCodeResponse.ok) {
        const openCodeData = await openCodeResponse.json();
        openCodeAgents = (openCodeData.agents || []).map((agent: any) => ({
          id: agent.id,
          name: agent.name,
          display_name: agent.name,
          type: agent.id,
          system: 'opencode' as const,
          status: 'ready',
          description: agent.description || '',
          icon: agent.id,
          can_spawn: true,
          role: 'Persona',
        }));
      }
      
      // Combine ELF and OpenCode agents
      const combined = [...elfAgents, ...openCodeAgents];
      setAllAgents(combined);
      setError(null);
      
      if (isInitialLoad) {
        setIsInitialLoad(false);
      }
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, [apiBaseUrl, isInitialLoad]);

  // Initial load
  useEffect(() => {
    fetchAgents(false);
    fetchModels();
  }, [fetchAgents, fetchModels]);

  // Silent refresh every 5 seconds (no loading state)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAgents(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  const handleStartAgent = async (agentType: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/spawn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_type: agentType }),
      });
      if (!response.ok) throw new Error(`Failed to start agent: ${response.statusText}`);
      fetchAgents(true);
    } catch (err) {
      console.error('Failed to start agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to start agent');
    }
  };

  const handleStopAgent = async (agentType: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/kill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_type: agentType }),
      });
      if (!response.ok) throw new Error(`Failed to stop agent: ${response.statusText}`);
      fetchAgents(true);
    } catch (err) {
      console.error('Failed to stop agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop agent');
    }
  };

  const handleTestAgent = async (agentType: string) => {
    setCallingAgent(agentType);
    setTestResponse(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_type: agentType }),
      });
      
      if (!response.ok) throw new Error(`Failed to test agent: ${response.statusText}`);
      
      const data = await response.json();
      setTestResponse(data.message || data.response || 'Test completed successfully');
    } catch (err) {
      console.error('Failed to test agent:', err);
      setTestResponse(`Error: ${err instanceof Error ? err.message : 'Failed to test agent'}`);
    } finally {
      setCallingAgent(null);
    }
  };

  const executeMission = async () => {
    if (!missionText.trim()) return;
    
    setIsExecuting(true);
    setLastResult(null);
    
    try {
      const mode = executionMode === 'manual' && selectedAgent ? 'manual' : executionMode;
      
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mission: missionText,
          mode: mode,
          agent_type: selectedAgent?.type,
          model: selectedModel,
        }),
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      
      const result: MissionResult = await response.json();
      setLastResult(result);
      fetchAgents(true);
    } catch (err) {
      console.error('Execution failed:', err);
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleStartClick = (agent?: Agent) => {
    if (agent) {
      setSelectedAgent(agent);
      setExecutionMode('manual');
    } else {
      setSelectedAgent(null);
      setExecutionMode('smart');
    }
    setMissionText('');
    setLastResult(null);
    setShowMissionModal(true);
  };

  const getIconComponent = (agent: Agent) => {
    return AGENT_ICONS[agent.icon] || AGENT_ICONS[agent.type] || AGENT_ICONS.default;
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading agents...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Mission Modal */}
      {showMissionModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Zap className="w-5 h-5 text-violet-400" />
                New Mission
                {selectedAgent && (
                  <span className="text-sm px-2 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                    {selectedAgent.display_name}
                  </span>
                )}
              </h3>
              <button onClick={() => setShowMissionModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Mode Selection */}
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2">Execution Mode</label>
              <div className="flex gap-2 flex-wrap">
                {[
                  { id: 'smart', label: 'Smart', desc: 'Auto-detect if swarm needed' },
                  { id: 'auto', label: 'Auto', desc: 'Select best single agent' },
                  { id: 'swarm', label: 'Swarm', desc: 'Multi-agent parallel' },
                  { id: 'manual', label: 'Manual', desc: 'Specific agent' },
                ].map((mode) => (
                  <button
                    key={mode.id}
                    onClick={() => setExecutionMode(mode.id as any)}
                    disabled={mode.id === 'manual' && !selectedAgent}
                    className={`px-3 py-1.5 rounded text-sm ${
                      executionMode === mode.id
                        ? 'bg-violet-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    } disabled:opacity-50`}
                  >
                    {mode.label}
                    <span className="text-xs opacity-70 ml-1">({mode.desc})</span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">
                <strong>Smart:</strong> Analyzes mission complexity and auto-selects single agent or swarm mode.<br/>
                <strong>Auto:</strong> Always selects the best single agent for the mission.
              </p>
            </div>

            {/* Model Selection */}
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2 flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                Model ({availableModels.length} available)
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
              >
                {availableModels.length === 0 && (
                  <option value="">Loading models...</option>
                )}
                {availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} {model.is_default ? '(default)' : ''} - {model.provider}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Select which AI model will execute this mission
              </p>
            </div>
            
            {/* Mission Templates */}
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2">Quick Templates</label>
              <div className="grid grid-cols-3 gap-2">
                {MISSION_TEMPLATES.map((template) => {
                  const IconComponent = template.icon;
                  return (
                    <button
                      key={template.label}
                      onClick={() => setMissionText(template.text)}
                      className="flex items-center gap-2 p-2 bg-slate-700 hover:bg-slate-600 rounded text-xs transition-colors"
                    >
                      <IconComponent className="w-4 h-4" />
                      <span>{template.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            
            {/* Mission Input */}
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2">Mission</label>
              <textarea
                value={missionText}
                onChange={(e) => setMissionText(e.target.value)}
                placeholder="Describe what you want the agent(s) to do..."
                className="w-full h-32 bg-slate-900 border border-slate-700 rounded p-3 text-sm text-slate-200 placeholder-slate-500 resize-none"
              />
            </div>
            
            {/* Last Result */}
            {lastResult && (
              <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">Execution Complete</span>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <p>Mode: {lastResult.mode}</p>
                  {lastResult.agent_type && <p>Agent: {lastResult.agent_type}</p>}
                  <p>Heuristics: {lastResult.heuristics_count} extracted</p>
                  <p>Time: {(lastResult.execution_time_ms / 1000).toFixed(1)}s</p>
                </div>
                {lastResult.response_preview && (
                  <div className="mt-2 p-2 bg-slate-800 rounded text-xs text-slate-300 max-h-32 overflow-y-auto">
                    <strong>Response:</strong>
                    <p className="mt-1">{lastResult.response_preview}...</p>
                  </div>
                )}
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowMissionModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-sm"
              >
                Close
              </button>
              <button
                onClick={executeMission}
                disabled={!missionText.trim() || isExecuting}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm flex items-center gap-2 disabled:opacity-50"
              >
                {isExecuting ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {isExecuting ? 'Executing...' : 'Execute'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">Agents</h2>
          </div>

          {/* Connection status */}
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${
            !error ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          }`}>
            {!error ? (
              <>
                <Wifi className="w-3 h-3" />
                <span>Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                <span>Disconnected</span>
              </>
            )}
          </div>
        </div>

        {/* Stats */}
        {agentStatus && (
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Running:</span>
              <span className="text-emerald-400 font-semibold">
                {allAgents.filter(a => a.status === 'running').length}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Total:</span>
              <span className="text-violet-400 font-semibold">{allAgents.length}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Uptime:</span>
              <span className="text-cyan-400 font-semibold">
                {formatDuration(agentStatus.orchestrator?.uptime_seconds || 0)}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleStartClick()}
            className="flex items-center gap-2 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded text-sm"
          >
            <PlusCircle className="w-4 h-4" />
            New Mission
          </button>
          <button
            onClick={() => fetchAgents(false)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Connection Error</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={() => fetchAgents(false)}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : allAgents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allAgents.map((agent, index) => {
              const IconComponent = getIconComponent(agent);
              const statusClass = STATUS_COLORS[agent.status] || STATUS_COLORS.stopped;
              const statusDisplay = STATUS_DISPLAY[agent.status] || { text: agent.status, emoji: '⚪' };
              const isElf = agent.system === 'elf';
              
              return (
                <div key={`${agent.system}-${agent.id}-${index}`} className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
                  {/* Agent Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`p-2 rounded-lg ${statusClass}`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                          {agent.display_name}
                          {agent.is_primary && <Crown className="w-3 h-3 text-yellow-400" />}
                          {isElf ? (
                            <span className="text-xs px-1.5 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                              ELF
                            </span>
                          ) : (
                            <span className="text-xs px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                              OC
                            </span>
                          )}
                        </h3>
                        <p className="text-xs text-slate-400">{agent.role || agent.type}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full border ${statusClass}`}>
                      {statusDisplay.emoji} {statusDisplay.text}
                    </span>
                  </div>

                  {/* Agent Info */}
                  <div className="space-y-2 mb-3">
                    <p className="text-sm text-slate-300">{agent.description}</p>
                    
                    {agent.status === 'running' && agent.start_time && (
                      <div className="text-xs text-slate-400">
                        Started: {new Date(agent.start_time).toLocaleTimeString()}
                      </div>
                    )}
                    
                    {agent.error_count && agent.error_count > 0 && (
                      <div className="text-xs text-red-400">
                        Errors: {agent.error_count}
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    {agent.status === 'running' ? (
                      <button
                        onClick={() => handleStopAgent(agent.type)}
                        className="flex items-center gap-1 px-2 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-xs"
                        title="Stop agent"
                      >
                        <Square className="w-3 h-3" />
                        Stop
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStartAgent(agent.type)}
                        className="flex items-center gap-1 px-2 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded text-xs"
                        title="Start agent"
                      >
                        <Play className="w-3 h-3" />
                        Start
                      </button>
                    )}
                    
                    <button
                      onClick={() => handleTestAgent(agent.type)}
                      disabled={callingAgent === agent.type}
                      className="flex items-center gap-1 px-2 py-1 bg-violet-600/20 hover:bg-violet-600/30 text-violet-400 rounded text-xs disabled:opacity-50"
                      title="Test agent"
                    >
                      {callingAgent === agent.type ? (
                        <RefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <Activity className="w-3 h-3" />
                      )}
                      Test
                    </button>

                    <button
                      onClick={() => handleStartClick(agent)}
                      className="flex items-center gap-1 px-2 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded text-xs"
                      title="Send mission"
                    >
                      <MessageSquare className="w-3 h-3" />
                      Mission
                    </button>
                  </div>

                  {/* Test Response */}
                  {testResponse && callingAgent === null && selectedAgent?.id === agent.id && (
                    <div className="mt-3 p-2 bg-slate-700/50 rounded text-xs">
                      <div className="font-semibold text-slate-300 mb-1">Response:</div>
                      <div className="text-slate-400 whitespace-pre-wrap">
                        {testResponse.substring(0, 200)}
                        {testResponse.length > 200 && '...'}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center text-slate-500">No agents available.</div>
        )}
      </div>

      {/* Footer Stats */}
      {agentStatus && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4 text-slate-400">
              <span>ELF: {allAgents.filter(a => a.system === 'elf').length}</span>
              <span>OpenCode: {allAgents.filter(a => a.system === 'opencode').length}</span>
            </div>
            <div className="text-slate-500">
              Last updated: {new Date(agentStatus.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
