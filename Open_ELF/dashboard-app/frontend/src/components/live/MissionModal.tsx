import React, { useState, useEffect } from 'react';
import { X, Zap, Play, RefreshCw, Cpu, Activity, Code, Search, Lightbulb, FileCode, Sparkles, Wand2 } from 'lucide-react';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  provider_id: string;
  is_default?: boolean;
}

interface PromptCategory {
  category: string;
  icon: React.ComponentType<{ className?: string }>;
  prompts: {
    label: string;
    text: string;
  }[];
}

interface MissionResult {
  mode: string;
  agent_type?: string;
  heuristics_count: number;
  execution_time_ms: number;
  response_preview?: string;
}

interface MissionModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiBaseUrl: string;
  selectedAgentName?: string | null;
}

const PROMPT_CATEGORIES: PromptCategory[] = [
  {
    category: 'Code',
    icon: Code,
    prompts: [
      { label: 'Analyze Code', text: 'Analyze this code for quality, performance issues, and potential bugs. Provide specific recommendations for improvement.' },
      { label: 'Refactor Code', text: 'Refactor this code to improve readability, maintainability, and performance while preserving functionality.' },
      { label: 'Add Tests', text: 'Write comprehensive unit tests for this code, covering edge cases and error scenarios.' },
      { label: 'Code Review', text: 'Perform a thorough code review, checking for best practices, security issues, and architectural concerns.' },
      { label: 'Optimize Performance', text: 'Optimize this code for better performance. Identify bottlenecks and suggest improvements.' },
      { label: 'Modernize Code', text: 'Modernize this legacy code using current best practices and design patterns.' },
    ]
  },
  {
    category: 'Debug',
    icon: Search,
    prompts: [
      { label: 'Debug Issue', text: 'Help me debug this issue. Analyze the error messages and code to find the root cause.' },
      { label: 'Trace Bug', text: 'Trace through this bug step by step. Identify where the logic fails and why.' },
      { label: 'Fix Error', text: 'Fix this error in the code. Provide a working solution with explanation.' },
      { label: 'Investigate Crash', text: 'Investigate why this code is crashing. Analyze stack traces and provide a fix.' },
      { label: 'Memory Leak', text: 'Find and fix any memory leaks in this code. Explain the issue and solution.' },
    ]
  },
  {
    category: 'Create',
    icon: FileCode,
    prompts: [
      { label: 'New Feature', text: 'Implement a new feature with clean, maintainable code. Include error handling and documentation.' },
      { label: 'Build Component', text: 'Create a reusable component with proper props, styling, and accessibility features.' },
      { label: 'API Endpoint', text: 'Design and implement a REST API endpoint with proper validation, error handling, and documentation.' },
      { label: 'Database Schema', text: 'Design a database schema for this feature. Include tables, relationships, and indexes.' },
      { label: 'Setup Project', text: 'Set up a new project with proper structure, configuration, and tooling.' },
    ]
  },
  {
    category: 'Architecture',
    icon: Wand2,
    prompts: [
      { label: 'System Design', text: 'Design a system architecture for this feature. Consider scalability, reliability, and maintainability.' },
      { label: 'Review Architecture', text: 'Review this architecture. Identify potential issues and suggest improvements.' },
      { label: 'Migrate Service', text: 'Plan the migration of this service to a new architecture with minimal downtime.' },
      { label: 'Scale Solution', text: 'Design a scaling strategy for this system. Consider load balancing, caching, and database optimization.' },
    ]
  },
  {
    category: 'Documentation',
    icon: Sparkles,
    prompts: [
      { label: 'Write Docs', text: 'Write comprehensive documentation for this code, including usage examples and API references.' },
      { label: 'Add Comments', text: 'Add helpful comments to this code explaining complex logic and assumptions.' },
      { label: 'README', text: 'Create a README file with setup instructions, usage guide, and contribution guidelines.' },
      { label: 'API Docs', text: 'Generate API documentation with endpoints, parameters, and example responses.' },
    ]
  },
  {
    category: 'Learning',
    icon: Lightbulb,
    prompts: [
      { label: 'Explain Code', text: 'Explain how this code works in detail. Break down complex concepts and logic.' },
      { label: 'Teach Concept', text: 'Teach me the concepts used in this code. Explain the theory and practical application.' },
      { label: 'Compare Approaches', text: 'Compare different approaches to solving this problem. Discuss trade-offs and best practices.' },
      { label: 'Best Practices', text: 'Review this code against industry best practices. Explain what should be changed and why.' },
    ]
  },
];

export function MissionModal({ isOpen, onClose, apiBaseUrl, selectedAgentName }: MissionModalProps) {
  const [missionText, setMissionText] = useState('');
  const [executionMode, setExecutionMode] = useState<'smart' | 'auto' | 'swarm' | 'manual'>('smart');
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<MissionResult | null>(null);
  const [modalKey, setModalKey] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<string>('Code');
  const [selectedPrompt, setSelectedPrompt] = useState<string>('');

  // Fetch available models
  useEffect(() => {
    if (!isOpen) return;
    
    const fetchModels = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/agents/models`);
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(data.models || []);
          const defaultModel = data.models?.find((m: ModelInfo) => m.is_default);
          if (defaultModel) {
            setSelectedModel(defaultModel.id);
          } else if (data.models?.length > 0) {
            setSelectedModel(data.models[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to fetch models:', err);
      }
    };
    fetchModels();
  }, [isOpen, apiBaseUrl]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setMissionText('');
      setExecutionMode('smart');
      setLastResult(null);
      setSelectedCategory('Code');
      setSelectedPrompt('');
      setModalKey(prev => prev + 1);
    }
  }, [isOpen]);

  // Update mission text when prompt selection changes
  useEffect(() => {
    if (selectedPrompt) {
      const category = PROMPT_CATEGORIES.find(c => c.category === selectedCategory);
      const prompt = category?.prompts.find(p => p.label === selectedPrompt);
      if (prompt) {
        setMissionText(prompt.text);
      }
    }
  }, [selectedPrompt, selectedCategory]);

  const executeMission = async () => {
    if (!missionText.trim()) return;
    
    setIsExecuting(true);
    setLastResult(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/agents/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mission: missionText,
          mode: executionMode,
          agent_type: selectedAgentName || undefined,
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setLastResult(result);
      } else {
        console.error('Mission execution failed:', await response.text());
      }
    } catch (err) {
      console.error('Failed to execute mission:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const currentCategory = PROMPT_CATEGORIES.find(c => c.category === selectedCategory);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 overflow-hidden">
      <div key={modalKey} className="bg-slate-800 rounded-lg border border-slate-700 p-6 w-full max-w-3xl max-h-[85vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-violet-400" />
            New Mission
            {selectedAgentName && (
              <span className="text-sm px-2 py-0.5 bg-violet-500/20 text-violet-400 rounded">
                {selectedAgentName}
              </span>
            )}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Execution Mode */}
        <div className="mb-4">
          <label className="block text-sm text-slate-400 mb-2">Execution Mode</label>
          <div className="flex gap-2 flex-wrap">
            {[
              { id: 'smart', label: 'Smart', desc: 'Auto-detect if swarm needed' },
              { id: 'auto', label: 'Auto', desc: 'Select best single agent' },
              { id: 'swarm', label: 'Swarm', desc: 'Multi-agent parallel' },
              { id: 'manual', label: 'Manual', desc: 'Specific agent' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => setExecutionMode(mode.id as any)}
                disabled={mode.id === 'manual' && !selectedAgentName}
                className={`px-3 py-1.5 rounded text-sm ${
                  executionMode === mode.id
                    ? 'bg-violet-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                } disabled:opacity-50`}
              >
                {mode.label}
                <span className="text-xs opacity-70 ml-1">({mode.desc})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Model Selection */}
        <div className="mb-4">
          <label className="block text-sm text-slate-400 mb-2 flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Model ({availableModels.length} available)
          </label>
          <div className="relative">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 appearance-none cursor-pointer"
            >
              {availableModels.length === 0 && (
                <option value="">Loading models...</option>
              )}
              {availableModels.map((model) => (
                <option key={`${model.provider_id}-${model.id}`} value={model.id}>
                  {model.name} {model.is_default ? '(default)' : ''} - {model.provider}
                </option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
        
        {/* Prompt Selection with Combo Boxes */}
        <div className="mb-4 grid grid-cols-2 gap-4">
          {/* Category Selection */}
          <div>
            <label className="block text-sm text-slate-400 mb-2">Category</label>
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setSelectedPrompt('');
                }}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 appearance-none cursor-pointer"
              >
                {PROMPT_CATEGORIES.map((cat) => (
                  <option key={cat.category} value={cat.category}>
                    {cat.category}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Prompt Selection */}
          <div>
            <label className="block text-sm text-slate-400 mb-2">Prompt Type</label>
            <div className="relative">
              <select
                value={selectedPrompt}
                onChange={(e) => setSelectedPrompt(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 appearance-none cursor-pointer"
              >
                <option value="">-- Select a prompt --</option>
                {currentCategory?.prompts.map((prompt) => (
                  <option key={prompt.label} value={prompt.label}>
                    {prompt.label}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        
        {/* Mission Input */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-slate-400">Mission Details</label>
            <button
              onClick={() => {
                setMissionText('');
                setSelectedPrompt('');
              }}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Clear
            </button>
          </div>
          <textarea
            value={missionText}
            onChange={(e) => setMissionText(e.target.value)}
            placeholder="Describe what you want the agent(s) to do, or select a prompt type above..."
            className="w-full h-40 bg-slate-900 border border-slate-700 rounded p-3 text-sm text-slate-200 placeholder-slate-500 resize-none"
          />
        </div>
        
        {/* Last Result */}
        {lastResult && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Execution Complete</span>
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <p>Mode: {lastResult.mode}</p>
              {lastResult.agent_type && <p>Agent: {lastResult.agent_type}</p>}
              <p>Heuristics: {lastResult.heuristics_count} extracted</p>
              <p>Time: {(lastResult.execution_time_ms / 1000).toFixed(1)}s</p>
            </div>
            {lastResult.response_preview && (
              <div className="mt-2 p-2 bg-slate-800 rounded text-xs text-slate-300 max-h-32 overflow-y-auto">
                <strong>Response:</strong>
                <p className="mt-1">{lastResult.response_preview}...</p>
              </div>
            )}
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-sm"
          >
            Close
          </button>
          <button
            onClick={executeMission}
            disabled={!missionText.trim() || isExecuting}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {isExecuting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
        </div>
      </div>
    </div>
  );
}
