import { useState, useCallback } from 'react'
import { Search, Loader2, FileCode, Brain, Zap, ExternalLink } from 'lucide-react'

interface SearchResult {
  id: number
  source_id: string
  source_type: string
  similarity: number
  text: string
  metadata?: {
    path?: string
    size?: number
    indexed_at?: string
  }
  created_at?: string
}

interface SearchResponse {
  query: string
  results: SearchResult[]
  total_matches: number
  returned: number
  error?: string
}

export function SemanticSearchPanel() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(10)
  const [sourceType, setSourceType] = useState<string>('')
  const [minSimilarity, setMinSimilarity] = useState(0.3)
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastQuery, setLastQuery] = useState<string>('')
  const [totalMatches, setTotalMatches] = useState(0)

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const payload: { query: string; top_k: number; source_type?: string; min_similarity: number } = {
        query: query.trim(),
        top_k: topK,
        min_similarity: minSimilarity,
      }
      if (sourceType) {
        payload.source_type = sourceType
      }

      const response = await fetch('/api/v1/semantic/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data: SearchResponse = await response.json()

      if (data.error) {
        setError(data.error)
        setResults([])
      } else {
        setResults(data.results || [])
        setTotalMatches(data.total_matches || data.results?.length || 0)
        setLastQuery(query)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }, [query, topK, sourceType])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const getSourceTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      python: 'text-yellow-400 bg-yellow-500/10',
      typescript: 'text-blue-400 bg-blue-500/10',
      javascript: 'text-yellow-300 bg-yellow-400/10',
      markdown: 'text-purple-400 bg-purple-500/10',
      bash: 'text-green-400 bg-green-500/10',
      shell: 'text-green-400 bg-green-500/10',
      json: 'text-orange-400 bg-orange-500/10',
      yaml: 'text-pink-400 bg-pink-500/10',
    }
    return colors[type] || 'text-slate-400 bg-slate-500/10'
  }

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.7) return 'text-emerald-400'
    if (similarity >= 0.5) return 'text-yellow-400'
    if (similarity >= 0.3) return 'text-orange-400'
    return 'text-slate-400'
  }

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-cyan-500/10">
            <Brain className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Semantic Search</h2>
            <p className="text-sm text-slate-400">Search across indexed files using AI embeddings</p>
          </div>
        </div>

        {/* Search Input */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search for code, concepts, or patterns..."
              className="w-full pl-12 pr-4 py-3 bg-slate-900/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400">Results:</label>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400">Type:</label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
              >
                <option value="">All</option>
                <option value="python">Python</option>
                <option value="typescript">TypeScript</option>
                <option value="javascript">JavaScript</option>
                <option value="markdown">Markdown</option>
                <option value="bash">Bash</option>
                <option value="json">JSON</option>
                <option value="yaml">YAML</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400">Min similarity:</label>
              <input
                type="range"
                min="0"
                max="0.8"
                step="0.05"
                value={minSimilarity}
                onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                className="w-20 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
              <span className="text-sm text-cyan-400 font-mono w-12">{(minSimilarity * 100).toFixed(0)}%</span>
            </div>

            <button
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
              className="ml-auto flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              Search
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-300">
              {totalMatches} results for "{lastQuery}"
            </h3>
          </div>

          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-lg p-4 hover:border-cyan-500/30 transition-colors"
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <FileCode className="w-4 h-4 text-slate-400" />
                    <span className="text-sm font-medium text-white">
                      {result.source_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSourceTypeColor(result.source_type)}`}>
                      {result.source_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-mono ${getSimilarityColor(result.similarity)}`}>
                      {(result.similarity * 100).toFixed(1)}% match
                    </span>
                    {result.metadata?.path && (
                      <button
                        onClick={() => {
                          // Could integrate with VS Code or file opener
                          console.log('Open file:', result.metadata?.path)
                        }}
                        className="text-slate-400 hover:text-cyan-400 transition-colors"
                        title="Open in editor"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Content Preview */}
                <pre className="text-sm text-slate-300 bg-slate-900/50 rounded-lg p-3 overflow-x-auto max-h-48 overflow-y-auto">
                  <code>{result.text.slice(0, 500)}{result.text.length > 500 ? '...' : ''}</code>
                </pre>

                {/* Metadata */}
                {result.metadata && (
                  <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                    {result.metadata.size && (
                      <span>{Math.round(result.metadata.size / 1024)} KB</span>
                    )}
                    {result.metadata.indexed_at && (
                      <span>Indexed: {new Date(result.metadata.indexed_at).toLocaleDateString()}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && results.length === 0 && lastQuery && !error && (
        <div className="text-center py-12 text-slate-400">
          <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No results found for "{lastQuery}"</p>
          <p className="text-sm mt-2">Try different keywords or check if the semantic daemon is running</p>
        </div>
      )}

      {/* Initial State */}
      {!lastQuery && results.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Enter a search query to find relevant code and documentation</p>
          <p className="text-sm mt-2">Uses AI embeddings for semantic similarity matching</p>
        </div>
      )}
    </div>
  )
}
