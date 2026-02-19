import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// Task types
interface GanttTask {
  id: string
  name: string
  start: Date
  end: Date
  progress: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  assignee?: string
}

// Generate sample Gantt data
const generateGanttData = (): GanttTask[] => {
  const now = new Date()
  const tasks: GanttTask[] = [
    {
      id: '1',
      name: 'Initialize Orchestrator',
      start: new Date(now.getTime() - 120 * 60000),
      end: new Date(now.getTime() - 100 * 60000),
      progress: 100,
      status: 'completed',
      assignee: 'System'
    },
    {
      id: '2',
      name: 'Load Heuristics',
      start: new Date(now.getTime() - 100 * 60000),
      end: new Date(now.getTime() - 80 * 60000),
      progress: 100,
      status: 'completed',
      assignee: 'Memory'
    },
    {
      id: '3',
      name: 'Analyze Patterns',
      start: new Date(now.getTime() - 80 * 60000),
      end: new Date(now.getTime() - 40 * 60000),
      progress: 100,
      status: 'completed',
      assignee: 'Research Agent'
    },
    {
      id: '4',
      name: 'Generate Insights',
      start: new Date(now.getTime() - 40 * 60000),
      end: new Date(now.getTime() - 10 * 60000),
      progress: 85,
      status: 'running',
      assignee: 'Analysis Agent'
    },
    {
      id: '5',
      name: 'Validate Results',
      start: new Date(now.getTime() - 10 * 60000),
      end: new Date(now.getTime() + 30 * 60000),
      progress: 0,
      status: 'pending',
      assignee: 'Validation Agent'
    },
    {
      id: '6',
      name: 'Update Knowledge',
      start: new Date(now.getTime() + 30 * 60000),
      end: new Date(now.getTime() + 60 * 60000),
      progress: 0,
      status: 'pending',
      assignee: 'Knowledge Base'
    },
  ]
  return tasks
}

// Status colors
const statusColors: Record<GanttTask['status'], string> = {
  pending: '#64748b',
  running: '#3b82f6',
  completed: '#10b981',
  failed: '#ef4444'
}

// Format duration
function formatDuration(start: Date, end: Date): string {
  const diff = end.getTime() - start.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  }
  return `${minutes}m`
}

// Format time
function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
}

// Main Gantt Chart component
interface GanttChartProps {
  data?: GanttTask[]
  onTaskSelect?: (task: GanttTask) => void
}

export function GanttChart({ data, onTaskSelect }: GanttChartProps) {
  const [selectedTask, setSelectedTask] = useState<GanttTask | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  
  const tasks = useMemo(() => data || generateGanttData(), [data])
  
  // Calculate timeline bounds
  const timeRange = useMemo(() => {
    const starts = tasks.map(t => t.start.getTime())
    const ends = tasks.map(t => t.end.getTime())
    const minTime = Math.min(...starts) - 30 * 60000 // 30 min padding
    const maxTime = Math.max(...ends) + 30 * 60000
    return { start: minTime, end: maxTime, duration: maxTime - minTime }
  }, [tasks])
  
  const handleTaskClick = (task: GanttTask) => {
    setSelectedTask(task)
    setShowDetails(true)
    onTaskSelect?.(task)
  }
  
  // Calculate bar position
  const getBarStyle = (task: GanttTask) => {
    const startOffset = task.start.getTime() - timeRange.start
    const duration = task.end.getTime() - task.start.getTime()
    
    const left = (startOffset / timeRange.duration) * 100
    const width = (duration / timeRange.duration) * 100
    
    return {
      left: `${Math.max(0, left)}%`,
      width: `${Math.max(1, width)}%`,
      backgroundColor: statusColors[task.status]
    }
  }
  
  // Time markers
  const timeMarkers = useMemo(() => {
    const markers: Date[] = []
    const current = new Date(timeRange.start)
    while (current.getTime() <= timeRange.end) {
      markers.push(new Date(current))
      current.setMinutes(current.getMinutes() + 15)
    }
    return markers
  }, [timeRange])
  
  // Current time indicator position
  const nowPosition = useMemo(() => {
    const now = Date.now()
    if (now < timeRange.start || now > timeRange.end) return null
    const offset = now - timeRange.start
    return (offset / timeRange.duration) * 100
  }, [timeRange])
  
  return (
    <div className="w-full h-full min-h-[300px] flex flex-col bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">Run Schedule</h3>
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded bg-slate-500"></div>
            <span className="text-slate-400">Pending</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded bg-blue-500"></div>
            <span className="text-slate-400">Running</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded bg-emerald-500"></div>
            <span className="text-slate-400">Done</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded bg-red-500"></div>
            <span className="text-slate-400">Failed</span>
          </div>
        </div>
      </div>
      
      {/* Timeline header */}
      <div className="flex border-b border-slate-700 bg-slate-800">
        <div className="w-32 flex-shrink-0 p-1 text-xs font-medium text-slate-400 border-r border-slate-700">
          Task
        </div>
        <div className="flex-1 relative p-1">
          <div className="flex justify-between text-xs text-slate-500">
            {timeMarkers.filter((_, i) => i % 4 === 0).map((marker, i) => (
              <span key={i}>{formatTime(marker)}</span>
            ))}
          </div>
          
          {/* Current time indicator */}
          {nowPosition !== null && (
            <div 
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-500 z-10"
              style={{ left: `${nowPosition}%` }}
            >
              <div className="absolute -top-1 -left-1 w-2 h-2 bg-yellow-500 rounded-full"></div>
            </div>
          )}
        </div>
      </div>
      
      {/* Task rows */}
      <div className="flex-1 min-h-0 overflow-auto">
        {tasks.map((task, index) => (
          <motion.div 
            key={task.id}
            className={`flex border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer ${
              selectedTask?.id === task.id ? 'bg-slate-700/50' : ''
            }`}
            onClick={() => handleTaskClick(task)}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            {/* Task name */}
            <div className="w-40 flex-shrink-0 p-2 border-r border-slate-700">
              <div className="text-xs text-white font-medium truncate">{task.name}</div>
              <div className="text-xs text-slate-500">{task.assignee}</div>
            </div>
            
            {/* Timeline bar */}
            <div className="flex-1 relative h-10 p-1">
              <div className="absolute inset-2 bg-slate-800 rounded">
                <motion.div
                  className="h-full rounded relative overflow-hidden"
                  style={getBarStyle(task)}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  {/* Progress fill */}
                  <div 
                    className="absolute inset-y-0 left-0 bg-white/20"
                    style={{ width: `${task.progress}%` }}
                  />
                  
                  {/* Status icon */}
                  {task.status === 'running' && (
                    <motion.div 
                      className="absolute inset-0 flex items-center justify-center"
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full"></div>
                    </motion.div>
                  )}
                  
                  {/* Progress text */}
                  {task.progress > 0 && task.status !== 'running' && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-medium text-white">{task.progress}%</span>
                    </div>
                  )}
                </motion.div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
      
      {/* Task details panel */}
      <AnimatePresence>
        {showDetails && selectedTask && (
          <motion.div 
            className="border-t border-slate-700 bg-slate-800 p-4"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-white font-medium">{selectedTask.name}</h4>
                <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                  <span>Status: <span style={{ color: statusColors[selectedTask.status] }}>{selectedTask.status}</span></span>
                  <span>Progress: {selectedTask.progress}%</span>
                  <span>Duration: {formatDuration(selectedTask.start, selectedTask.end)}</span>
                </div>
                <div className="mt-2 text-sm text-slate-500">
                  {formatTime(selectedTask.start)} - {formatTime(selectedTask.end)}
                </div>
              </div>
              <button
                onClick={() => setShowDetails(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
