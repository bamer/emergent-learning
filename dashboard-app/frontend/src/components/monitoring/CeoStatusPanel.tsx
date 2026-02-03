import React, { useState, useEffect, useCallback } from 'react';
import {
  User, Inbox, AlertTriangle, CheckCircle, Clock, 
  RefreshCw, Play, Square, Bell, BellOff, ChevronRight, ChevronDown
} from 'lucide-react';

interface CeoItem {
  filename: string;
  title: string;
  priority: string;
  status: string;
  date: string | null;
  summary: string;
  path: string;
}

interface CeoStatusPanelProps {
  apiBaseUrl?: string;
  refreshInterval?: number;
}

const PRIORITY_CONFIG = {
  'Critical': {
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    icon: AlertTriangle,
    label: 'Critical'
  },
  'High': {
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
    icon: AlertTriangle,
    label: 'High'
  },
  'Medium': {
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    icon: Bell,
    label: 'Medium'
  },
  'Low': {
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/20',
    icon: BellOff,
    label: 'Low'
  }
};

export function CeoStatusPanel({
  apiBaseUrl = '',
  refreshInterval = 30000
}: CeoStatusPanelProps) {
  const [items, setItems] = useState<CeoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  const fetchCeoInbox = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/ceo-inbox`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setItems(data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch CEO inbox:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch CEO inbox');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchCeoInbox();
    const interval = setInterval(fetchCeoInbox, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchCeoInbox, refreshInterval]);

  const toggleItem = (filename: string) => {
    setExpandedItem(expandedItem === filename ? null : filename);
  };

  const getPriorityConfig = (priority: string) => {
    // Convertir les priorités du format texte vers les clés du config
    const priorityKey = priority.includes('Critical') ? 'Critical' :
                       priority.includes('High') ? 'High' :
                       priority.includes('Medium') ? 'Medium' : 'Low';
    return PRIORITY_CONFIG[priorityKey] || PRIORITY_CONFIG.Low;
  };

  if (loading && items.length === 0) {
    return (
      <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-700 rounded w-1/3"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
          <div className="h-4 bg-slate-700 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 backdrop-blur-sm rounded-xl border border-red-700/50 p-6">
        <div className="flex items-center gap-3 text-red-400">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div>
            <div className="font-medium">Error Loading CEO Inbox</div>
            <div className="text-sm text-red-300 mt-1">{error}</div>
          </div>
        </div>
        <button
          onClick={fetchCeoInbox}
          className="mt-4 flex items-center gap-2 text-sm text-red-300 hover:text-red-200 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    );
  }

  const pendingItems = items.filter(item => item.status === 'Pending');
  const criticalItems = pendingItems.filter(item => item.priority.includes('Critical') || item.priority.includes('High'));
  
  const StatusIcon = pendingItems.length > 0 ? AlertTriangle : CheckCircle;

  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`${pendingItems.length > 0 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'} p-2 rounded-lg border`}>
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">CEO Status</h3>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              {pendingItems.length > 0 ? (
                <span className="text-amber-400">
                  {pendingItems.length} pending escalations
                </span>
              ) : (
                <span className="text-emerald-400">All clear</span>
              )}
              {lastUpdate && (
                <span>• Updated {lastUpdate.toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchCeoInbox}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
            aria-label="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
            aria-label="Toggle CEO Agent"
          >
            <Play className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-white">{pendingItems.length}</div>
          <div className="text-sm text-slate-400">Pending</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-amber-400">{criticalItems.length}</div>
          <div className="text-sm text-slate-400">Critical</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-2xl font-bold text-emerald-400">{items.length - pendingItems.length}</div>
          <div className="text-sm text-slate-400">Resolved</div>
        </div>
      </div>

      {/* Pending Items List */}
      {pendingItems.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
            <Inbox className="w-4 h-4" />
            Pending Escalations
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
            {pendingItems.map((item) => {
              const isExpanded = expandedItem === item.filename;
              const priorityConfig = getPriorityConfig(item.priority);
              const PriorityIcon = priorityConfig.icon;

              return (
                <div
                  key={item.filename}
                  className="bg-slate-800/30 hover:bg-slate-800/50 rounded-lg border border-slate-700/30 transition-colors"
                >
                  <button
                    onClick={() => toggleItem(item.filename)}
                    className="w-full p-3 text-left flex items-start justify-between"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div className={`${priorityConfig.bgColor} ${priorityConfig.borderColor} p-1 rounded mt-0.5`}>
                        <PriorityIcon className={`w-3 h-3 ${priorityConfig.color}`} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-white truncate">
                          {item.title}
                        </div>
                        <div className="text-xs text-slate-400">
                          {item.date || 'No date'}
                        </div>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0 mt-1" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0 mt-1" />
                    )}
                  </button>
                  
                  {isExpanded && (
                    <div className="px-3 pb-3 pt-1 border-t border-slate-700/30">
                      <div className="text-xs text-slate-300">
                        {item.summary || 'No summary available'}
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs">
                        <span className={`${priorityConfig.bgColor} ${priorityConfig.borderColor} ${priorityConfig.color} px-2 py-1 rounded`}>
                          {priorityConfig.label}
                        </span>
                        <span className="text-slate-500">
                          {item.filename}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {pendingItems.length === 0 && (
        <div className="text-center py-8 text-slate-400">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-400/20" />
          <p className="text-sm">No pending escalations</p>
          <p className="text-xs mt-1">System operating normally</p>
        </div>
      )}
    </div>
  );
}