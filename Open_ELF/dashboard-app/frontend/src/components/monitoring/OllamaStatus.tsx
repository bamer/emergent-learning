import React, { useState, useEffect, useRef } from 'react';
import { Brain, CheckCircle, XCircle, AlertCircle, RefreshCw, Zap, Database, BarChart3, Clock, FileText, TrendingUp } from 'lucide-react';

interface EmbeddingStats {
  total_embeddings: number;
  timeframe_stats: {
    last_hour: number;
    last_6_hours: number;
    last_24_hours: number;
    last_7_days: number;
    last_30_days: number;
  };
  by_source_type: Record<string, number>;
  by_hour: Array<{ hour: string; count: number }>;
  by_day: Array<{ day: string; count: number }>;
  recent_embeddings: Array<{
    id: number;
    source_type: string;
    content_preview: string;
    created_at: string;
  }>;
  average_length: number;
  oldest: string | null;
  newest: string | null;
  embedding_dimension: number;
}

interface OllamaStatusData {
  status: string;
  service_running: boolean;
  embedding_status: 'working' | 'error' | 'failed' | 'not_tested';
  models_available: string[];
  embedding_model?: string | null;
  service_url: string;
  last_checked: string;
  error?: string;
  embedding_stats?: EmbeddingStats;
}

interface OllamaStatusProps {
  apiBaseUrl?: string;
}

export function OllamaStatus({ apiBaseUrl = '' }: OllamaStatusProps) {
  const [status, setStatus] = useState<OllamaStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const isMountedRef = useRef(true);
  const isInitialLoadRef = useRef(true);

  const fetchStatus = async () => {
    if (!isMountedRef.current) return;
    
    const isInitialLoad = isInitialLoadRef.current;
    
    try {
      if (isInitialLoad) {
        setLoading(true);
      }
      
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/ollama/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'ok' || data.status === 'error') {
        setStatus(data);
        setLastUpdate(new Date());
        
        // Mark initial load as complete
        if (isInitialLoadRef.current) {
          isInitialLoadRef.current = false;
        }
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Failed to fetch Ollama status:', err);
      setError(err instanceof Error ? err.message : 'Failed to load status');
    } finally {
      if (!isMountedRef.current) return;
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    
    fetchStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    
    return () => {
      isMountedRef.current = false;
      clearInterval(interval);
    };
  }, [apiBaseUrl]);

  const getServiceStatusIcon = (running: boolean) => {
    if (running) {
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    } else {
      return <XCircle className="w-5 h-5 text-red-400" />;
    }
  };

  const getServiceStatusColor = (running: boolean) => {
    return running ? 'text-green-400' : 'text-red-400';
  };

  const getEmbeddingStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    }
  };

  const getEmbeddingStatusColor = (status: string) => {
    switch (status) {
      case 'working':
        return 'text-green-400';
      case 'error':
      case 'failed':
        return 'text-red-400';
      default:
        return 'text-yellow-400';
    }
  };

  const getEmbeddingStatusText = (status: string) => {
    switch (status) {
      case 'working':
        return 'Working';
      case 'error':
        return 'Error';
      case 'failed':
        return 'Failed';
      case 'not_tested':
        return 'Not Tested';
      default:
        return 'Unknown';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/50 border border-slate-700/50 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-slate-200">Ollama Embeddings</h3>
        </div>
        
        <div className="flex items-center gap-2">
          {lastUpdate && (
            <span className="text-xs text-slate-400">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && !status ? (
          <div className="flex items-center justify-center h-32">
            <div className="flex items-center gap-2 text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Checking status...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-400 text-sm mb-2">{error}</p>
              <button
                onClick={fetchStatus}
                className="px-3 py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded text-sm transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : !status ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <Brain className="w-8 h-8 text-slate-500 mx-auto mb-2" />
              <p className="text-slate-400 text-sm">No status data available</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Service Status */}
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-slate-200">Service Status</h4>
                <div className="flex items-center gap-2">
                  {getServiceStatusIcon(status.service_running)}
                  <span className={`text-sm font-medium ${getServiceStatusColor(status.service_running)}`}>
                    {status.service_running ? 'Running' : 'Stopped'}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Service URL:</span>
                  <span className="text-slate-300 font-mono text-xs">{status.service_url}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Embedding Status:</span>
                  <div className="flex items-center gap-1">
                    {getEmbeddingStatusIcon(status.embedding_status)}
                    <span className={`text-sm font-medium ${getEmbeddingStatusColor(status.embedding_status)}`}>
                      {getEmbeddingStatusText(status.embedding_status)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Models */}
            <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
              <div className="flex items-center gap-2 mb-3">
                <Database className="w-4 h-4 text-blue-400" />
                <h4 className="text-sm font-medium text-slate-200">Available Models</h4>
              </div>
              
              {status.models_available.length > 0 ? (
                <div className="space-y-2">
                  {status.models_available.map((model, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between p-2 rounded ${
                        model.includes('nomic-embed')
                          ? 'bg-green-900/20 border border-green-700/30'
                          : 'bg-slate-700/30'
                      }`}
                    >
                      <span className="text-sm text-slate-300 font-mono">{model}</span>
                      {model.includes('nomic-embed') && (
                        <span className="text-xs bg-green-600/20 text-green-400 px-2 py-0.5 rounded">
                          Embedding Model
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400 text-sm">No models available</p>
              )}
            </div>

            {/* Embedding Statistics Overview */}
            {status.embedding_stats && (
              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="w-4 h-4 text-purple-400" />
                  <h4 className="text-sm font-medium text-slate-200">Embedding Statistics</h4>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Total Embeddings</div>
                    <div className="text-2xl font-bold text-slate-100">
                      {status.embedding_stats.total_embeddings.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Dimensions</div>
                    <div className="text-2xl font-bold text-slate-100">
                      {status.embedding_stats.embedding_dimension}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Avg Text Length</div>
                    <div className="text-lg font-semibold text-slate-100">
                      {status.embedding_stats.average_length.toLocaleString()} chars
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Oldest Embed</div>
                    <div className="text-xs text-slate-300">
                      {status.embedding_stats.oldest 
                        ? new Date(status.embedding_stats.oldest).toLocaleDateString()
                        : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Embedding Rate by Time */}
            {status.embedding_stats && (
              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                  <h4 className="text-sm font-medium text-slate-200">Embedding Rate</h4>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400">Last Hour</span>
                    <span className="text-sm font-medium text-slate-300">{status.embedding_stats.timeframe_stats?.last_hour || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400">Last 6 Hours</span>
                    <span className="text-sm font-medium text-slate-300">{status.embedding_stats.timeframe_stats?.last_6_hours || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400">Last 24 Hours</span>
                    <span className="text-sm font-medium text-slate-300">{status.embedding_stats.timeframe_stats?.last_24_hours || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400">Last 7 Days</span>
                    <span className="text-sm font-medium text-slate-300">{status.embedding_stats.timeframe_stats?.last_7_days || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400">Last 30 Days</span>
                    <span className="text-sm font-medium text-slate-300">{status.embedding_stats.timeframe_stats?.last_30_days || 0}</span>
                  </div>

                  {/* Indicator for recent activity */}
                  <div className={`mt-2 pt-2 border-t border-slate-700/50 ${
                    (status.embedding_stats.timeframe_stats?.last_24_hours || 0) > 0
                      ? 'text-green-400'
                      : 'text-yellow-400'
                  }`}>
                    <Clock className="w-3 h-3 inline mr-1" />
                    <span className="text-xs">
                      {(status.embedding_stats.timeframe_stats?.last_24_hours || 0) > 0
                        ? '✓ Active in last 24h'
                        : '⚠ No activity in 24h'
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* By Source Type */}
            {status.embedding_stats && Object.keys(status.embedding_stats.by_source_type || {}).length > 0 && (
              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-green-400" />
                  <h4 className="text-sm font-medium text-slate-200">By Source Type</h4>
                </div>
                
                <div className="space-y-2">
                  {Object.entries(status.embedding_stats.by_source_type).map(([source, count]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className="text-sm text-slate-300 capitalize">{source}</span>
                      <span className="text-sm font-mono text-slate-400">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Embeddings */}
            {status.embedding_stats && (status.embedding_stats.recent_embeddings || []).length > 0 && (
              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="w-4 h-4 text-orange-400" />
                  <h4 className="text-sm font-medium text-slate-200">Recent Embeddings (Last 10)</h4>
                </div>
                
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {status.embedding_stats.recent_embeddings.map((emb, index) => (
                    <div key={emb.id} className="p-2 bg-slate-700/30 rounded border border-slate-600/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-slate-400 font-mono">#{emb.id}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          emb.source_type === 'python' ? 'bg-blue-900/20 text-blue-400' :
                          emb.source_type === 'heuristic' ? 'bg-green-900/20 text-green-400' :
                          emb.source_type === 'bash' ? 'bg-yellow-900/20 text-yellow-400' :
                          'bg-slate-700/50 text-slate-400'
                        }`}>
                          {emb.source_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 truncate">
                        {emb.content_preview}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {emb.created_at ? new Date(emb.created_at).toLocaleString() : 'Unknown'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Embedding Model Details */}
            {status.embedding_model && (
              <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <h4 className="text-sm font-medium text-slate-200">Active Embedding Model</h4>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300 font-mono">{status.embedding_model}</span>
                  <CheckCircle className="w-4 h-4 text-green-400" />
                </div>
              </div>
            )}

            {/* Error Details */}
            {status.error && (
              <div className="bg-red-900/20 rounded-lg p-4 border border-red-700/30">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <h4 className="text-sm font-medium text-red-300">Error Details</h4>
                </div>
                <p className="text-sm text-red-200">{status.error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-900/50">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Last checked: {status ? formatTimestamp(status.last_checked) : 'Never'}</span>
          <span>Auto-refresh: 30s</span>
        </div>
      </div>
    </div>
  );
}