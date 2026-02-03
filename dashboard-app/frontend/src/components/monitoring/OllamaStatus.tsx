import React, { useState, useEffect } from 'react';
import { Brain, CheckCircle, XCircle, AlertCircle, RefreshCw, Zap, Database } from 'lucide-react';

interface OllamaStatusData {
  status: string;
  service_running: boolean;
  embedding_status: 'working' | 'error' | 'failed' | 'not_tested';
  models_available: string[];
  embedding_model?: string | null;
  service_url: string;
  last_checked: string;
  error?: string;
}

interface OllamaStatusProps {
  apiBaseUrl?: string;
}

export function OllamaStatus({ apiBaseUrl = '' }: OllamaStatusProps) {
  const [status, setStatus] = useState<OllamaStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/monitoring/ollama/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'ok' || data.status === 'error') {
        setStatus(data);
        setLastUpdate(new Date());
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      console.error('Failed to fetch Ollama status:', err);
      setError(err instanceof Error ? err.message : 'Failed to load status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    
    return () => clearInterval(interval);
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