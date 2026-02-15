import { useState } from 'react'
import { TreemapView } from './TreemapView'
import { ForceGraph } from './ForceGraph'
import { HeatmapView } from './HeatmapView'
import { GanttChart } from './GanttChart'
import { SankeyDiagram } from './SankeyDiagram'

export type VisualizationType = 'treemap' | 'forcegraph' | 'heatmap' | 'gantt' | 'sankey'

const visualizations: { id: VisualizationType; label: string; icon: string }[] = [
  { id: 'treemap', label: '3D Treemap', icon: '📊' },
  { id: 'forcegraph', label: 'Force Graph', icon: '🔗' },
  { id: 'heatmap', label: 'Heatmap', icon: '🗓️' },
  { id: 'gantt', label: 'Gantt Chart', icon: '📅' },
  { id: 'sankey', label: 'Sankey Diagram', icon: '🔀' },
]

interface AdvancedVisualizationsProps {
  defaultView?: VisualizationType
}

export function AdvancedVisualizations({ defaultView = 'treemap' }: AdvancedVisualizationsProps) {
  const [activeView, setActiveView] = useState<VisualizationType>(defaultView)

  return (
    <div className="w-full h-full flex flex-col bg-slate-900 rounded-lg overflow-hidden">
      {/* Visualization Tabs */}
      <div className="flex items-center gap-1 p-2 border-b border-slate-700 bg-slate-800 overflow-x-auto">
        {visualizations.map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => setActiveView(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeView === id
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <span>{icon}</span>
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Visualization Content */}
      <div className="flex-1 min-h-0">
        {activeView === 'treemap' && <TreemapView />}
        {activeView === 'forcegraph' && <ForceGraph />}
        {activeView === 'heatmap' && <HeatmapView />}
        {activeView === 'gantt' && <GanttChart />}
        {activeView === 'sankey' && <SankeyDiagram />}
      </div>
    </div>
  )
}
