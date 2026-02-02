import React, { useState } from 'react'
import { Send, AlertTriangle, Star, XCircle, Sparkles, ClipboardList, Play, Square, RefreshCw } from 'lucide-react'
import type { Task, TaskSessions } from './TaskKanban'

interface SignalInputProps {
  sessions: TaskSessions
  selectedTask: Task | null
  totalTasks: number
  onSendNote: (sessionId: string, taskId: string, note: string) => Promise<void>
  onChangeStatus: (sessionId: string, taskId: string, status: string, reason?: string) => Promise<void>
}

export function SignalInput({
  sessions,
  selectedTask,
  totalTasks,
  onSendNote,
  onChangeStatus,
}: SignalInputProps) {
  const [noteText, setNoteText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [manualSessionId, setManualSessionId] = useState<string>('')
  const [manualTaskId, setManualTaskId] = useState<string>('')

  const sessionIds = Object.keys(sessions)
  const currentSessionId = selectedTask?.session_id || manualSessionId
  const currentTaskId = selectedTask?.id || manualTaskId

  const currentSessionTasks = currentSessionId ? sessions[currentSessionId] || [] : []

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!noteText.trim() || !currentSessionId || !currentTaskId) return

    setIsSubmitting(true)
    try {
      await onSendNote(currentSessionId, currentTaskId, noteText.trim())
      setNoteText('')
    } catch (err) {
      console.error('Failed to send note:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleQuickAction = async (status: string) => {
    if (!currentSessionId || !currentTaskId) return

    const reason = status === 'blocked' ? 'Marked blocked from dashboard' :
                   status === 'cancelled' ? 'Cancelled from dashboard' :
                   undefined

    setIsSubmitting(true)
    try {
      await onChangeStatus(currentSessionId, currentTaskId, status, reason)
    } catch (err) {
      console.error('Failed to change status:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = noteText.trim() && currentSessionId && currentTaskId && !isSubmitting

  return (
    <div className="border-t border-slate-700/50 bg-slate-900/50 p-3">
      {/* Task Selection (when no task selected) */}
      {!selectedTask && (
        <div className="flex items-center gap-2 mb-3">
          <select
            value={manualSessionId}
            onChange={(e) => {
              setManualSessionId(e.target.value)
              setManualTaskId('')
            }}
            className="text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-slate-300 focus:outline-none focus:border-violet-500 flex-1"
          >
            <option value="">Select session...</option>
            {sessionIds.map(id => {
              const sessionTasks = sessions[id]
              const sessionName = sessionTasks[0]?.session_name || id.slice(0, 8) + '...'
              return (
                <option key={id} value={id}>
                  {sessionName} ({sessionTasks.length} tasks)
                </option>
              )
            })}
          </select>

          <select
            value={manualTaskId}
            onChange={(e) => setManualTaskId(e.target.value)}
            disabled={!manualSessionId}
            className="text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-slate-300 focus:outline-none focus:border-violet-500 flex-1 disabled:opacity-50"
          >
            <option value="">Select task...</option>
            {currentSessionTasks.map(task => (
              <option key={task.id} value={task.id}>
                #{task.id}: {task.subject.slice(0, 30)}...
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Selected Task Info */}
      {(selectedTask || (manualSessionId && manualTaskId)) && (
        <div className="mb-3 px-2 py-1.5 bg-slate-800/50 rounded text-xs">
          <span className="text-slate-500">Target: </span>
          <span className="text-violet-400">
            #{currentTaskId}
          </span>
          <span className="text-slate-500"> in </span>
          <span className="text-slate-400 font-mono">
            {currentSessionId?.slice(0, 8)}...
          </span>
        </div>
      )}

      {/* Getting Started Panel - shown when no tasks exist */}
      {totalTasks === 0 && (
        <div className="mb-3 p-4 bg-gradient-to-br from-violet-500/10 to-cyan-500/10 border border-violet-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Sparkles className="w-5 h-5 text-violet-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-slate-200 mb-1">
                Getting Started with Tasks
              </h4>
              <p className="text-xs text-slate-400 mb-2">
                No active tasks found. Tasks appear here when ELF agents are running with task tracking enabled.
              </p>
              <div className="flex items-center gap-2 text-[10px] text-slate-500">
                <ClipboardList className="w-3 h-3" />
                <span>Use <code className="bg-slate-800 px-1 rounded">/swarm</code> or <code className="bg-slate-800 px-1 rounded">delegate_task()</code> to create tracked tasks</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hint when tasks exist but nothing selected */}
      {totalTasks > 0 && !selectedTask && !manualSessionId && (
        <div className="mb-2 px-2 py-1.5 bg-slate-800/30 border border-slate-700/30 rounded text-xs text-slate-500">
          💡 Click a task in the Kanban board above, or select a session and task from the dropdowns
        </div>
      )}

      {/* Note Input */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          type="text"
          value={noteText}
          onChange={(e) => setNoteText(e.target.value)}
          placeholder={currentTaskId ? "Add a note to this task..." : "Select a task first..."}
          disabled={!currentSessionId || !currentTaskId || isSubmitting}
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-violet-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!canSubmit}
          className="p-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:opacity-50 rounded-lg transition-colors"
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </form>

      {/* Quick Actions */}
      {(currentSessionId && currentTaskId) && (
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">Quick:</span>
          
          {/* Start button - for pending/blocked tasks */}
          {selectedTask?.status === 'pending' || selectedTask?.status === 'blocked' ? (
            <button
              onClick={() => handleQuickAction('in_progress')}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded border border-emerald-500/30 transition-colors disabled:opacity-50"
            >
              <Play className="w-3 h-3" />
              Start
            </button>
          ) : null}
          
          {/* Stop button - for in_progress tasks */}
          {selectedTask?.status === 'in_progress' ? (
            <button
              onClick={() => handleQuickAction('blocked')}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded border border-red-500/30 transition-colors disabled:opacity-50"
            >
              <Square className="w-3 h-3" />
              Stop
            </button>
          ) : null}
          
          {/* Relaunch button - for completed/cancelled tasks */}
          {selectedTask?.status === 'completed' || selectedTask?.status === 'cancelled' ? (
            <button
              onClick={() => handleQuickAction('in_progress')}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-2 py-1 text-xs bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 rounded border border-violet-500/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw className="w-3 h-3" />
              Relaunch
            </button>
          ) : null}
          
          <button
            onClick={() => handleQuickAction('blocked')}
            disabled={isSubmitting}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded border border-amber-500/30 transition-colors disabled:opacity-50"
          >
            <AlertTriangle className="w-3 h-3" />
            Mark Blocked
          </button>
          <button
            onClick={() => handleQuickAction('cancelled')}
            disabled={isSubmitting}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded border border-red-500/30 transition-colors disabled:opacity-50"
          >
            <XCircle className="w-3 h-3" />
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
