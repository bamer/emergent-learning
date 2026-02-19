import { useMemo, useState, useCallback } from 'react'
import * as d3 from 'd3'

// Sankey data types
interface SankeyNode {
  id: string
  name: string
  color: string
}

interface SankeyLink {
  source: string
  target: string
  value: number
}

interface SankeyData {
  nodes: SankeyNode[]
  links: SankeyLink[]
}

// Generate sample Sankey data
const generateSankeyData = (): SankeyData => {
  const nodes: SankeyNode[] = [
    // Sources
    { id: 'input', name: 'User Input', color: '#3b82f6' },
    { id: 'api', name: 'API Requests', color: '#8b5cf6' },
    { id: 'scheduled', name: 'Scheduled Tasks', color: '#06b6d4' },
    
    // Processing
    { id: 'orchestrator', name: 'Orchestrator', color: '#f59e0b' },
    { id: 'research', name: 'Research Agent', color: '#10b981' },
    { id: 'analysis', name: 'Analysis Agent', color: '#ec4899' },
    { id: 'execution', name: 'Execution Agent', color: '#ef4444' },
    
    // Storage
    { id: 'memory', name: 'Memory', color: '#6366f1' },
    { id: 'knowledge', name: 'Knowledge Base', color: '#14b8a6' },
    
    // Output
    { id: 'response', name: 'User Response', color: '#22c55e' },
    { id: 'learning', name: 'Learning', color: '#a855f7' },
    { id: 'logs', name: 'Logs', color: '#64748b' },
  ]
  
  const links: SankeyLink[] = [
    // Input flows
    { source: 'input', target: 'orchestrator', value: 45 },
    { source: 'api', target: 'orchestrator', value: 30 },
    { source: 'scheduled', target: 'orchestrator', value: 25 },
    
    // Orchestrator distribution
    { source: 'orchestrator', target: 'research', value: 35 },
    { source: 'orchestrator', target: 'analysis', value: 40 },
    { source: 'orchestrator', target: 'execution', value: 25 },
    
    // Research flows
    { source: 'research', target: 'memory', value: 20 },
    { source: 'research', target: 'knowledge', value: 15 },
    
    // Analysis flows
    { source: 'analysis', target: 'memory', value: 25 },
    { source: 'analysis', target: 'learning', value: 15 },
    
    // Execution flows
    { source: 'execution', target: 'response', value: 20 },
    { source: 'execution', target: 'logs', value: 5 },
    
    // Storage to output
    { source: 'memory', target: 'response', value: 30 },
    { source: 'memory', target: 'learning', value: 15 },
    { source: 'knowledge', target: 'response', value: 10 },
    { source: 'knowledge', target: 'learning', value: 5 },
    
    // Learning output
    { source: 'learning', target: 'logs', value: 20 },
  ]
  
  return { nodes, links }
}

// Simple Sankey layout calculation
function calculateSankeyLayout(data: SankeyData) {
  const nodeWidth = 20
  const nodePadding = 15
  
  // Group nodes by "column" (manually assigned based on id)
  const columns: Record<string, string[]> = {
    'col-0': ['input', 'api', 'scheduled'],
    'col-1': ['orchestrator'],
    'col-2': ['research', 'analysis', 'execution'],
    'col-3': ['memory', 'knowledge'],
    'col-4': ['response', 'learning', 'logs'],
  }
  
  // Calculate node positions
  const nodePositions: Record<string, { x: number; y: number; height: number }> = {}
  const columnWidth = 180
  const canvasHeight = 400
  
  // Calculate total values per column
  const columnTotals: Record<string, number> = {}
  Object.entries(columns).forEach(([col, nodeIds]) => {
    columnTotals[col] = nodeIds.reduce((sum, id) => {
      const outgoing = data.links.filter(l => l.source === id).reduce((s, l) => s + l.value, 0)
      const incoming = data.links.filter(l => l.target === id).reduce((s, l) => s + l.value, 0)
      return Math.max(incoming, outgoing, 1)
    }, 0)
  })
  
  // Position nodes
  let currentY: Record<string, number> = {}
  Object.keys(columns).forEach(col => { currentY[col] = 30 })
  
  Object.entries(columns).forEach(([col, nodeIds]) => {
    const colIndex = parseInt(col.split('-')[1])
    const x = colIndex * columnWidth + 20
    
    nodeIds.forEach(nodeId => {
      const outgoing = data.links.filter(l => l.source === nodeId).reduce((s, l) => s + l.value, 0)
      const incoming = data.links.filter(l => l.target === nodeId).reduce((s, l) => s + l.value, 0)
      const value = Math.max(incoming, outgoing, 1)
      
      const height = Math.max(20, (value / 100) * canvasHeight * 0.5)
      
      nodePositions[nodeId] = {
        x,
        y: currentY[col],
        height
      }
      
      currentY[col] += height + nodePadding
    })
  })
  
  // Calculate link paths
  const linkPaths: { link: SankeyLink; path: string; color: string }[] = []
  
  data.links.forEach(link => {
    const sourcePos = nodePositions[link.source]
    const targetPos = nodePositions[link.target]
    
    if (!sourcePos || !targetPos) return
    
    const linkHeight = Math.max(2, (link.value / 100) * 50)
    
    const sourceX = sourcePos.x + nodeWidth
    const sourceY = sourcePos.y + sourcePos.height / 2
    const targetX = targetPos.x
    const targetY = targetPos.y + targetPos.height / 2
    
    // Create smooth bezier curve
    const midX = (sourceX + targetX) / 2
    
    const path = `M ${sourceX} ${sourceY - linkHeight / 2}
                  C ${midX} ${sourceY - linkHeight / 2},
                    ${midX} ${targetY - linkHeight / 2},
                    ${targetX} ${targetY - linkHeight / 2}
                  L ${targetX} ${targetY + linkHeight / 2}
                  C ${midX} ${targetY + linkHeight / 2},
                    ${midX} ${sourceY + linkHeight / 2},
                    ${sourceX} ${sourceY + linkHeight / 2}
                  Z`
    
    const sourceNode = data.nodes.find(n => n.id === link.source)
    linkPaths.push({
      link,
      path,
      color: sourceNode?.color || '#64748b'
    })
  })
  
  return { nodePositions, linkPaths }
}

// Main Sankey Diagram component
interface SankeyDiagramProps {
  data?: SankeyData
  onNodeSelect?: (node: SankeyNode) => void
}

export function SankeyDiagram({ data, onNodeSelect }: SankeyDiagramProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [hoveredLink, setHoveredLink] = useState<SankeyLink | null>(null)
  
  const sankeyData = useMemo(() => data || generateSankeyData(), [data])
  const { nodePositions, linkPaths } = useMemo(
    () => calculateSankeyLayout(sankeyData),
    [sankeyData]
  )
  
  const handleNodeClick = useCallback((node: SankeyNode) => {
    onNodeSelect?.(node)
  }, [onNodeSelect])
  
  return (
    <div className="w-full h-full min-h-[300px] flex flex-col bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">Flow Analysis</h3>
        <div className="text-xs text-slate-400">
          Data Flow
        </div>
      </div>
      
      {/* Sankey Canvas */}
      <div className="flex-1 min-h-0 p-2 overflow-auto">
        <svg width="100%" height="100%" viewBox="0 0 800 350" preserveAspectRatio="xMidYMid meet">
          <defs>
            {sankeyData.nodes.map(node => (
              <linearGradient key={node.id} id={`gradient-${node.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={node.color} stopOpacity={0.8} />
                <stop offset="100%" stopColor={node.color} stopOpacity={0.4} />
              </linearGradient>
            ))}
          </defs>
          
          {/* Links */}
          {linkPaths.map(({ link, path, color }, index) => {
            const isHovered = hoveredLink?.source === link.source && hoveredLink?.target === link.target
            
            return (
              <path
                key={`${link.source}-${link.target}-${index}`}
                d={path}
                fill={color}
                fillOpacity={isHovered ? 0.7 : 0.4}
                stroke={isHovered ? 'white' : 'none'}
                strokeWidth={isHovered ? 1 : 0}
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredLink(link)}
                onMouseLeave={() => setHoveredLink(null)}
              />
            )
          })}
          
          {/* Nodes */}
          {sankeyData.nodes.map(node => {
            const pos = nodePositions[node.id]
            if (!pos) return null
            
            const isHovered = hoveredNode === node.id
            
            return (
              <g
                key={node.id}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => handleNodeClick(node)}
              >
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={20}
                  height={pos.height}
                  fill={`url(#gradient-${node.id})`}
                  rx={3}
                  stroke={isHovered ? 'white' : 'none'}
                  strokeWidth={2}
                />
                <text
                  x={pos.x - 5}
                  y={pos.y + pos.height / 2}
                  textAnchor="end"
                  alignmentBaseline="middle"
                  fill={isHovered ? 'white' : '#94a3b8'}
                  fontSize={12}
                  fontWeight={isHovered ? 600 : 400}
                  className="transition-colors"
                >
                  {node.name}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
      
      {/* Hover/Legend panel */}
      <div className="p-4 border-t border-slate-700 bg-slate-800">
        <div className="flex items-center justify-between">
          <div>
            {hoveredLink && (
              <div className="text-sm">
                <span className="text-slate-400">Flow: </span>
                <span className="text-white font-medium">
                  {sankeyData.nodes.find(n => n.id === hoveredLink.source)?.name}
                </span>
                <span className="text-slate-400"> → </span>
                <span className="text-white font-medium">
                  {sankeyData.nodes.find(n => n.id === hoveredLink.target)?.name}
                </span>
                <span className="text-blue-400 ml-2">({hoveredLink.value})</span>
              </div>
            )}
            {hoveredNode && !hoveredLink && (
              <div className="text-sm">
                <span className="text-white font-medium">
                  {sankeyData.nodes.find(n => n.id === hoveredNode)?.name}
                </span>
              </div>
            )}
            {!hoveredNode && !hoveredLink && (
              <div className="text-sm text-slate-400">
                Hover over nodes or links to see details
              </div>
            )}
          </div>
          
          {/* Legend */}
          <div className="flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <span className="text-slate-400">Input</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-amber-500"></div>
              <span className="text-slate-400">Processing</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-violet-500"></div>
              <span className="text-slate-400">Storage</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              <span className="text-slate-400">Output</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
