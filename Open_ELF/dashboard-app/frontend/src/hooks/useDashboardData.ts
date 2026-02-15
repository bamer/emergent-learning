import { useState, useEffect, useCallback, useMemo } from 'react'
import { Stats, Hotspot, ApiRun, RawEvent, TimelineEvent } from '../types'
import { useAPI } from './useAPI'

export function useDashboardData() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [runs, setRuns] = useState<ApiRun[]>([])
  const [events, setEvents] = useState<RawEvent[]>([])
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const api = useAPI()

  const loadData = useCallback(async () => {
    try {
      const [statsData, hotspotsData, runsData, timelineEventsData, eventsData] = await Promise.all([
        api.get('/api/v1/stats').catch(() => null),
        api.get('/api/v1/hotspots').catch(() => []),
        api.get('/api/v1/runs?limit=100').catch(() => []),
        api.get('/api/v1/timeline/events?limit=500').catch(() => []),  // Increased from 100 to 500 for better event diversity
        api.get('/api/v1/events?limit=100').catch(() => []),
      ])
      if (statsData) setStats(statsData)
      setHotspots(hotspotsData || [])
      setRuns(runsData || [])
      setTimelineEvents(timelineEventsData?.events || [])
      setEvents(eventsData || [])
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setIsLoading(false)
    }
  }, [api])

  const reload = useCallback(() => {
    setIsLoading(true)
    loadData()
  }, [loadData])

  const loadStats = useCallback(async () => {
    try {
      const data = await api.get('/api/v1/stats')
      if (data) setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }, [api])

  // Initial data load
  useEffect(() => {
    loadData()

    const interval = setInterval(() => {
      api.get('/api/v1/stats').then(data => {
        if (data) setStats(data)
      }).catch(() => { })
      api.get('/api/v1/runs?limit=100').then(data => {
        if (data) setRuns(data)
      }).catch(() => { })
      api.get('/api/v1/events?limit=100').then(data => {
        if (data) setEvents(data)
      }).catch(() => { })
      api.get('/api/v1/timeline/events?limit=200').then(data => {  // Increased from 50 to 200 for reload
        if (data) setTimelineEvents(data?.events || [])
      }).catch(() => { })
    }, 30000)

    return () => clearInterval(interval)
  }, [loadData, api])

  return useMemo(() => ({
    stats,
    hotspots,
    runs,
    events,
    timelineEvents,
    isLoading,
    reload,
    loadStats,
    setStats,
  }), [stats, hotspots, runs, events, timelineEvents, isLoading, reload, loadStats])
}
