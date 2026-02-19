import React, { useState, useEffect } from 'react'
import { Shield, CheckCircle, XCircle, RefreshCw, Filter } from 'lucide-react'

interface Invariant {
  id: number
  name: string
  description: string
  domain: string
  is_active: boolean
  last_checked: string
  violations_count: number
}

interface InvariantsPanelProps {
  className?: string
}

export default function InvariantsPanel({ className = '' }: InvariantsPanelProps) {
  const [invariants, setInvariants] = useState<Invariant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)

  useEffect(() => {
    const fetchInvariants = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/v1/invariants')
        if (!response.ok) {
          throw new Error('Failed to fetch invariants')
        }
        const data = await response.json()
        setInvariants(data.invariants || [])
      } catch (err) {
        console.error('Error fetching invariants:', err)
        setError('Failed to load invariants')
      } finally {
        setLoading(false)
      }
    }

    fetchInvariants()
  }, [])

  const domains = [...new Set(invariants.map(i => i.domain))]

  const filteredInvariants = selectedDomain
    ? invariants.filter(i => i.domain === selectedDomain)
    : invariants

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center justify-center h-64 text-red-400">
          <XCircle className="w-8 h-8 mr-2" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Shield className="w-6 h-6 text-blue-400 mr-2" />
          <h2 className="text-xl font-bold text-white">System Invariants</h2>
        </div>
        <div className="flex items-center gap-4">
          {domains.length > 0 && (
            <div className="flex items-center">
              <Filter className="w-4 h-4 text-slate-400 mr-2" />
              <select
                value={selectedDomain || ''}
                onChange={(e) => setSelectedDomain(e.target.value || null)}
                className="bg-slate-800 text-white border border-slate-600 rounded px-2 py-1 text-sm"
              >
                <option value="">All Domains</option>
                {domains.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {filteredInvariants.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No invariants found</p>
          <p className="text-sm mt-2">Invariants are rules that should always hold true in the system.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredInvariants.map((invariant) => (
            <div
              key={invariant.id}
              className={`p-4 rounded-lg border ${
                invariant.is_active
                  ? 'bg-green-900/20 border-green-700'
                  : 'bg-red-900/20 border-red-700'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center">
                    {invariant.is_active ? (
                      <CheckCircle className="w-5 h-5 text-green-400 mr-2" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400 mr-2" />
                    )}
                    <h3 className="font-semibold text-white">{invariant.name}</h3>
                  </div>
                  <p className="text-sm text-slate-400 mt-1">{invariant.description}</p>
                  <div className="flex items-center mt-2 text-xs text-slate-500">
                    <span className="px-2 py-0.5 bg-slate-700 rounded mr-2">
                      {invariant.domain}
                    </span>
                    {invariant.violations_count > 0 && (
                      <span className="text-red-400">
                        {invariant.violations_count} violations
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}