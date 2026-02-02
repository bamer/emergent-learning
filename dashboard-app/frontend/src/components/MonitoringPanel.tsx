import React, { useState } from 'react';
import {
  Shield, ScrollText, Heart, Eye, Grid, List,
  ChevronDown, ChevronRight, Zap
} from 'lucide-react';
import {
  SentinelMonitorPanel,
  EventChronicleViewer,
  SystemHealthPanel,
  WatcherStatusPanel,
  EventBridgeStatusPanel
} from './monitoring';

interface MonitoringPanelProps {
  apiBaseUrl?: string;
}

type MonitorView = 'sentinel' | 'chronicle' | 'health' | 'watcher' | 'eventbridge' | 'all';

export function MonitoringPanel({ apiBaseUrl = '' }: MonitoringPanelProps) {
  const [activeView, setActiveView] = useState<MonitorView>('all');
  const [layoutMode, setLayoutMode] = useState<'grid' | 'list'>('grid');

  const views = [
    { id: 'sentinel', label: 'Sentinel', icon: Shield, component: SentinelMonitorPanel },
    { id: 'chronicle', label: 'Event Chronicle', icon: ScrollText, component: EventChronicleViewer },
    { id: 'health', label: 'System Health', icon: Heart, component: SystemHealthPanel },
    { id: 'watcher', label: 'Watcher', icon: Eye, component: WatcherStatusPanel },
    { id: 'eventbridge', label: 'Event Bridge', icon: Zap, component: EventBridgeStatusPanel },
  ] as const;

  const ActiveComponent = views.find(v => v.id === activeView)?.component;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 bg-slate-900/50">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-slate-200">System Monitoring</h2>
          
          {/* View Selector */}
          <div className="flex bg-slate-800 rounded-lg p-1">
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeView === 'all' ? (
          layoutMode === 'grid' ? (
            /* Grid Layout - 2x3 */
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 h-full">
              <div className="min-h-[400px]">
                <SentinelMonitorPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="min-h-[400px]">
                <SystemHealthPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="min-h-[400px]">
                <EventBridgeStatusPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="min-h-[400px]">
                <WatcherStatusPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="min-h-[400px]">
                <EventChronicleViewer apiBaseUrl={apiBaseUrl} />
              </div>
            </div>
          ) : (
            /* List Layout - Stacked */
            <div className="space-y-4">
              <div className="h-[500px]">
                <SentinelMonitorPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="h-[500px]">
                <SystemHealthPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="h-[500px]">
                <EventBridgeStatusPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="h-[500px]">
                <WatcherStatusPanel apiBaseUrl={apiBaseUrl} />
              </div>
              <div className="h-[500px]">
                <EventChronicleViewer apiBaseUrl={apiBaseUrl} />
              </div>
            </div>
          )
        ) : (
          /* Single View */
          <div className="h-full">
            {ActiveComponent && <ActiveComponent apiBaseUrl={apiBaseUrl} />}
          </div>
        )}
      </div>
    </div>
  );
}
