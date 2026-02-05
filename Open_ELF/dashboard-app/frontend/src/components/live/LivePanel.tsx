import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Activity, RefreshCw, Wifi, WifiOff, PlusCircle, Play } from 'lucide-react'
import { TaskKanban, Task, TaskSessions } from './TaskKanban'
import { TrailFeed, Trail } from './TrailFeed'
import { SignalInput } from './SignalInput'
import { AgentsPanel } from './AgentsPanel'

interface LivePanelProps {
  apiBaseUrl?: string
}

export function LivePanel({ apiBaseUrl = '' }: LivePanelProps) {
  const [taskSessions, setTaskSessions] = useState<TaskSessions>({})
  const [trails, setTrails] = useState<Trail[]>([])
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [taskConnected, setTaskConnected] = useState(false)
  const [trailConnected, setTrailConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'agents' | 'tasks'>('agents')
  const [watcherStatus, setWatcherStatus] = useState<{running: boolean; state?: string}>({running: false})

  const taskEventSourceRef = useRef<EventSource | null>(null)
  const trailEventSourceRef = useRef<EventSource | null>(null)

  // Connect to task SSE
  useEffect(() => {
    const connectTaskSSE = () => {
      const eventSource = new EventSource(`${apiBaseUrl}/api/v1/live/tasks`)
      taskEventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setTaskConnected(true)
        setError(null)
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'initial' || data.type === 'update') {
            setTaskSessions(data.sessions || {})
          } else if (data.type === 'error') {
            console.error('Task SSE error:', data.message)
          }
        } catch (err) {
          console.error('Failed to parse task SSE data:', err)
        }
      }

      eventSource.onerror = () => {
        setTaskConnected(false)
        eventSource.close()

        // Reconnect after 3 seconds
        setTimeout(connectTaskSSE, 3000)
      }
    }

    connectTaskSSE()

    return () => {
      if (taskEventSourceRef.current) {
        taskEventSourceRef.current.close()
      }
    }
  }, [apiBaseUrl])

  // Connect to trail SSE
  useEffect(() => {
    const connectTrailSSE = () => {
      const eventSource = new EventSource(`${apiBaseUrl}/api/v1/live/trails`)
      trailEventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setTrailConnected(true)
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'initial') {
            setTrails(data.trails || [])
          } else if (data.type === 'new_trails') {
            setTrails(prev => [...data.trails, ...prev])
          }
        } catch (err) {
          console.error('Failed to parse trail SSE data:', err)
        }
      }

      eventSource.onerror = () => {
        setTrailConnected(false)
        eventSource.close()

        // Reconnect after 3 seconds
        setTimeout(connectTrailSSE, 3000)
      }
    }

    connectTrailSSE()

    return () => {
      if (trailEventSourceRef.current) {
        trailEventSourceRef.current.close()
      }
    }
  }, [apiBaseUrl])

  // Send note to task
  const handleSendNote = useCallback(async (sessionId: string, taskId: string, note: string) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/live/signal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        task_id: taskId,
        note_text: note,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to send note')
    }
  }, [apiBaseUrl])

  // Change task status
  const handleChangeStatus = useCallback(async (
    sessionId: string,
    taskId: string,
    status: string,
    reason?: string
  ) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/live/task/${sessionId}/${taskId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reason }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to change status')
    }
  }, [apiBaseUrl])

  // Calculate active agent count
  const activeSessions = Object.keys(taskSessions).length
  const totalTasks = Object.values(taskSessions).flat().length
  const inProgressTasks = Object.values(taskSessions).flat().filter(t => t.status === 'in_progress').length
  const [trailFeedCollapsed, setTrailFeedCollapsed] = useState(false)
  
  // Task action handlers
  const handleTaskStart = useCallback(async (sessionId: string, taskId: string) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/live/task/${sessionId}/${taskId}/start`, {
      method: 'POST',
    })
    if (response.ok) {
      // Refresh will trigger auto-update via SSE
      console.info(`Started task ${taskId} in session ${sessionId}`)
    }
  }, [apiBaseUrl])
  
  const handleTaskStop = useCallback(async (sessionId: string, taskId: string) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/live/task/${sessionId}/${taskId}/stop`, {
      method: 'POST',
    })
    if (response.ok) {
      console.info(`Stopped task ${taskId} in session ${sessionId}`)
    }
  }, [apiBaseUrl])
  
  const handleTaskRelaunch = useCallback(async (sessionId: string, taskId: string) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/live/task/${sessionId}/${taskId}/relaunch`, {
      method: 'POST',
    })
    if (response.ok) {
      console.info(`Relaunched task ${taskId} in session ${sessionId}`)
    }
  }, [apiBaseUrl])

  const handleLaunchWatcher = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/watcher/start`, {
        method: 'POST',
      })
      if (response.ok) {
        const data = await response.json();
        console.info('Watcher launched:', data.message || 'Started');
        // Refresh status after launching
        setTimeout(fetchWatcherStatus, 1000);
      }
    } catch (err) {
      console.error('Failed to launch watcher:', err);
    }
  }, [apiBaseUrl])

  // Fetch watcher status
  const fetchWatcherStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/watcher/status`);
      if (response.ok) {
        const data = await response.json();
        setWatcherStatus({
          running: data.status?.running || false,
          state: data.status?.state || 'unknown'
        });
      }
    } catch (err) {
      console.debug('Failed to fetch watcher status:', err);
      setWatcherStatus({running: false, state: 'unknown'});
    }
  }, [apiBaseUrl]);

  // Poll watcher status every 5 seconds
  useEffect(() => {
    fetchWatcherStatus();
    const interval = setInterval(fetchWatcherStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchWatcherStatus]);
  
  const isConnected = taskConnected && trailConnected
  
  return (
    <div className="h-full flex flex-col bg-slate-900/30 rounded-lg border border-slate-700/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-slate-200">Live System</h2>
          </div>

          {/* View Mode Toggle */}
          <div className="flex bg-slate-800/50 rounded-lg p-1">
            <button
              onClick={() => setViewMode('agents')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                viewMode === 'agents'
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ELF Agents
            </button>
            <button
              onClick={() => setViewMode('tasks')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                viewMode === 'tasks'
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tasks & Trails
            </button>
          </div>
        </div>

        {/* Connection status */}
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${
          viewMode === 'agents' ? 'hidden' : (
            isConnected
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-red-500/10 text-red-400'
          )
        }`}>
          {isConnected ? (
            <>
              <Wifi className="w-3 h-3" />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3" />
              <span>Reconnecting...</span>
            </>
          )}
        </div>

        {/* Watcher status/button - visible in Tasks view */}
        {viewMode === 'tasks' && (
          watcherStatus.running ? (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-xs font-medium border border-emerald-500/20">
              <Activity className="w-3.5 h-3.5 animate-pulse" />
              <span>Watcher {watcherStatus.state || 'Running'}</span>
            </div>
          ) : (
            <button
              onClick={handleLaunchWatcher}
              className="flex items-center gap-1.5 px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-xs font-medium transition-colors"
              title="Launch Log Watcher"
            >
              <Play className="w-3.5 h-3.5" />
              <span className="ml-1">Launch Watcher</span>
            </button>
          )
        )}

        {/* Stats for tasks view */}
        {viewMode === 'tasks' && (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500">Sessions:</span>
                <span className="text-violet-400 font-semibold">{activeSessions}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500">Tasks:</span>
                <span className="text-cyan-400 font-semibold">{totalTasks}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500">Active:</span>
                <span className="text-emerald-400 font-semibold">{inProgressTasks}</span>
              </div>
            </div>
            
            {/* New Mission Button for Tasks View */}
            <button
              onClick={() => {
                // Switch to agents view and open mission modal
                setViewMode('agents')
                // The AgentsPanel will need to handle opening the modal
                // We'll dispatch a custom event
                window.dispatchEvent(new CustomEvent('openNewMissionModal'))
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-700 text-white rounded text-xs font-medium transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              New Mission
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'agents' ? (
          <AgentsPanel apiBaseUrl={apiBaseUrl} />
        ) : (
          <div className="flex h-full overflow-hidden">
            {/* Left: Task Kanban with Signal Input at top */}
            <div className="flex-[3] flex flex-col min-w-0 overflow-hidden">
              {/* Top: Signal Input for easy access to session/task selection */}
              <div className="flex-shrink-0 border-b border-slate-700/50">
                <SignalInput
                  sessions={taskSessions}
                  selectedTask={selectedTask}
                  totalTasks={totalTasks}
                  onSendNote={handleSendNote}
                  onChangeStatus={handleChangeStatus}
                />
              </div>

              {/* Bottom: Task Kanban - fills remaining height */}
              <div className="flex-1 p-4 overflow-hidden">
                <TaskKanban
                  sessions={taskSessions}
                  selectedSession={selectedSession}
                  onSessionSelect={setSelectedSession}
                  onTaskSelect={setSelectedTask}
                  selectedTask={selectedTask}
                  onStartTask={handleTaskStart}
                  onStopTask={handleTaskStop}
                  onRelaunchTask={handleTaskRelaunch}
                />
              </div>
            </div>

            {/* Right: Trail Feed - collapsible */}
            <div className={`border-l border-slate-700/50 flex flex-col relative transition-all duration-300 ${
              trailFeedCollapsed ? 'w-12' : 'flex-[1] min-w-[260px] max-w-[360px]'
            }`}>
              <TrailFeed
                trails={trails}
                autoScroll={autoScroll}
                onAutoScrollChange={setAutoScroll}
                collapsed={trailFeedCollapsed}
                onToggleCollapse={() => setTrailFeedCollapsed(!trailFeedCollapsed)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Toast */}
      {error && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 px-4 py-2 bg-red-500/90 text-white text-sm rounded-lg shadow-lg">
          {error}
        </div>
      )}
    </div>
  )
}
