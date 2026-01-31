import React, { useState, useEffect, useCallback } from 'react'
import { Activity, RefreshCw, Wifi, WifiOff, Play, Square, Crown, Search, Lightbulb, HelpCircle, Building } from 'lucide-react'
// import { useAPI } from '../../hooks'

interface AgentInfo {
  type: string
  name: string
  display_name: string
  description: string
  icon: string
  role: string
  is_primary: boolean
  status: string
  priority: number
  session_id: string | null
  last_activity: string | null
  start_time: string | null
  error_count: number
  auto_start: boolean
  status_display: {
    text: string
    color: string
    emoji: string
  }
}

interface AgentStatusResponse {
  timestamp: string
  orchestrator: {
    running: boolean
    uptime_seconds: number
    stats: {
      total_sessions_created: number
      total_messages_sent: number
      agents_started: number
      agents_stopped: number
      errors_handled: number
      uptime_seconds: number
    }
  }
  agents: AgentInfo[]
}

interface AgentsPanelProps {
  apiBaseUrl?: string
}

const AGENT_ICONS = {
  orchestrator: Building,
  sentinel: Search,
  researcher: Activity,
  architect: Lightbulb,
  skeptic: HelpCircle,
  creative: Lightbulb,
  ceo: Crown,
}

const STATUS_COLORS = {
  running: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  starting: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  busy: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  error: 'bg-red-500/10 text-red-400 border-red-500/20',
  stopping: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

export function AgentsPanel({ apiBaseUrl = 'http://localhost:8888' }: AgentsPanelProps) {
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [callingAgent, setCallingAgent] = useState<string | null>(null)
  const [testResponse, setTestResponse] = useState<string | null>(null)
  // const api = useAPI()

  const fetchAgentStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents/status`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setAgentStatus(data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch agent status:', err)
      setError(err instanceof Error ? err.message : 'Failed to connect to agent API')
      setAgentStatus(null)
    } finally {
      setLoading(false)
    }
  }, [apiBaseUrl])

  // Initial load and refresh
  useEffect(() => {
    fetchAgentStatus()
    const interval = setInterval(fetchAgentStatus, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [fetchAgentStatus])

  const handleStartAgent = async (agentType: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents/start/${agentType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        throw new Error(`Failed to start agent: ${response.statusText}`)
      }
      fetchAgentStatus() // Refresh status
    } catch (err) {
      console.error('Failed to start agent:', err)
      setError(err instanceof Error ? err.message : 'Failed to start agent')
    }
  }

  const handleStopAgent = async (agentType: string) => {
    try {
      const response = await fetch(`${apiBaseUrl}/agents/stop/${agentType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        throw new Error(`Failed to stop agent: ${response.statusText}`)
      }
      fetchAgentStatus() // Refresh status
    } catch (err) {
      console.error('Failed to stop agent:', err)
      setError(err instanceof Error ? err.message : 'Failed to stop agent')
    }
  }

  const handleTestAgent = async (agentType: string) => {
    setCallingAgent(agentType)
    setTestResponse(null)
    
    try {
      const prompts = {
        sentinel: "Analyze the current system health and report any issues.",
        researcher: "Investigate the latest system patterns and provide insights.",
        architect: "Design a solution for the current coordination challenges.",
        skeptic: "Review the current system for potential risks and issues.",
        creative: "Suggest innovative improvements to the agent system.",
        ceo: "Make an executive decision about the current system priorities.",
        orchestrator: "Report on the overall system coordination status.",
      }

      const response = await fetch(`${apiBaseUrl}/agents/call/${agentType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompts[agentType as keyof typeof prompts] || "Report your current status.",
          timeout: 30000
        }),
      })
      
      if (!response.ok) {
        throw new Error(`Failed to call agent: ${response.statusText}`)
      }
      
      const data = await response.json()
      setTestResponse(data.response || 'No response received')
    } catch (err) {
      console.error('Failed to call agent:', err)
      setTestResponse(`Error: ${err instanceof Error ? err.message : 'Failed to call agent'}`)
    } finally {
      setCallingAgent(null)
    }
  }

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-900/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading agents...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">ELF Agents</h2>
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
                {agentStatus.agents.filter(a => a.status === 'running').length}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Total:</span>
              <span className="text-violet-400 font-semibold">{agentStatus.agents.length}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Uptime:</span>
              <span className="text-cyan-400 font-semibold">
                {formatDuration(agentStatus.orchestrator.uptime_seconds)}
              </span>
            </div>
          </div>
        )}

        {/* Refresh button */}
        <button
          onClick={fetchAgentStatus}
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
                onClick={fetchAgentStatus}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
              >
                Retry Connection
              </button>
            </div>
          </div>
        ) : agentStatus ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentStatus.agents.map((agent) => {
              const IconComponent = AGENT_ICONS[agent.type as keyof typeof AGENT_ICONS] || Activity
              const statusClass = STATUS_COLORS[agent.status as keyof typeof STATUS_COLORS] || STATUS_COLORS.stopped
              
              return (
                <div key={agent.type} className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
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
                        </h3>
                        <p className="text-xs text-slate-400">{agent.role}</p>
                      </div>
                    </div>
                    <span className={statusClass + ' text-xs px-2 py-1 rounded-full border'}>
                      {agent.status_display.text}
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
                    
                    {agent.error_count > 0 && (
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
                      disabled={callingAgent === agent.type || agent.status !== 'running'}
                      className="flex items-center gap-1 px-2 py-1 bg-violet-600/20 hover:bg-violet-600/30 text-violet-400 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Test agent"
                    >
                      {callingAgent === agent.type ? (
                        <RefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <Activity className="w-3 h-3" />
                      )}
                      Test
                    </button>
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
              )
            })}
          </div>
        ) : null}
      </div>

      {/* Orchestrator Stats Footer */}
      {agentStatus && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4 text-slate-400">
              <span>Sessions: {agentStatus.orchestrator.stats.total_sessions_created}</span>
              <span>Messages: {agentStatus.orchestrator.stats.total_messages_sent}</span>
              <span>Started: {agentStatus.orchestrator.stats.agents_started}</span>
            </div>
            <div className="text-slate-500">
              Last updated: {new Date(agentStatus.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}