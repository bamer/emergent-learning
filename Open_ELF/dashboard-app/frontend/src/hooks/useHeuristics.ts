import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import { Heuristic } from '../types'
import { useAPI } from './useAPI'
import { useNotificationContext } from '../context/NotificationContext'

interface UseHeuristicsOptions {
  onStatsChange?: () => void
  scope?: 'global' | 'project'
}

export function useHeuristics(options?: UseHeuristicsOptions) {
  const [heuristics, setHeuristics] = useState<Heuristic[]>([])
  const api = useAPI()
  const { onStatsChange, scope = 'global' } = options || {}
  const { addNotification } = useNotificationContext()
  const scopeRef = useRef(scope)
  scopeRef.current = scope

  const reloadHeuristics = useCallback(async () => {
    try {
      const data = await api.get(`/api/v1/heuristics?scope=${scopeRef.current}`)
      setHeuristics(data || [])
    } catch (err) {
      console.error('Failed to load heuristics:', err)
    }
  }, [api])

  const promoteHeuristic = useCallback(async (id: number) => {
    try {
      await api.post(`/api/v1/heuristics/${id}/promote`)
      setHeuristics(prev => prev.map(h =>
        h.id === id ? { ...h, is_golden: true } : h
      ))
      if (onStatsChange) onStatsChange()
    } catch (err) {
      console.error('Failed to promote heuristic:', err)
      throw err
    }
  }, [api, onStatsChange])

  const demoteHeuristic = useCallback(async (id: number) => {
    try {
      await api.post(`/api/v1/heuristics/${id}/demote`)
      setHeuristics(prev => prev.map(h =>
        h.id === id ? { ...h, is_golden: false } : h
      ))
      if (onStatsChange) onStatsChange()
    } catch (err) {
      console.error('Failed to demote heuristic:', err)
      throw err
    }
  }, [api, onStatsChange])

  const promoteToSuperGolden = useCallback(async (id: number) => {
    try {
      await api.post(`/api/v1/golden-rules/${id}/promote-to-super`)
      // The heuristic stays golden but now it's also a super golden rule
      addNotification('Super Golden Rule', 'Promoted to Super Golden Rule!', { type: 'success' })
      if (onStatsChange) onStatsChange()
    } catch (err) {
      console.error('Failed to promote to super golden:', err)
      throw err
    }
  }, [api, onStatsChange, addNotification])

  const deleteHeuristic = useCallback(async (id: number) => {
    try {
      await api.del(`/api/v1/heuristics/${id}`)
      setHeuristics(prev => prev.filter(h => h.id !== id))
      if (onStatsChange) onStatsChange()
    } catch (err) {
      console.error('Failed to delete heuristic:', err)
      throw err
    }
  }, [api, onStatsChange])

  const updateHeuristic = useCallback(async (
    id: number,
    updates: { rule?: string; explanation?: string; domain?: string }
  ) => {
    try {
      await api.put(`/api/v1/heuristics/${id}`, updates)
      setHeuristics(prev => prev.map(h =>
        h.id === id ? { ...h, ...updates } : h
      ))
    } catch (err) {
      console.error('Failed to update heuristic:', err)
      throw err
    }
  }, [api])

  // Reload when scope changes
  useEffect(() => {
    reloadHeuristics()
  }, [reloadHeuristics, scope])

  return useMemo(() => ({
    heuristics,
    setHeuristics,
    promoteHeuristic,
    promoteToSuperGolden,
    demoteHeuristic,
    deleteHeuristic,
    updateHeuristic,
    reloadHeuristics,
  }), [heuristics, promoteHeuristic, promoteToSuperGolden, demoteHeuristic, deleteHeuristic, updateHeuristic, reloadHeuristics])
}
