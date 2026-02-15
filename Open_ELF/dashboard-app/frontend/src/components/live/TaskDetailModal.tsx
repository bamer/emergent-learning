import React, { createPortal } from 'react-dom';
import { X, AlertCircle, Activity, CheckCircle2, FileText, Calendar, Clock, Bug, Terminal, ExternalLink, RefreshCw, Archive } from 'lucide-react';

interface TaskDetailModalProps {
  isOpen: boolean;
  task: Task | null;
  onClose: () => void;
  apiBaseUrl: string;
  onEscalate?: (taskId: string) => void;
  onArchive?: (taskId: string) => void;
  onRestart?: (taskId: string) => void;
}

interface Task {
  id: string
  subject: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked' | 'cancelled' | 'error' | 'failed'
  activeForm?: string
  blocks?: string[]
  blockedBy?: string[]
  notes?: Array<{ text: string; timestamp: string; source: string }>
  output?: string
  result?: string
  session_id: string
  session_name?: string
  creation_time?: string
  updated_time?: string
  archived?: boolean
  archived_at?: string
}

export function TaskDetailModal({ isOpen, task, onClose, apiBaseUrl, onEscalate, onArchive, onRestart }: TaskDetailModalProps) {
  if (!isOpen || !task) return null;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const statusColors: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
    pending: { bg: 'bg-slate-500/10', text: 'text-slate-400', icon: Clock },
    in_progress: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', icon: Activity },
    completed: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', icon: CheckCircle2 },
    blocked: { bg: 'bg-amber-500/10', text: 'text-amber-400', icon: AlertCircle },
    cancelled: { bg: 'bg-red-500/10', text: 'text-red-400', icon: X },
    error: { bg: 'bg-red-500/10', text: 'text-red-400', icon: Bug },
    failed: { bg: 'bg-red-500/10', text: 'text-red-400', icon: AlertCircle },
  };

  const statusInfo = statusColors[task.status] || statusColors.pending;
  const StatusIcon = statusInfo.icon;

  const handleEscalate = () => {
    if (onEscalate && task.id) {
      onEscalate(task.id);
    }
  };

  const handleArchive = () => {
    if (onArchive && task.id) {
      onArchive(task.id);
    }
  };

  const handleRestart = () => {
    if (onRestart && task.id) {
      onRestart(task.id);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[9999] overflow-hidden flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gray-900/90 backdrop-blur-sm animate-in fade-in" onClick={onClose} />
      <div className="relative w-full max-w-5xl max-h-[90vh] bg-slate-900 shadow-2xl animate-in zoom-in-95 overflow-hidden flex flex-col rounded-lg border border-slate-700">
        {/* Header */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusIcon className={`w-6 h-6 ${statusInfo.text}`} />
              <h2 className="text-xl font-bold text-white">Mission Details</h2>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
              <X className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
          </div>
          <div className="mt-2">
            <h3 className="text-sm font-medium text-emerald-400">{task.subject}</h3>
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
            <span>Session: {task.session_name || task.session_id}</span>
            <span>Status: <span className={`${statusInfo.bg} ${statusInfo.text} px-2 py-1 rounded font-medium`}>{task.status}</span></span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Description */}
          {task.description && (
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-slate-400" />
                <h4 className="text-sm font-semibold text-white">Description</h4>
              </div>
              <div className="text-sm text-slate-300 whitespace-pre-wrap">
                {task.description}
              </div>
            </div>
          )}

          {/* Active Form / State */}
          {task.activeForm && (
            <div className="p-4 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h4 className="text-sm font-semibold text-cyan-300">Active State</h4>
              </div>
              <div className="text-sm text-cyan-200">
                {task.activeForm}
              </div>
            </div>
          )}

          {/* Output / Result */}
          {(task.output || task.result) && (
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <Terminal className="w-4 h-4 text-slate-400" />
                <h4 className="text-sm font-semibold text-white">
                  {task.status === 'error' || task.status === 'failed' ? 'Error / Conclusion' : 'Output'}
                </h4>
              </div>
              <div className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded font-mono whitespace-pre-wrap overflow-x-auto max-h-64">
                {(task.status === 'error' || task.status === 'failed') ? task.result || task.output : task.output || task.result}
              </div>
            </div>
          )}

          {/* Notes Timeline */}
          {task.notes && task.notes.length > 0 && (
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-slate-400" />
                <h4 className="text-sm font-semibold text-white">Execution Log ({task.notes.length} entries)</h4>
              </div>
              <div className="space-y-2">
                {task.notes.map((note, idx) => (
                  <div key={idx} className="flex gap-2 text-sm">
                    <span className="text-slate-500 whitespace-nowrap text-xs">
                      {formatDate(note.timestamp)}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      note.source === 'error'
                        ? 'bg-red-500/20 text-red-400'
                        : note.source === 'warning'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-slate-600 text-slate-300'
                    }`}>
                      {note.source}
                    </span>
                    <span className="text-slate-300">{note.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Blocked By */}
          {task.blockedBy && task.blockedBy.length > 0 && (
            <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/30">
              <div className="flex items-center gap-2 mb-3">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <h4 className="text-sm font-semibold text-amber-300">Blocked By ({task.blockedBy.length})</h4>
              </div>
              <ul className="list-disc list-inside pl-4 space-y-1 text-sm text-amber-200">
                {task.blockedBy.map((id, idx) => (
                  <li key={idx} className="text-slate-400">
                    Waiting for: {id}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Blocks */}
          {task.blocks && task.blocks.length > 0 && (
            <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <div className="flex items-center gap-2 mb-3">
                <ExternalLink className="w-4 h-4 text-purple-400" />
                <h4 className="text-sm font-semibold text-purple-300">Blocking ({task.blocks.length} tasks)</h4>
              </div>
              <ul className="list-disc list-inside pl-4 space-y-1 text-sm text-purple-200">
                {task.blocks.map((id, idx) => (
                  <li key={idx} className="text-slate-400">
                    Blocking: {id}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer with Actions */}
        <div className="p-6 border-t border-slate-700 space-y-3">
          {/* Restart Button - For blocked tasks */}
          {(task.status === 'blocked' || task.status === 'error') && onRestart && (
            <button
              onClick={handleRestart}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-lg transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              Restart Task
            </button>
          )}

          {/* Escalate Button - For blocked tasks */}
          {(task.status === 'blocked') && onEscalate && (
            <button
              onClick={handleEscalate}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-violet-600 hover:bg-violet-700 text-white font-medium rounded-lg transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              Escalate to Orchestrator
            </button>
          )}

          {/* Archive Button - For completed/failed/error tasks */}
          {(task.status === 'completed' || task.status === 'error' || task.status === 'failed') && onArchive && (
            <button
              onClick={handleArchive}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 text-slate-300 font-medium rounded-lg transition-all"
            >
              <Archive className="w-4 h-4" />
              Archive from Kanban
            </button>
          )}

          {/* Close Button */}
          <button
            onClick={onClose}
            className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-transparent border border-slate-600 hover:border-slate-500 text-slate-400 hover:text-slate-300 font-medium rounded-lg transition-all"
          >
            <X className="w-4 h-4" />
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
