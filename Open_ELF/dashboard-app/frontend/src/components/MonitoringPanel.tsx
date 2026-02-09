import React, { useState } from 'react';
import {
  Shield, ScrollText, Heart, Grid, List,
  Zap, Cpu, Brain, User,
  Layers
} from 'lucide-react';
import {
  WatcherMonitorPanel,
  EventChronicleViewer,
  SystemHealthPanel,
  EventBridgeStatusPanel,
  OrchestratorStatusPanel,
  OllamaStatus,
  CeoStatusPanel
} from './monitoring';

interface MonitoringPanelProps {
  apiBaseUrl?: string;
}

type MonitorView = 'sentinel' | 'chronicle' | 'health' | 'eventbridge' | 'orchestrator' | 'ceo' | 'ollama' | 'all';

export function MonitoringPanel({ apiBaseUrl = '' }: MonitoringPanelProps) {
  const [activeView, setActiveView] = useState<MonitorView>('all');
  const [layoutMode, setLayoutMode] = useState<'grid' | 'list'>('grid');

  const views = [
    { id: 'sentinel', label: 'Watcher/Sentinel (L1)', icon: Shield, component: WatcherMonitorPanel, description: 'Merged Watcher + Sentinel - Level 1 Agent' },
    { id: 'eventbridge', label: 'EventBridge v2', icon: Zap, component: EventBridgeStatusPanel, description: 'Event processing and tool detection' },
    { id: 'orchestrator', label: 'Orchestrator (L2)', icon: Cpu, component: OrchestratorStatusPanel, description: 'Task coordination and workflow management' },
    { id: 'ceo', label: 'CEO (L3)', icon: User, component: CeoStatusPanel, description: 'Strategic decisions and approvals' },
    { id: 'health', label: 'System Health', icon: Heart, component: SystemHealthPanel, description: 'Overall system health and metrics' },
    { id: 'chronicle', label: 'Event Chronicle', icon: ScrollText, component: EventChronicleViewer, description: 'Historical event log' },
    { id: 'ollama', label: 'Ollama', icon: Brain, component: OllamaStatus, description: 'AI/LLM service status' },
  ] as const;

  const ActiveComponent = views.find(v => v.id === activeView)?.component;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-900/50">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-slate-200">System Monitoring</h2>
          
          {/* View Selector */}
          <div className="flex bg-slate-800 rounded-lg p-1 flex-wrap gap-1">
            <button
              onClick={() => setActiveView('all')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                activeView === 'all'
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            {views.map(view => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id as MonitorView)}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
                  activeView === view.id
                    ? 'bg-violet-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title={view.description}
              >
                <view.icon className="w-3.5 h-3.5" />
                {view.label}
              </button>
            ))}
          </div>
        </div>

        {/* Layout Toggle (only for 'all' view) */}
        {activeView === 'all' && (
          <div className="flex bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setLayoutMode('grid')}
              className={`p-1.5 rounded transition-colors ${
                layoutMode === 'grid'
                  ? 'bg-slate-700 text-slate-200'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Grid layout"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayoutMode('list')}
              className={`p-1.5 rounded transition-colors ${
                layoutMode === 'list'
                  ? 'bg-slate-700 text-slate-200'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="List layout"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Architecture Legend */}
      {activeView === 'all' && (
        <div className="px-4 py-2 border-b border-slate-700/50 bg-slate-800/30">
          <div className="flex items-center gap-6 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>3-Level Agent Hierarchy:</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-violet-400" />
              <span className="text-violet-400">L1: Watcher/Sentinel</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-amber-400">L2: Orchestrator</span>
            </span>
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">L3: CEO</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-400">EventBridge v2</span>
            </span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeView === 'all' ? (
          layoutMode === 'grid' ? (
            /* Grid Layout - 2x4 */
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {/* L1: Watcher/Sentinel (Merged) */}
              <div className="min-h-[400px] lg:col-span-2 xl:col-span-1">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <Shield className="w-4 h-4 text-violet-400" />
                    <span className="text-xs font-medium text-violet-400">L1 Agent</span>
                    <span className="text-xs text-slate-500">- Watcher + Sentinel (Merged)</span>
                  </div>
                  <WatcherMonitorPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* EventBridge v2 */}
              <div className="min-h-[400px]">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <Zap className="w-4 h-4 text-rose-400" />
                    <span className="text-xs font-medium text-rose-400">Event Processing</span>
                    <span className="text-xs text-slate-500">- EventBridge v2</span>
                  </div>
                  <EventBridgeStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* L2: Orchestrator */}
              <div className="min-h-[400px]">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <Cpu className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-medium text-amber-400">L2 Agent</span>
                    <span className="text-xs text-slate-500">- Orchestrator</span>
                  </div>
                  <OrchestratorStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* L3: CEO */}
              <div className="min-h-[400px]">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <User className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-medium text-emerald-400">L3 Agent</span>
                    <span className="text-xs text-slate-500">- CEO</span>
                  </div>
                  <CeoStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* System Health */}
              <div className="min-h-[400px]">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <Heart className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-medium text-cyan-400">Infrastructure</span>
                    <span className="text-xs text-slate-500">- System Health</span>
                  </div>
                  <SystemHealthPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* Ollama */}
              <div className="min-h-[400px]">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <Brain className="w-4 h-4 text-pink-400" />
                    <span className="text-xs font-medium text-pink-400">AI Services</span>
                    <span className="text-xs text-slate-500">- Ollama</span>
                  </div>
                  <OllamaStatus apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* Event Chronicle - Full width */}
              <div className="min-h-[400px] lg:col-span-2 xl:col-span-3">
                <div className="h-full">
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <ScrollText className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-medium text-blue-400">Event Log</span>
                    <span className="text-xs text-slate-500">- Event Chronicle</span>
                  </div>
                  <EventChronicleViewer apiBaseUrl={apiBaseUrl} />
                </div>
              </div>
            </div>
          ) : (
            /* List Layout - Stacked with hierarchy indicators */
            <div className="space-y-6">
              {/* L1: Watcher/Sentinel (Merged) */}
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-violet-500/20">
                    <Shield className="w-4 h-4 text-violet-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-violet-400">Level 1: Watcher/Sentinel (Merged)</span>
                    <p className="text-xs text-slate-500">Session monitoring, tool detection, and initial processing</p>
                  </div>
                </div>
                <div className="h-[400px] ml-4 pl-4 border-l-2 border-violet-500/30">
                  <WatcherMonitorPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* EventBridge v2 */}
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-rose-500/20">
                    <Zap className="w-4 h-4 text-rose-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-rose-400">EventBridge v2</span>
                    <p className="text-xs text-slate-500">SSE event streaming and tool usage detection</p>
                  </div>
                </div>
                <div className="h-[400px] ml-4 pl-4 border-l-2 border-rose-500/30">
                  <EventBridgeStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* L2: Orchestrator */}
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-500/20">
                    <Cpu className="w-4 h-4 text-amber-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-amber-400">Level 2: Orchestrator</span>
                    <p className="text-xs text-slate-500">Task coordination and workflow management</p>
                  </div>
                </div>
                <div className="h-[400px] ml-4 pl-4 border-l-2 border-amber-500/30">
                  <OrchestratorStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* L3: CEO */}
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-500/20">
                    <User className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-emerald-400">Level 3: CEO</span>
                    <p className="text-xs text-slate-500">Strategic decisions and high-level approvals</p>
                  </div>
                </div>
                <div className="h-[400px] ml-4 pl-4 border-l-2 border-emerald-500/30">
                  <CeoStatusPanel apiBaseUrl={apiBaseUrl} />
                </div>
              </div>

              {/* System Health */}
              <div className="h-[400px]">
                <SystemHealthPanel apiBaseUrl={apiBaseUrl} />
              </div>

              {/* Ollama */}
              <div className="h-[400px]">
                <OllamaStatus apiBaseUrl={apiBaseUrl} />
              </div>

              {/* Event Chronicle */}
              <div className="h-[500px] overflow-hidden">
                <EventChronicleViewer apiBaseUrl={apiBaseUrl} />
              </div>
            </div>
          )
        ) : (
          /* Single View */
          <div className="h-full">
            {activeView === 'sentinel' && (
              <div className="mb-4 p-4 bg-violet-500/10 border border-violet-500/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Shield className="w-6 h-6 text-violet-400" />
                  <div>
                    <h3 className="text-lg font-semibold text-violet-400">Watcher/Sentinel (Level 1 Agent)</h3>
                    <p className="text-sm text-slate-400">
                      Merged component handling session monitoring, SSE event processing, and tool detection.
                      Previously separate Watcher and Sentinel components have been unified.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {activeView === 'eventbridge' && (
              <div className="mb-4 p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Zap className="w-6 h-6 text-rose-400" />
                  <div>
                    <h3 className="text-lg font-semibold text-rose-400">EventBridge v2</h3>
                    <p className="text-sm text-slate-400">
                      Processes SSE events from OpenCode, detects tool usage via message.part.updated events,
                      and triggers learning operations through the LearningProcessor.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {activeView === 'orchestrator' && (
              <div className="mb-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <Cpu className="w-6 h-6 text-amber-400" />
                  <div>
                    <h3 className="text-lg font-semibold text-amber-400">Orchestrator (Level 2 Agent)</h3>
                    <p className="text-sm text-slate-400">
                      Coordinates tasks and workflows across the system. Receives escalations from Level 1
                      and manages multi-step operations.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {activeView === 'ceo' && (
              <div className="mb-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <User className="w-6 h-6 text-emerald-400" />
                  <div>
                    <h3 className="text-lg font-semibold text-emerald-400">CEO (Level 3 Agent)</h3>
                    <p className="text-sm text-slate-400">
                      Strategic decision making and high-level approvals. Receives escalations from Level 2
                      for critical decisions requiring human oversight.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {ActiveComponent && <ActiveComponent apiBaseUrl={apiBaseUrl} />}
          </div>
        )}
      </div>
    </div>
  );
}
