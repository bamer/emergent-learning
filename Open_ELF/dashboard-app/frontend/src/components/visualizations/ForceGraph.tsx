import { useRef, useMemo, useState, useCallback, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Text, Html, Line } from '@react-three/drei'
import * as THREE from 'three'
import * as d3 from 'd3'

// Node and link types
interface GraphNode {
  id: string
  label: string
  group: number
  value: number
}

interface GraphLink {
  source: string
  target: string
  value: number
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

// Generate sample graph data
const generateGraphData = (): GraphData => {
  const nodes: GraphNode[] = [
    { id: 'orchestrator', label: 'Orchestrator', group: 1, value: 50 },
    { id: 'agent1', label: 'Research Agent', group: 2, value: 30 },
    { id: 'agent2', label: 'Analysis Agent', group: 2, value: 30 },
    { id: 'agent3', label: 'Execution Agent', group: 2, value: 30 },
    { id: 'memory', label: 'Memory', group: 3, value: 40 },
    { id: 'knowledge', label: 'Knowledge', group: 3, value: 35 },
    { id: 'learning', label: 'Learning Engine', group: 4, value: 45 },
    { id: 'heuristics', label: 'Heuristics', group: 4, value: 35 },
    { id: 'api', label: 'API Gateway', group: 5, value: 25 },
    { id: 'db', label: 'Database', group: 5, value: 30 },
  ]
  
  const links: GraphLink[] = [
    { source: 'orchestrator', target: 'agent1', value: 10 },
    { source: 'orchestrator', target: 'agent2', value: 10 },
    { source: 'orchestrator', target: 'agent3', value: 10 },
    { source: 'orchestrator', target: 'memory', value: 8 },
    { source: 'orchestrator', target: 'knowledge', value: 8 },
    { source: 'agent1', target: 'learning', value: 6 },
    { source: 'agent2', target: 'heuristics', value: 6 },
    { source: 'agent3', target: 'api', value: 5 },
    { source: 'memory', target: 'db', value: 7 },
    { source: 'knowledge', target: 'db', value: 7 },
    { source: 'learning', target: 'heuristics', value: 5 },
    { source: 'heuristics', target: 'orchestrator', value: 4 },
  ]
  
  return { nodes, links }
}

// Node sphere component
interface NodeProps {
  node: GraphNode
  position: THREE.Vector3
  onSelect: (node: GraphNode) => void
  selected: boolean
  hovered: string | null
  onHover: (id: string | null) => void
}

function GraphNode({ node, position, onSelect, selected, hovered, onHover }: NodeProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  const color = useMemo(() => {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    return colors[node.group - 1] || '#6b7280'
  }, [node.group])
  
  const scale = useMemo(() => {
    return Math.max(0.5, node.value / 20)
  }, [node.value])
  
  useFrame(() => {
    if (meshRef.current) {
      const targetScale = hovered === node.id ? 1.3 : 1
      meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1)
    }
  })
  
  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={() => onSelect(node)}
        onPointerOver={() => onHover(node.id)}
        onPointerOut={() => onHover(null)}
      >
        <sphereGeometry args={[scale, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected || hovered === node.id ? 0.5 : 0.2}
          roughness={0.3}
          metalness={0.7}
        />
      </mesh>
      <Text
        position={[0, scale + 1, 0]}
        fontSize={1.5}
        color="white"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.1}
        outlineColor="#000000"
      >
        {node.label}
      </Text>
    </group>
  )
}

// Edge line component
interface EdgeProps {
  start: THREE.Vector3
  end: THREE.Vector3
  value: number
  highlighted: boolean
}

function GraphEdge({ start, end, value, highlighted }: EdgeProps) {
  const points = useMemo(() => [start, end], [start, end])
  
  return (
    <Line
      points={points}
      color={highlighted ? '#60a5fa' : '#475569'}
      lineWidth={highlighted ? 3 : Math.max(0.5, value / 3)}
      transparent
      opacity={highlighted ? 1 : 0.6}
    />
  )
}

// Force simulation hook
function useForceSimulation(data: GraphData) {
  const [positions, setPositions] = useState<Map<string, THREE.Vector3>>(new Map())
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null)
  
  useEffect(() => {
    // Initialize positions
    const initialPositions = new Map<string, THREE.Vector3>()
    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * Math.PI * 2
      const radius = 20
      initialPositions.set(node.id, new THREE.Vector3(
        Math.cos(angle) * radius,
        Math.sin(angle) * radius,
        (Math.random() - 0.5) * 10
      ))
    })
    setPositions(initialPositions)
    
    // Create simulation
    const nodes = data.nodes.map(n => ({ ...n }))
    const links = data.links.map(l => ({ ...l }))
    
    simulationRef.current = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(15).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(0, 0))
      .force('collision', d3.forceCollide().radius(5))
      .on('tick', () => {
        const newPositions = new Map<string, THREE.Vector3>()
        nodes.forEach((node: any) => {
          newPositions.set(node.id, new THREE.Vector3(node.x, node.y, 0))
        })
        setPositions(newPositions)
      })
    
    return () => {
      simulationRef.current?.stop()
    }
  }, [data])
  
  return positions
}

// Main Force Graph component
interface ForceGraphProps {
  data?: GraphData
  onNodeSelect?: (node: GraphNode) => void
}

export function ForceGraph({ data, onNodeSelect }: ForceGraphProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [layout, setLayout] = useState<'3d' | '2d'>('3d')
  
  const graphData = useMemo(() => data || generateGraphData(), [data])
  const positions = useForceSimulation(graphData)
  
  const handleNodeSelect = useCallback((node: GraphNode) => {
    setSelectedNode(node)
    onNodeSelect?.(node)
  }, [onNodeSelect])
  
  // Get highlighted links
  const highlightedLinks = useMemo(() => {
    if (!selectedNode) return new Set<string>()
    const highlighted = new Set<string>()
    graphData.links.forEach(link => {
      if (link.source === selectedNode.id || link.target === selectedNode.id) {
        highlighted.add(`${link.source}-${link.target}`)
        highlighted.add(`${link.target}-${link.source}`)
      }
    })
    return highlighted
  }, [selectedNode, graphData.links])
  
  return (
    <div className="w-full h-full min-h-[500px] flex flex-col bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">Force Graph</h3>
        <div className="flex gap-1">
          <button
            onClick={() => setLayout('3d')}
            className={`px-2 py-1 rounded text-xs ${
              layout === '3d' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            3D
          </button>
          <button
            onClick={() => setLayout('2d')}
            className={`px-2 py-1 rounded text-xs ${
              layout === '2d' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            2D
          </button>
        </div>
      </div>
      
      {/* Canvas */}
      <div className="flex-1 min-h-[400px]">
        <Canvas camera={{ position: [0, 0, 100], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[50, 50, 50]} intensity={1} />
          <pointLight position={[-50, -50, 50]} intensity={0.5} />
          
          {/* Edges */}
          {graphData.links.map((link, i) => {
            const sourcePos = positions.get(link.source as string)
            const targetPos = positions.get(link.target as string)
            if (!sourcePos || !targetPos) return null
            
            return (
              <GraphEdge
                key={`${link.source}-${link.target}-${i}`}
                start={sourcePos}
                end={targetPos}
                value={link.value}
                highlighted={highlightedLinks.has(`${link.source}-${link.target}`)}
              />
            )
          })}
          
          {/* Nodes */}
          {graphData.nodes.map(node => {
            const pos = positions.get(node.id)
            if (!pos) return null
            
            return (
              <GraphNode
                key={node.id}
                node={node}
                position={pos}
                onSelect={handleNodeSelect}
                selected={selectedNode?.id === node.id}
                hovered={hoveredNode}
                onHover={setHoveredNode}
              />
            )
          })}
          
          <OrbitControls
            enablePan
            enableZoom
            enableRotate={layout === '3d'}
            minDistance={30}
            maxDistance={150}
          />
        </Canvas>
      </div>
      
      {/* Legend */}
      <div className="p-2 border-t border-slate-700 bg-slate-800">
        <div className="flex flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-slate-400">Orchestration</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            <span className="text-slate-400">Agents</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <span className="text-slate-400">Storage</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-slate-400">Learning</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-violet-500"></div>
            <span className="text-slate-400">Infrastructure</span>
          </div>
        </div>
      </div>
      
      {/* Selected node details */}
      {selectedNode && (
        <div className="p-4 border-t border-slate-700 bg-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-medium">{selectedNode.label}</h4>
              <p className="text-slate-400 text-sm">ID: {selectedNode.id}</p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
