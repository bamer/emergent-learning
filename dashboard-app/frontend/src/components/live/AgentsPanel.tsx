// File: AgentsPanel.tsx - Unified Agent Dashboard
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, RefreshCw, Wifi, WifiOff, Play, Square, Crown, Search, Lightbulb, 
  HelpCircle, Building, Info, X, MessageSquare, Sparkles, Brain, ClipboardList,
  FileSearch, PlusCircle
} from 'lucide-react';

interface UnifiedAgent {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  type: string;
  system: 'elf' | 'opencode';
  status: string;
  role?: string;
  is_primary?: boolean;
  icon?: string;
  priority?: number;
  session_id?: string | null;
  last_activity?: string | null;
  start_time?: string | null;
  error_count?: number;
  auto_start?: boolean;
  restart_count?: number;
  can_spawn?: boolean;
}

interface AgentStatusResponse {
  timestamp?: string;
  orchestrator: {
    running: boolean;
    start_time: string | null;
    uptime_seconds: number;
    stats?: {
      agents_started?: number;
      agents_stopped?: number;
      errors_handled?: number;
      uptime_seconds?: number;
    };
  };
  agents: UnifiedAgent[];
  stats?: {
    agents_started: number;
    agents_stopped: number;
    agents_crashed: number;
    errors_handled: number;
    escalations: number;
    uptime_seconds: number;
  };
  escalations?: number;
}

interface OpenCodeAgentRaw {
  id: string;
  name: string;
  description: string;
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
  default: MessageSquare,
};

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  starting: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  busy: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  error: 'bg-red-500/10 text-red-400 border-red-500/20',
  stopping: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  ready: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
};

// Agent descriptions for tooltips
const AGENT_DESCRIPTIONS: Record<string, string> = {
  orchestrator: "Coordination centrale de tous les agents ELF. Gère le cycle de vie des agents et la surveillance.",
  sentinel: "Surveillance continue et détection de patterns. Analyse l'état du système en temps réel.",
  watcher: "Vérifications périodiques et interventions. Surveille les métriques et déclenche des actions.",
  researcher: "Investigation approfondie et collecte d'evidence. Analyse les problèmes complexes.",
  architect: "Conception système et planification structure. Design les solutions techniques.",
  skeptic: "Analyse critique et identification des risques. Challenge les approches proposées.",
  creative: "Innovation et génération de solutions. Propose des idées alternatives et créatives.",
  ceo: "Décisions exécutives et direction stratégique. Prend les décisions finales et gère les escalations.",
  'multi-agent-coordinator': "Coordonne des workflows multi-agents complexes avec gestion des dépendances et tolérance aux pannes.",
  'learning-extractor': "Extrait des insights et patterns d'apprentissage des sessions de travail.",
  'swarm-orchestrator': "Orchestre les swarms d'agents pour des tâches collaboratives.",
};

// Predefined mission templates
const MISSION_TEMPLATES = [
  { label: 'Clear', icon: X, prompt: '' },
  { label: 'Analysis', icon: FileSearch, prompt: 'Analyze the current system state and identify areas for improvement. Provide detailed findings and recommendations.' },
  { label: 'Investigation', icon: Search, prompt: 'Investigate recent issues or anomalies in the system. Find root causes and propose solutions.' },
  { label: 'New Feature', icon: PlusCircle, prompt: 'Design and plan a new feature for the system. Include architecture, implementation steps, and potential challenges.' },
  { label: 'Brainstorming', icon: Brain, prompt: 'Generate creative ideas and innovative approaches for current challenges. Think outside the box and propose unconventional solutions.' },
];

export function AgentsPanel({ apiBaseUrl = '' }: AgentsPanelProps) {
  const [allAgents, setAllAgents] = useState<UnifiedAgent[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [callingAgent, setCallingAgent] = useState<string | null>(null);
  const [testResponse, setTestResponse] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<UnifiedAgent | null>(null);
  const [missionPrompt, setMissionPrompt] = useState('');
  const [showMissionModal, setShowMissionModal] = useState(false);
  const [tooltipAgent, setTooltipAgent] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      // Fetch ELF agents status
      const statusResponse = await fetch(`${apiBaseUrl}/api/v1/agents/status`);
      if (!statusResponse.ok) {
        throw new Error(`HTTP ${statusResponse.status}: ${statusResponse.statusText}`);
      }
      const statusData = await statusResponse.json();
      setAgentStatus(statusData);

      // Fetch OpenCode agents
      const openCodeResponse = await fetch(`${apiBaseUrl}/api/v1/agents/opencode/list`);
      let openCodeAgents: OpenCodeAgentRaw[] = [];
      if (openCodeResponse.ok) {
        const openCodeData = await openCodeResponse.json();
        openCodeAgents = openCodeData.agents || [];
      }

      // Merge agents
      const elfAgents: UnifiedAgent[] = (statusData.agents || []).map((agent: any) => ({
        ...agent,
        id: agent.type,
        system: 'elf' as const,
        can_spawn: !agent.auto_start && agent.status === 'stopped',
      }));

      const ocAgents: UnifiedAgent[] = openCodeAgents.map((agent) => ({
        id: agent.id,
        name: agent.name,
        type: agent.id,
        system: 'opencode' as const,
        status: 'ready', // OpenCode agents are always "ready" as they're personas
        description: agent.description,
        can_spawn: true,
        role: 'Persona',
        is_primary: false,
        error_count: 0,
        session_id: null,
        last_activity: null,
        start_time: null,
      }));

      // Combine and sort alphabetically by name
      const combined = [...elfAgents, ...ocAgents].sort((a, b) => 
        a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
      );

      setAllAgents(combined);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch agent data:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to agent API');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Initial load and refresh
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartAgentClick = (agent: UnifiedAgent) => {
    setSelectedAgent(agent);
    setMissionPrompt('');
    setShowMissionModal(true);
    setActionStatus(null);
  };

  const handleStartAgent = async () => {
    if (!selectedAgent) return;
    
    setActionStatus('starting');
    try {
      let response;
      
      if (selectedAgent.system === 'elf') {
        // Start ELF agent
        response = await fetch(`${apiBaseUrl}/api/v1/agents/spawn`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_type: selectedAgent.type,
            params: missionPrompt ? { mission: missionPrompt } : undefined,
          }),
        });
      } else {
        // Start OpenCode swarm
        response = await fetch(`${apiBaseUrl}/api/v1/agents/opencode/swarm`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task: missionPrompt || `Execute ${selectedAgent.name} persona`,
            mode: 'all',
            context: `Using ${selectedAgent.name} agent from OpenCode`,
            custom_agents: [selectedAgent.id],
          }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to start agent: ${response.statusText}`);
      }

      const result = await response.json();
      setActionStatus('success');
      setShowMissionModal(false);
      setMissionPrompt('');
      setSelectedAgent(null);
      
      // Show success message briefly
      setTimeout(() => setActionStatus(null), 3000);
      
      // Refresh status
      fetchData();
    } catch (err) {
      console.error('Failed to start agent:', err);
      setActionStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to start agent');
    }
  };

  const handleStopAgent = async (agent: UnifiedAgent) => {
    if (agent.system !== 'elf') return; // Can't stop OpenCode agents
    
    setActionStatus('stopping');
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/kill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_type: agent.type, force: false }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to stop agent: ${response.statusText}`);
      }
      
      fetchData();
      setActionStatus(null);
    } catch (err) {
      console.error('Failed to stop agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to stop agent');
      setActionStatus(null);
    }
  };

  const handleTestAgent = async (agent: UnifiedAgent, isDryRun: boolean = false) => {
    if (agent.system !== 'elf') {
      setTestResponse(`OpenCode agents (${agent.name}) are prompt-based personas and don't require testing. They are always ready to use.`);
      return;
    }

    setCallingAgent(agent.id);
    setTestResponse(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: agent.type,
          dry_run: isDryRun,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to test agent: ${response.statusText}`);
      }

      const data = await response.json();
      setTestResponse(data.message || 'Test completed');
    } catch (err) {
      console.error('Failed to test agent:', err);
      setTestResponse(`Error: ${err instanceof Error ? err.message : 'Failed to test agent'}`);
    } finally {
      setCallingAgent(null);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const getIconComponent = (agent: UnifiedAgent) => {
    if (agent.icon && AGENT_ICONS[agent.icon]) {
      return AGENT_ICONS[agent.icon];
    }
    return AGENT_ICONS[agent.type] || AGENT_ICONS.default;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-slate-400 mx-auto animate-spin" />
          <p className="text-slate-500 mt-2">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 text-slate-100 overflow-auto max-h-full">
      {/* Mission Modal */}
      {showMissionModal && selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 w-full max-w-lg mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Play className="w-5 h-5 text-emerald-400" />
                Start Agent: {selectedAgent.name}
                <span className={`text-xs px-2 py-0.5 rounded ${
                  selectedAgent.system === 'elf' ? 'bg-violet-500/20 text-violet-400' : 'bg-blue-500/20 text-blue-400'
                }`}>
                  {selectedAgent.system === 'elf' ? 'ELF' : 'OC'}
                </span>
              </h3>
              <button
                onClick={() => setShowMissionModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm text-slate-400 mb-2">
                Mission / Prompt (optional)
              </label>
              
              {/* Quick template buttons */}
              <div className="grid grid-cols-5 gap-2 mb-3">
                {MISSION_TEMPLATES.map((template) => {
                  const IconComponent = template.icon;
                  return (
                    <button
                      key={template.label}
                      onClick={() => setMissionPrompt(template.prompt)}
                      className="flex flex-col items-center gap-1 p-2 bg-slate-700 hover:bg-slate-600 rounded text-xs transition-colors"
                    >
                      <IconComponent className="w-4 h-4" />
                      <span>{template.label}</span>
                    </button>
                  );
                })}
              </div>
              
              <textarea
                value={missionPrompt}
                onChange={(e) => setMissionPrompt(e.target.value)}
                placeholder="Enter a mission or prompt for the agent..."
                className="w-full h-24 bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 placeholder-slate-500 resize-none"
              />
            </div>

            {/* Status message */}
            {actionStatus && (
              <div className={`mb-4 p-2 rounded text-sm ${
                actionStatus === 'success' ? 'bg-emerald-500/20 text-emerald-400' :
                actionStatus === 'error' ? 'bg-red-500/20 text-red-400' :
                'bg-amber-500/20 text-amber-400'
              }`}>
                {actionStatus === 'starting' && 'Starting agent...'}
                {actionStatus === 'success' && 'Agent started successfully!'}
                {actionStatus === 'error' && 'Failed to start agent. Check console for details.'}
              </div>
            )}

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowMissionModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleStartAgent}
                disabled={actionStatus === 'starting'}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm flex items-center gap-2 disabled:opacity-50"
              >
                {actionStatus === 'starting' ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Start Agent
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Activity className="w-5 h-5 text-violet-400" />
          Agents
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
        </h2>

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

        {/* Refresh button */}
        <button
          onClick={fetchData}
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded"
          title="Refresh agent status"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-red-400 mb-2">Agent API Unavailable</h3>
              <p className="text-slate-400 text-sm mb-4">{error}</p>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry Connection
              </button>
            </div>
          </div>
        ) : allAgents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allAgents.map((agent) => {
              const IconComponent = getIconComponent(agent);
              const statusClass = STATUS_COLORS[agent.status] || STATUS_COLORS.stopped;
              const displayName = agent.display_name || agent.name;
              const isPrimary = agent.is_primary || agent.type === 'ceo' || agent.type === 'orchestrator';
              const description = AGENT_DESCRIPTIONS[agent.type] || agent.description;
              const isRunning = agent.status === 'running';
              const isElf = agent.system === 'elf';

              return (
                <div 
                  key={`${agent.system}-${agent.id}`} 
                  className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4 relative hover:border-slate-600/50 transition-colors"
                  onMouseEnter={() => setTooltipAgent(agent.id)}
                  onMouseLeave={() => setTooltipAgent(null)}
                >
                  {/* Tooltip */}
                  {tooltipAgent === agent.id && description && (
                    <div className="absolute bottom-full left-0 right-0 mb-2 p-3 bg-slate-700 rounded-lg border border-slate-600 shadow-lg z-10">
                      <div className="flex items-start gap-2">
                        <Info className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                        <p className="text-xs text-slate-300">{description}</p>
                      </div>
                      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-slate-700 border-r border-b border-slate-600"></div>
                    </div>
                  )}

                  {/* Agent Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`p-2 rounded-lg ${statusClass}`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                          {displayName}
                          {isPrimary && <Crown className="w-3 h-3 text-yellow-400" />}
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            isElf ? 'bg-violet-500/20 text-violet-400' : 'bg-blue-500/20 text-blue-400'
                          }`}>
                            {isElf ? 'ELF' : 'OC'}
                          </span>
                        </h3>
                        <p className="text-xs text-slate-400 capitalize">{agent.type}</p>
                      </div>
                    </div>
                    <span className={statusClass + ' text-xs px-2 py-1 rounded-full border capitalize'}>
                      {agent.status}
                    </span>
                  </div>

                  {/* Agent Info */}
                  <div className="space-y-2 mb-3 min-h-[40px]">
                    {isElf && isRunning && agent.start_time && (
                      <div className="text-xs text-slate-400">
                        Started: {new Date(agent.start_time).toLocaleTimeString()}
                      </div>
                    )}

                    {isElf && (agent.error_count || 0) > 0 && (
                      <div className="text-xs text-red-400">
                        Errors: {agent.error_count}
                      </div>
                    )}

                    {!isElf && (
                      <div className="text-xs text-blue-400">
                        Prompt-based persona agent
                      </div>
                    )}
                  </div>

                  {/* Action Buttons - Same for all agents */}
                  <div className="flex gap-2 flex-wrap">
                    {isElf ? (
                      // ELF agent controls
                      isRunning ? (
                        <button
                          onClick={() => handleStopAgent(agent)}
                          className="flex items-center gap-1 px-2 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-xs"
                          title="Stop agent"
                        >
                          <Square className="w-3 h-3" />
                          Stop
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartAgentClick(agent)}
                          className="flex items-center gap-1 px-2 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded text-xs"
                          title="Start agent with optional mission"
                        >
                          <Play className="w-3 h-3" />
                          Start
                        </button>
                      )
                    ) : (
                      // OpenCode agent controls
                      <button
                        onClick={() => handleStartAgentClick(agent)}
                        className="flex items-center gap-1 px-2 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded text-xs"
                        title="Activate OpenCode agent"
                      >
                        <Play className="w-3 h-3" />
                        Activate
                      </button>
                    )}

                    {/* Test/Dry-run buttons - only for ELF */}
                    {isElf && (
                      <>
                        <button
                          onClick={() => handleTestAgent(agent, false)}
                          disabled={callingAgent === agent.id || !isRunning}
                          className="flex items-center gap-1 px-2 py-1 bg-violet-600/20 hover:bg-violet-600/30 text-violet-400 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Test agent (requires running)"
                        >
                          {callingAgent === agent.id ? (
                            <RefreshCw className="w-3 h-3 animate-spin" />
                          ) : (
                            <Activity className="w-3 h-3" />
                          )}
                          Test
                        </button>

                        {!isRunning && (
                          <button
                            onClick={() => handleTestAgent(agent, true)}
                            disabled={callingAgent === agent.id}
                            className="flex items-center gap-1 px-2 py-1 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 rounded text-xs disabled:opacity-50"
                            title="Dry-run test (check if agent will work)"
                          >
                            {callingAgent === agent.id ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <HelpCircle className="w-3 h-3" />
                            )}
                            Dry-Run
                          </button>
                        )}
                      </>
                    )}
                  </div>

                  {/* Test Response */}
                  {testResponse && callingAgent === null && (
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
    </div>
  );
}