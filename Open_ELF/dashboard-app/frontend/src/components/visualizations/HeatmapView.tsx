import { useMemo, useState } from 'react'
import * as d3 from 'd3'

// Heatmap data types
interface HeatmapCell {
  row: string
  col: string
  value: number
}

interface HeatmapData {
  rows: string[]
  cols: string[]
  cells: HeatmapCell[]
}

// Generate sample heatmap data
const generateHeatmapData = (): HeatmapData => {
  const rows = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const cols = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
  
  const cells: HeatmapCell[] = []
  
  // Simulate activity patterns
  rows.forEach(row => {
    cols.forEach(col => {
      let baseValue = 20
      
      // Higher activity during work hours
      if (col >= '08:00' && col <= '20:00') {
        baseValue += 30
      }
      
      // Higher on weekdays
      if (row !== 'Sat' && row !== 'Sun') {
        baseValue += 20
      }
      
      // Add some randomness
      const value = Math.max(0, Math.min(100, baseValue + (Math.random() - 0.5) * 40))
      
      cells.push({ row, col, value })
    })
  })
  
  return { rows, cols, cells }
}

// Color scale
const colorScale = d3.scaleSequential(d3.interpolateViridis).domain([0, 100])

// Main Heatmap component
interface HeatmapViewProps {
  data?: HeatmapData
  onCellSelect?: (cell: HeatmapCell) => void
  title?: string
}

export function HeatmapView({ data, onCellSelect, title = 'Activity Heatmap' }: HeatmapViewProps) {
  const [hoveredCell, setHoveredCell] = useState<HeatmapCell | null>(null)
  const [selectedCell, setSelectedCell] = useState<HeatmapCell | null>(null)
  
  const heatmapData = useMemo(() => data || generateHeatmapData(), [data])
  
  const handleCellClick = (cell: HeatmapCell) => {
    setSelectedCell(cell)
    onCellSelect?.(cell)
  }
  
  // Calculate row and column totals
  const rowTotals = useMemo(() => {
    const totals: Record<string, number> = {}
    heatmapData.rows.forEach(row => {
      const rowCells = heatmapData.cells.filter(c => c.row === row)
      totals[row] = rowCells.reduce((sum, c) => sum + c.value, 0) / rowCells.length
    })
    return totals
  }, [heatmapData])
  
  const colTotals = useMemo(() => {
    const totals: Record<string, number> = {}
    heatmapData.cols.forEach(col => {
      const colCells = heatmapData.cells.filter(c => c.col === col)
      totals[col] = colCells.reduce((sum, c) => sum + c.value, 0) / colCells.length
    })
    return totals
  }, [heatmapData])
  
  return (
    <div className="w-full h-full min-h-[300px] flex flex-col bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        <div className="flex items-center gap-1">
          <span className="text-xs text-slate-400">Low</span>
          <div className="w-16 h-2 rounded" style={{
            background: `linear-gradient(to right, ${colorScale(0)}, ${colorScale(50)}, ${colorScale(100)})`
          }}></div>
          <span className="text-xs text-slate-400">High</span>
        </div>
      </div>
      
      {/* Heatmap Grid */}
      <div className="flex-1 min-h-0 p-2 overflow-auto">
        <div className="inline-block">
          {/* Column headers */}
          <div className="flex ml-12 mb-1">
            {heatmapData.cols.map(col => (
              <div
                key={col}
                className="flex-shrink-0 text-xs text-slate-400 text-center px-1"
                style={{ width: 60 }}
              >
                {col}
              </div>
            ))}
            <div className="flex-shrink-0 text-xs text-slate-400 text-center px-1 ml-2" style={{ width: 50 }}>
              Avg
            </div>
          </div>
          
          {/* Rows */}
          {heatmapData.rows.map(row => (
            <div key={row} className="flex items-center mb-1">
              {/* Row label */}
              <div className="w-10 text-xs text-slate-400 text-right mr-2">{row}</div>
              
              {/* Cells */}
              {heatmapData.cols.map(col => {
                const cell = heatmapData.cells.find(c => c.row === row && c.col === col)
                if (!cell) return null
                
                const isHovered = hoveredCell?.row === row && hoveredCell?.col === col
                const isSelected = selectedCell?.row === row && selectedCell?.col === col
                
                return (
                  <div
                    key={`${row}-${col}`}
                    className={`flex-shrink-0 mx-0.5 rounded cursor-pointer transition-all ${
                      isSelected ? 'ring-2 ring-white' : ''
                    } ${isHovered ? 'transform scale-110 z-10' : ''}`}
                    style={{
                      width: 56,
                      height: 40,
                      backgroundColor: colorScale(cell.value)
                    }}
                    onMouseEnter={() => setHoveredCell(cell)}
                    onMouseLeave={() => setHoveredCell(null)}
                    onClick={() => handleCellClick(cell)}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-xs font-medium text-white drop-shadow-md">
                        {cell.value.toFixed(0)}
                      </span>
                    </div>
                  </div>
                )
              })}
              
              {/* Row average */}
              <div className="flex-shrink-0 text-xs text-slate-300 text-center ml-2" style={{ width: 50 }}>
                {rowTotals[row].toFixed(0)}
              </div>
            </div>
          ))}
          
          {/* Column averages */}
          <div className="flex items-center mt-2 pt-2 border-t border-slate-700">
            <div className="w-10 text-xs text-slate-400 text-right mr-2">Avg</div>
            {heatmapData.cols.map(col => (
              <div
                key={`avg-${col}`}
                className="flex-shrink-0 text-xs text-slate-300 text-center mx-0.5"
                style={{ width: 56 }}
              >
                {colTotals[col].toFixed(0)}
              </div>
            ))}
            <div className="flex-shrink-0 text-xs text-white text-center ml-2 font-medium" style={{ width: 50 }}>
              {(Object.values(rowTotals).reduce((a, b) => a + b, 0) / Object.values(rowTotals).length).toFixed(0)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Selected cell details */}
      {(selectedCell || hoveredCell) && (
        <div className="p-4 border-t border-slate-700 bg-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-medium">
                {selectedCell?.row || hoveredCell?.row} at {selectedCell?.col || hoveredCell?.col}
              </h4>
              <p className="text-slate-400 text-sm">
                Activity Level: {(selectedCell?.value || hoveredCell?.value)?.toFixed(1)}
              </p>
            </div>
            <button
              onClick={() => setSelectedCell(null)}
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
