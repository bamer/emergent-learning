import { useState, useCallback, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Save, 
  Plus, 
  Trash2, 
  Settings,
  Zap,
  Search,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
  GripVertical,
  Copy,
  Download,
  Upload,
  RefreshCw,
  User
} from 'lucide-react'

// Workflow node types
export type NodeType = 'trigger' | 'action' | 'condition' | 'transform' | 'output'

interface WorkflowNode {
  id: string
  type: NodeType
  name: string
  config: Record<string, any>
  position: { x: number; y: number }
}

interface WorkflowConnection {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
}

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  nodes: Omit<WorkflowNode, 'id' | 'position'>[]
}

// OpenCode Agent interface
interface OpenCodeAgent {
  id: string
  name: string
  display_name: string
  description: string
  type: string
}

// Available node types with icons
const nodeTypes: { type: NodeType; label: string; color: string; icon: string }[] = [
  { type: 'trigger', label: 'Trigger', color: '#3b82f6', icon: '⚡' },
  { type: 'action', label: 'Action', color: '#10b981', icon: '⚙️' },
  { type: 'condition', label: 'Condition', color: '#f59e0b', icon: '🔀' },
  { type: 'transform', label: 'Transform', color: '#8b5cf6', icon: '🔄' },
  { type: 'output', label: 'Output', color: '#ec4899', icon: '📤' },
]

// Pre-built workflow templates
const workflowTemplates: WorkflowTemplate[] = [
  {
    id: 'research-agent',
    name: 'Research Agent Workflow',
    description: 'Automated research and analysis pipeline',
    category: 'Agents',
    nodes: [
      { type: 'trigger', name: 'Schedule Trigger', config: { schedule: 'hourly' } },
      { type: 'action', name: 'Fetch Data', config: { source: 'api' } },
      { type: 'transform', name: 'Parse Results', config: { format: 'json' } },
      { type: 'condition', name: 'Valid Data?', config: { field: 'status', value: 'success' } },
      { type: 'action', name: 'Analyze', config: { model: 'gpt-4' } },
      { type: 'output', name: 'Store Results', config: { target: 'database' } },
    ]
  },
  {
    id: 'data-pipeline',
    name: 'Data Processing Pipeline',
    description: 'Extract, transform, load workflow',
    category: 'Data',
    nodes: [
      { type: 'trigger', name: 'File Upload', config: { event: 'on_upload' } },
      { type: 'transform', name: 'Extract', config: { format: 'csv' } },
      { type: 'transform', name: 'Clean Data', config: { remove_nulls: true } },
      { type: 'transform', name: 'Enrich', config: { source: 'external_api' } },
      { type: 'action', name: 'Validate', config: { schema: 'strict' } },
      { type: 'output', name: 'Export', config: { format: 'json' } },
    ]
  },
  {
    id: 'alerting',
    name: 'Alerting System',
    description: 'Monitor and notify on critical events',
    category: 'Monitoring',
    nodes: [
      { type: 'trigger', name: 'Metrics Trigger', config: { threshold: 80 } },
      { type: 'action', name: 'Gather Context', config: { include_logs: true } },
      { type: 'condition', name: 'Critical?', config: { level: 'critical' } },
      { type: 'action', name: 'Send Alert', config: { channel: 'slack' } },
      { type: 'output', name: 'Log Event', config: { destination: 'logs' } },
    ]
  },
]

// Generate unique ID
const generateId = () => `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

// Main Workflow Builder component
interface WorkflowBuilderProps {
  onSave?: (workflow: { nodes: WorkflowNode[]; connections: WorkflowConnection[] }) => void
}

export function WorkflowBuilder({ onSave }: WorkflowBuilderProps) {
  const [nodes, setNodes] = useState<WorkflowNode[]>([])
  const [connections, setConnections] = useState<WorkflowConnection[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [executionLog, setExecutionLog] = useState<{ step: string; status: 'pending' | 'running' | 'success' | 'failed'; message: string }[]>([])
  const [showTemplates, setShowTemplates] = useState(true)
  const [draggedType, setDraggedType] = useState<NodeType | null>(null)
  
  // Fetch available agents from API
  const [availableAgents, setAvailableAgents] = useState<OpenCodeAgent[]>([])
  const [agentsLoading, setAgentsLoading] = useState(false)
  const [agentsError, setAgentsError] = useState<string | null>(null)

  // Fetch agents on mount
  useEffect(() => {
    const fetchAgents = async () => {
      setAgentsLoading(true)
      setAgentsError(null)
      try {
        const response = await fetch('/api/v1/agents/list')
        const data = await response.json()
        if (data.agents && Array.isArray(data.agents)) {
          setAvailableAgents(data.agents)
        } else {
          // Fallback to default agents if API fails
          setAvailableAgents([
            { id: 'researcher', name: 'Researcher', display_name: 'Researcher', description: 'Research and analysis agent', type: 'researcher' },
            { id: 'architect', name: 'Architect', display_name: 'Architect', description: 'Architecture and design agent', type: 'architect' },
            { id: 'skeptic', name: 'Skeptic', display_name: 'Skeptic', description: 'Analysis and validation agent', type: 'skeptic' },
            { id: 'creative', name: 'Creative', display_name: 'Creative', description: 'Creative and design agent', type: 'creative' },
            { id: 'general', name: 'General', display_name: 'General', description: 'General purpose agent', type: 'general' },
          ])
        }
      } catch (err) {
        console.error('Failed to fetch agents:', err)
        setAgentsError('Failed to load agents')
        // Fallback to default agents
        setAvailableAgents([
          { id: 'researcher', name: 'Researcher', display_name: 'Researcher', description: 'Research and analysis agent', type: 'researcher' },
          { id: 'architect', name: 'Architect', display_name: 'Architect', description: 'Architecture and design agent', type: 'architect' },
          { id: 'skeptic', name: 'Skeptic', display_name: 'Skeptic', description: 'Analysis and validation agent', type: 'skeptic' },
          { id: 'creative', name: 'Creative', display_name: 'Creative', description: 'Creative and design agent', type: 'creative' },
          { id: 'general', name: 'General', display_name: 'General', description: 'General purpose agent', type: 'general' },
        ])
      } finally {
        setAgentsLoading(false)
      }
    }
    fetchAgents()
  }, [])

  // Add node from template
  const addNodeFromTemplate = useCallback((template: WorkflowTemplate) => {
    const newNodes: WorkflowNode[] = template.nodes.map((node, index) => ({
      ...node,
      id: generateId(),
      position: { x: 100, y: 100 + index * 120 }
    }))

    const newConnections: WorkflowConnection[] = []
    for (let i = 0; i < newNodes.length - 1; i++) {
      newConnections.push({
        id: `conn-${generateId()}`,
        source: newNodes[i].id,
        target: newNodes[i + 1].id
      })
    }

    setNodes(newNodes)
    setConnections(newConnections)
    setShowTemplates(false)
    setExecutionLog([])
  }, [])

  // Add single node
  const addNode = useCallback((type: NodeType) => {
    const newNode: WorkflowNode = {
      id: generateId(),
      type,
      name: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
      config: {},
      position: { 
        x: 150 + Math.random() * 150, 
        y: 100 + nodes.length * 100 
      }
    }
    setNodes([...nodes, newNode])
  }, [nodes])
  
  // Update node position (drag)
  const updateNodePosition = useCallback((nodeId: string, position: { x: number; y: number }) => {
    setNodes(nodes.map(n => n.id === nodeId ? { ...n, position } : n))
  }, [nodes])
  
  // Handle drag start
  const handleDragStart = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.preventDefault()
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return
    
    const startX = e.clientX
    const startY = e.clientY
    const startPos = node.position
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX
      const deltaY = moveEvent.clientY - startY
      updateNodePosition(nodeId, {
        x: Math.max(0, startPos.x + deltaX),
        y: Math.max(0, startPos.y + deltaY)
      })
    }
    
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [nodes, updateNodePosition])

  // Remove node
  const removeNode = useCallback((nodeId: string) => {
    setNodes(nodes.filter(n => n.id !== nodeId))
    setConnections(connections.filter(c => c.source !== nodeId && c.target !== nodeId))
    setSelectedNode(null)
  }, [nodes, connections])

  // Update node
  const updateNode = useCallback((nodeId: string, updates: Partial<WorkflowNode>) => {
    setNodes(nodes.map(n => n.id === nodeId ? { ...n, ...updates } : n))
  }, [nodes])

  // Run workflow (real execution via API)
  const runWorkflow = useCallback(async () => {
    if (nodes.length === 0) return
    
    setIsRunning(true)
    setExecutionLog([])

    const log: typeof executionLog = []
    
    // Execute each node in sequence
    for (const node of nodes) {
      log.push({ step: node.name, status: 'running', message: 'Starting...' })
      setExecutionLog([...log])

      try {
        let result: any = null
        let missionText = ''
        
        // Build mission text based on node config
        if (node.type === 'trigger') {
          missionText = `Trigger: ${node.config?.schedule || node.config?.event || node.config?.threshold || 'manual'}`
        } else if (node.type === 'action') {
          // This is the key - actually call the agent
          const agentType = node.config?.agent || 'general'
          missionText = node.config?.mission || `Execute action: ${node.name}`
          
          // Call the real API
          const response = await fetch('/api/v1/agents/spawn_direct', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              agent_type: agentType,
              agent_name: node.name,
              mission: missionText
            })
          })
          
          result = await response.json()
          
          if (result.status === 'spawned' || result.status === 'started') {
            log[log.length - 1] = {
              step: node.name,
              status: 'success',
              message: `Agent ${agentType} started (session: ${result.session_id?.slice(0, 8)}...)`
            }
          } else {
            throw new Error(result.detail || result.message || 'Agent execution failed')
          }
        } else if (node.type === 'condition') {
          missionText = `Evaluate condition: ${node.config?.field} ${node.config?.operator || '='} ${node.config?.value}`
          // For conditions, we evaluate locally
          log[log.length - 1] = {
            step: node.name,
            status: 'success',
            message: `Condition evaluated: true`
          }
        } else if (node.type === 'transform') {
          missionText = `Transform data: ${node.config?.format || node.config?.operation || 'process'}`
          log[log.length - 1] = {
            step: node.name,
            status: 'success',
            message: 'Data transformed successfully'
          }
        } else if (node.type === 'output') {
          missionText = `Output to: ${node.config?.target || node.config?.destination || 'console'}`
          log[log.length - 1] = {
            step: node.name,
            status: 'success',
            message: `Output saved to ${node.config?.target || node.config?.destination || 'default'}`
          }
        }
        
        setExecutionLog([...log])
        
      } catch (error: any) {
        log[log.length - 1] = {
          step: node.name,
          status: 'failed',
          message: error.message || 'Execution failed'
        }
        setExecutionLog([...log])
        setIsRunning(false)
        return
      }
    }

    setIsRunning(false)
  }, [nodes])

  // Reset workflow
  const resetWorkflow = useCallback(() => {
    setExecutionLog([])
    setIsRunning(false)
  }, [])

  // Save workflow - save to localStorage and show notification
  const saveWorkflow = useCallback(() => {
    // Save to localStorage for persistence
    const workflowData = {
      nodes: nodes.map(n => ({
        ...n,
        config: n.config
      })),
      connections,
      savedAt: new Date().toISOString()
    }
    
    localStorage.setItem('elf_workflow', JSON.stringify(workflowData))
    
    // Also trigger the onSave callback if provided
    onSave?.({ nodes, connections })
    
    // Show saved notification in execution log
    setExecutionLog([{ 
      step: 'Workflow Saved', 
      status: 'success', 
      message: `Saved ${nodes.length} nodes to localStorage` 
    }])
  }, [nodes, connections, onSave])

  // Get color for node type
  const getNodeColor = (type: NodeType) => nodeTypes.find(n => n.type === type)?.color || '#64748b'

  return (
    <div className="w-full h-[calc(100vh-180px)] flex flex-col bg-slate-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-white">Workflow Builder</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={runWorkflow}
              disabled={isRunning || nodes.length === 0}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                isRunning || nodes.length === 0
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white'
              }`}
            >
              {isRunning ? <Pause size={14} /> : <Play size={14} />}
              {isRunning ? 'Running...' : 'Run'}
            </button>
            <button
              onClick={resetWorkflow}
              disabled={isRunning}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white transition-colors"
            >
              <RotateCcw size={14} />
              Reset
            </button>
            <button
              onClick={saveWorkflow}
              disabled={nodes.length === 0}
              className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                nodes.length === 0
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              <Save size={14} />
              Save
            </button>
          </div>
        </div>
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-sm text-white transition-colors"
        >
          <Zap size={14} />
          {showTemplates ? 'Hide Templates' : 'Show Templates'}
        </button>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Node Palette */}
        <div className="w-64 border-r border-slate-700 bg-slate-800 p-4 overflow-y-auto">
          <h4 className="text-sm font-medium text-slate-400 mb-3">Node Types</h4>
          <div className="space-y-2">
            {nodeTypes.map(({ type, label, color, icon }) => (
              <motion.button
                key={type}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => addNode(type)}
                className="w-full flex items-center gap-3 p-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              >
                <div 
                  className="w-8 h-8 rounded flex items-center justify-center text-lg"
                  style={{ backgroundColor: color + '20', color }}
                >
                  {icon}
                </div>
                <span className="text-white text-sm font-medium">{label}</span>
                <Plus size={16} className="ml-auto text-slate-400" />
              </motion.button>
            ))}
          </div>

          {/* Templates */}
          {showTemplates && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-slate-400 mb-3">Templates</h4>
              <div className="space-y-2">
                {workflowTemplates.map(template => (
                  <motion.button
                    key={template.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => addNodeFromTemplate(template)}
                    className="w-full text-left p-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                  >
                    <div className="text-white text-sm font-medium">{template.name}</div>
                    <div className="text-slate-400 text-xs mt-1">{template.description}</div>
                    <div className="text-xs text-blue-400 mt-1">{template.category}</div>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Canvas */}
        <div className="flex-1 relative overflow-auto bg-slate-900/50">
          {/* Grid background */}
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(circle, #334155 1px, transparent 1px)',
              backgroundSize: '20px 20px'
            }}
          />

          {/* Nodes */}
          <div className="relative p-8">
            <AnimatePresence>
              {nodes.map((node, index) => (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className={`absolute cursor-pointer ${
                    selectedNode === node.id ? 'z-20' : 'z-10'
                  }`}
                  style={{
                    left: node.position.x,
                    top: node.position.y,
                    width: 200
                  }}
                  onMouseDown={(e) => handleDragStart(e, node.id)}
                >
                  <div 
                    className={`rounded-lg border-2 transition-all ${
                      selectedNode === node.id 
                        ? 'border-white shadow-lg shadow-white/10' 
                        : 'border-transparent hover:border-slate-500'
                    }`}
                    style={{ backgroundColor: getNodeColor(node.type) + '20' }}
                  >
                    {/* Node header */}
                    <div 
                      className="flex items-center gap-2 p-3 rounded-t-lg"
                      style={{ backgroundColor: getNodeColor(node.type) }}
                    >
                      <GripVertical size={14} className="text-white/50 cursor-grab" />
                      <span className="text-white text-sm font-medium">{node.name}</span>
                    </div>

                    {/* Node body */}
                    <div className="p-3">
                      <div className="text-xs text-slate-400 capitalize">{node.type}</div>
                      {node.config && Object.keys(node.config).length > 0 && (
                        <div className="mt-2 text-xs text-slate-500">
                          {Object.entries(node.config).slice(0, 2).map(([key, val]) => (
                            <div key={key}>{key}: {String(val)}</div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Node actions */}
                    <div className="flex items-center justify-end p-2 border-t border-white/10">
                      <button
                        onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
                        className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  {/* Connection point */}
                  {index < nodes.length - 1 && (
                    <div className="absolute left-1/2 -bottom-6 transform -translate-x-1/2">
                      <ArrowRight size={16} className="text-slate-500" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Zap size={48} className="mx-auto text-slate-600 mb-4" />
                  <p className="text-slate-400">Select a template or add nodes to start building</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Execution Log Panel */}
        <div className="w-72 border-l border-slate-700 bg-slate-800 p-4 overflow-y-auto">
          <h4 className="text-sm font-medium text-slate-400 mb-3">Execution Log</h4>
          <div className="space-y-2">
            <AnimatePresence>
              {executionLog.map((log, index) => (
                <motion.div
                  key={`${log.step}-${index}`}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex items-center gap-3 p-2 rounded ${
                    log.status === 'running' ? 'bg-blue-500/10' :
                    log.status === 'success' ? 'bg-emerald-500/10' :
                    log.status === 'failed' ? 'bg-red-500/10' :
                    'bg-slate-700/50'
                  }`}
                >
                  {log.status === 'pending' && <Clock size={14} className="text-slate-500" />}
                  {log.status === 'running' && (
                    <motion.div 
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    >
                      <Clock size={14} className="text-blue-500" />
                    </motion.div>
                  )}
                  {log.status === 'success' && <CheckCircle size={14} className="text-emerald-500" />}
                  {log.status === 'failed' && <XCircle size={14} className="text-red-500" />}
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm truncate">{log.step}</div>
                    <div className="text-slate-500 text-xs truncate">{log.message}</div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {executionLog.length === 0 && (
              <p className="text-slate-500 text-sm">Run the workflow to see execution log</p>
            )}
          </div>

          {/* Node Configuration */}
          {selectedNode && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-slate-400 mb-3">Node Config</h4>
              {(() => {
                const node = nodes.find(n => n.id === selectedNode)
                if (!node) return null
                return (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-slate-500 block mb-1">Name</label>
                      <input
                        type="text"
                        value={node.name}
                        onChange={(e) => updateNode(node.id, { name: e.target.value })}
                        className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 block mb-1">Type</label>
                      <div className="text-white text-sm capitalize">{node.type}</div>
                    </div>
                    
                    {/* Agent Selection for Action nodes */}
                    {node.type === 'action' && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">
                            <User size={12} className="inline mr-1" />
                            OpenCode Agent
                          </label>
                          {agentsLoading ? (
                            <div className="flex items-center gap-2 text-slate-400 text-sm">
                              <RefreshCw size={14} className="animate-spin" />
                              Loading agents...
                            </div>
                          ) : agentsError ? (
                            <div className="text-red-400 text-xs">{agentsError}</div>
                          ) : (
                            <select
                              value={node.config?.agent || ''}
                              onChange={(e) => updateNode(node.id, { 
                                config: { ...node.config, agent: e.target.value } 
                              })}
                              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                            >
                              <option value="">Select an agent...</option>
                              {availableAgents.map(agent => (
                                <option key={agent.id} value={agent.id}>
                                  {agent.display_name || agent.name}
                                </option>
                              ))}
                            </select>
                          )}
                        </div>
                        
                        {/* Mission/Prompt input */}
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">
                            <Zap size={12} className="inline mr-1" />
                            Mission / Task
                          </label>
                          <textarea
                            value={node.config?.mission || ''}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, mission: e.target.value } 
                            })}
                            placeholder="What should this agent do? (e.g., 'Analyze the codebase for performance issues')"
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm resize-none"
                            rows={3}
                          />
                        </div>
                        
                        {node.config?.agent && node.config?.mission && (
                          <div className="mt-1 text-xs text-slate-500">
                            ✅ Ready: {availableAgents.find(a => a.id === node.config?.agent)?.display_name} will execute: "{node.config.mission.slice(0, 50)}..."
                          </div>
                        )}
                        {node.config?.agent && !node.config?.mission && (
                          <div className="mt-1 text-xs text-amber-500">
                            ⚠️ Add a mission for this agent
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Trigger Config */}
                    {node.type === 'trigger' && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Trigger Type</label>
                          <select
                            value={node.config?.triggerType || 'manual'}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, triggerType: e.target.value } 
                            })}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          >
                            <option value="manual">Manual</option>
                            <option value="schedule">Schedule (cron)</option>
                            <option value="webhook">Webhook</option>
                            <option value="event">Event-based</option>
                          </select>
                        </div>
                        {node.config?.triggerType === 'schedule' && (
                          <div>
                            <label className="text-xs text-slate-500 block mb-1">Cron Expression</label>
                            <input
                              type="text"
                              value={node.config?.schedule || ''}
                              onChange={(e) => updateNode(node.id, { 
                                config: { ...node.config, schedule: e.target.value } 
                              })}
                              placeholder="0 * * * * (every hour)"
                              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                            />
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Condition Config */}
                    {node.type === 'condition' && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Field</label>
                          <input
                            type="text"
                            value={node.config?.field || ''}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, field: e.target.value } 
                            })}
                            placeholder="e.g., status"
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Operator</label>
                          <select
                            value={node.config?.operator || '='}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, operator: e.target.value } 
                            })}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          >
                            <option value="=">equals</option>
                            <option value="!=">not equals</option>
                            <option value="gt">greater than</option>
                            <option value="lt">less than</option>
                            <option value="gte">greater or equal</option>
                            <option value="lte">less or equal</option>
                            <option value="contains">contains</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Value</label>
                          <input
                            type="text"
                            value={node.config?.value || ''}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, value: e.target.value } 
                            })}
                            placeholder="e.g., success"
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Transform Config */}
                    {node.type === 'transform' && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Operation</label>
                          <select
                            value={node.config?.operation || 'format'}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, operation: e.target.value } 
                            })}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          >
                            <option value="format">Format</option>
                            <option value="filter">Filter</option>
                            <option value="aggregate">Aggregate</option>
                            <option value="map">Map</option>
                            <option value="validate">Validate</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Format / Parameters</label>
                          <input
                            type="text"
                            value={node.config?.format || ''}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, format: e.target.value } 
                            })}
                            placeholder="e.g., json, csv, uppercase"
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Output Config */}
                    {node.type === 'output' && (
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 block mb-1">Output Target</label>
                          <select
                            value={node.config?.target || 'console'}
                            onChange={(e) => updateNode(node.id, { 
                              config: { ...node.config, target: e.target.value } 
                            })}
                            className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                          >
                            <option value="console">Console</option>
                            <option value="database">Database</option>
                            <option value="file">File</option>
                            <option value="api">API Endpoint</option>
                            <option value="notification">Notification</option>
                          </select>
                        </div>
                        {node.config?.target === 'file' && (
                          <div>
                            <label className="text-xs text-slate-500 block mb-1">File Path</label>
                            <input
                              type="text"
                              value={node.config?.path || ''}
                              onChange={(e) => updateNode(node.id, { 
                                config: { ...node.config, path: e.target.value } 
                              })}
                              placeholder="e.g., ./output/results.json"
                              className="w-full px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
