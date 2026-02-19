import { useRef, useMemo, useState, useCallback } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Text, Html } from '@react-three/drei'
import * as THREE from 'three'

// Treemap data type
interface TreemapNode {
  name: string
  value: number
  color?: string
  children?: TreemapNode[]
}

// Generate sample hierarchical data
const generateTreemapData = (): TreemapNode => {
  const domains = ['Analytics', 'Orchestration', 'Learning', 'Memory', 'Agents']
  const heuristics = [
    'Pattern Recognition', 'Decision Making', 'Data Processing',
    'User Interaction', 'System Integration', 'Error Handling',
    'Performance Optimization', 'Security', 'Validation', 'Testing'
  ]
  
  return {
    name: 'ELF System',
    value: 1000,
    children: domains.map((domain, di) => ({
      name: domain,
      value: 100 + Math.random() * 100,
      color: `hsl(${di * 72}, 70%, 50%)`,
      children: heuristics.slice(0, 3 + Math.floor(Math.random() * 4)).map((h, hi) => ({
        name: h,
        value: 10 + Math.random() * 30,
        color: `hsl(${di * 72 + hi * 10}, 70%, ${45 + hi * 5}%)`
      }))
    }))
  }
}

// Squarified Treemap algorithm
function squarify(
  nodes: TreemapNode[],
  x: number,
  y: number,
  width: number,
  height: number
): { node: TreemapNode; x: number; y: number; w: number; h: number }[] {
  if (nodes.length === 0) return []
  
  const total = nodes.reduce((sum, n) => sum + n.value, 0)
  const scale = (width * height) / total
  
  const result: { node: TreemapNode; x: number; y: number; w: number; h: number }[] = []
  
  // Simple slice-and-dice algorithm
  let currentX = x
  let currentY = y
  let remainingWidth = width
  let remainingHeight = height
  
  // Sort by value descending
  const sortedNodes = [...nodes].sort((a, b) => b.value - a.value)
  
  for (const node of sortedNodes) {
    const nodeArea = node.value * scale
    
    if (remainingWidth > remainingHeight) {
      // Horizontal slice
      const nodeWidth = nodeArea / remainingHeight
      result.push({
        node,
        x: currentX,
        y: currentY,
        w: nodeWidth,
        h: remainingHeight
      })
      currentX += nodeWidth
      remainingWidth -= nodeWidth
    } else {
      // Vertical slice
      const nodeHeight = nodeArea / remainingWidth
      result.push({
        node,
        x: currentX,
        y: currentY,
        w: remainingWidth,
        h: nodeHeight
      })
      currentY += nodeHeight
      remainingHeight -= nodeHeight
    }
  }
  
  return result
}

// 3D Box component for treemap
interface BoxProps {
  node: TreemapNode
  position: [number, number, number]
  size: [number, number, number]
  depth: number
  onSelect: (node: TreemapNode) => void
  selected: boolean
}

function TreemapBox({ node, position, size, depth, onSelect, selected }: BoxProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)
  
  const color = useMemo(() => {
    if (node.color) return node.color
    return `hsl(${Math.random() * 360}, 70%, 50%)`
  }, [node.color])
  
  useFrame(() => {
    if (meshRef.current) {
      const targetScale = hovered ? 1.02 : 1
      meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1)
    }
  })
  
  const boxDepth = Math.max(0.5, 3 - depth * 0.5)
  
  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={() => onSelect(node)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry args={[size[0] - 0.1, size[1] - 0.1, boxDepth]} />
        <meshStandardMaterial
          color={color}
          transparent
          opacity={selected ? 1 : 0.85}
          emissive={selected ? color : hovered ? color : '#000000'}
          emissiveIntensity={selected ? 0.3 : hovered ? 0.2 : 0}
        />
      </mesh>
      
      {/* Label */}
      {size[0] > 15 && size[1] > 10 && (
        <Text
          position={[0, 0, boxDepth / 2 + 0.1]}
          fontSize={Math.min(size[0], size[1]) * 0.15}
          color="white"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.5}
          outlineColor="#000000"
        >
          {node.name}
        </Text>
      )}
      
      {/* Value badge */}
      {size[0] > 20 && size[1] > 15 && (
        <Html position={[size[0] / 2 - 3, -size[1] / 2 + 3, boxDepth / 2 + 0.1]}>
          <div className="bg-black/50 text-white text-xs px-2 py-1 rounded">
            {node.value.toFixed(0)}
          </div>
        </Html>
      )}
    </group>
  )
}

// Main 3D Treemap component
interface TreemapViewProps {
  data?: TreemapNode
  onNodeSelect?: (node: TreemapNode) => void
}

export function TreemapView({ data, onNodeSelect }: TreemapViewProps) {
  const [selectedNode, setSelectedNode] = useState<TreemapNode | null>(null)
  const [viewMode, setViewMode] = useState<'3d' | '2d'>('3d')
  
  const treeData = useMemo(() => data || generateTreemapData(), [data])
  
  const handleNodeSelect = useCallback((node: TreemapNode) => {
    setSelectedNode(node)
    onNodeSelect?.(node)
  }, [onNodeSelect])
  
  const layout = useMemo(() => {
    const width = 80
    const height = 60
    
    if (!treeData.children) {
      return [{ node: treeData, x: 0, y: 0, w: width, h: height }]
    }
    
    return squarify(treeData.children, 0, 0, width, height)
  }, [treeData])
  
  return (
    <div className="w-full h-full min-h-[500px] flex flex-col bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">3D Treemap</h3>
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('3d')}
            className={`px-2 py-1 rounded text-xs ${
              viewMode === '3d' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            3D
          </button>
          <button
            onClick={() => setViewMode('2d')}
            className={`px-2 py-1 rounded text-xs ${
              viewMode === '2d' ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            2D
          </button>
        </div>
      </div>
      
      {/* Canvas */}
      <div className="flex-1 min-h-[400px]">
        {viewMode === '3d' ? (
          <Canvas camera={{ position: [0, 0, 120], fov: 50 }}>
            <ambientLight intensity={0.5} />
            <pointLight position={[50, 50, 50]} intensity={1} />
            <pointLight position={[-50, -50, 50]} intensity={0.5} />
            
            <group position={[-40, -30, 0]}>
              {layout.map((item, index) => (
                <TreemapBox
                  key={`${item.node.name}-${index}`}
                  node={item.node}
                  position={[item.x + item.w / 2, item.y + item.h / 2, index * 0.5]}
                  size={[item.w, item.h, 0]}
                  depth={0}
                  onSelect={handleNodeSelect}
                  selected={selectedNode?.name === item.node.name}
                />
              ))}
            </group>
            
            <OrbitControls
              enablePan
              enableZoom
              enableRotate
              minDistance={50}
              maxDistance={200}
            />
          </Canvas>
        ) : (
          <div className="p-2 h-full overflow-auto">
            <div className="grid grid-cols-3 gap-2">
              {layout.map((item, index) => (
                <div
                  key={`${item.node.name}-${index}`}
                  onClick={() => handleNodeSelect(item.node)}
                  className={`p-2 cursor-pointer transition-all hover:scale-[1.02] rounded text-center ${
                    selectedNode?.name === item.node.name ? 'ring-2 ring-blue-500' : ''
                  }`}
                  style={{
                    backgroundColor: item.node.color || `hsl(${index * 60}, 70%, 50%)`
                  }}
                >
                  <div className="text-white font-medium text-xs">{item.node.name}</div>
                  <div className="text-white/70 text-xs">{item.node.value.toFixed(0)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Selected node details */}
      {selectedNode && (
        <div className="p-4 border-t border-slate-700 bg-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-medium">{selectedNode.name}</h4>
              <p className="text-slate-400 text-sm">Value: {selectedNode.value.toFixed(2)}</p>
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
