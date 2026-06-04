import { useQuery } from '@tanstack/react-query'
import { Activity, Users, Clock, AlertTriangle, TrendingUp, Building2 } from 'lucide-react'
import { fetchStoreAnalytics, fetchZoneAnalytics, fetchQueueAnalytics, fetchAnomalies, fetchRecentEvents } from '../services/api'
import { useState } from 'react'

export default function Dashboard() {
  const [selectedStore, setSelectedStore] = useState('store_1')
  
  const { data: summary, isLoading } = useQuery({
    queryKey: ['storeSummary', selectedStore],
    queryFn: () => fetchStoreAnalytics(selectedStore),
    refetchInterval: 10000, // 10s
  })

  // Debug logging
  console.log('Dashboard - Selected Store:', selectedStore)
  console.log('Dashboard - Summary Data:', summary)
  console.log('Dashboard - Is Loading:', isLoading)

  const { data: zones } = useQuery({
    queryKey: ['zones', selectedStore],
    queryFn: () => fetchZoneAnalytics(selectedStore),
    refetchInterval: 10000,
  })

  const { data: queue } = useQuery({
    queryKey: ['queue', selectedStore],
    queryFn: () => fetchQueueAnalytics(selectedStore),
    refetchInterval: 10000,
  })

  const { data: anomalies } = useQuery({
    queryKey: ['anomalies'],
    queryFn: fetchAnomalies,
    refetchInterval: 15000,
  })

  const { data: recentEvents } = useQuery({
    queryKey: ['recentEvents', selectedStore],
    queryFn: () => fetchRecentEvents(20, selectedStore),
    refetchInterval: 5000, // 5s for live feel
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-xl text-gray-700">Loading analytics...</div>
      </div>
    )
  }

  const demographics = summary?.demographics || {}
  const queueData = summary?.queue || {}

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Store Intelligence MVP</h1>
            <p className="text-gray-600 mt-2">Real-time retail analytics • Computer Vision Powered</p>
            <p className="text-sm text-gray-500 mt-1">Auto-refresh: 10s • Hackathon Demo</p>
          </div>
          <div className="flex items-center gap-3">
            <Building2 className="w-6 h-6 text-gray-600" />
            <select
              value={selectedStore}
              onChange={(e) => setSelectedStore(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-lg font-medium bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="store_1">Store 1</option>
              <option value="store_2">Store 2</option>
            </select>
          </div>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Footfall"
          value={summary?.footfall || 0}
          icon={<Users className="w-6 h-6" />}
          color="blue"
          subtitle="Last 24h"
        />
        <MetricCard
          title="Unique Visitors"
          value={summary?.unique_visitors || 0}
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
          subtitle="Distinct tracks"
        />
        <MetricCard
          title="Queue Abandonments"
          value={queueData.abandonments || 0}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          subtitle={`${((queueData.abandonment_rate || 0) * 100).toFixed(0)}% rate`}
        />
        <MetricCard
          title="Avg Wait Time"
          value={`${Math.round(queueData.avg_wait_seconds || 0)}s`}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
          subtitle="Queue performance"
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Demographics */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Demographics
          </h2>
          <div className="space-y-3">
            {demographics.M > 0 && (
              <DemoBar label="Male" value={demographics.M} total={summary?.footfall || 1} color="blue" />
            )}
            {demographics.F > 0 && (
              <DemoBar label="Female" value={demographics.F} total={summary?.footfall || 1} color="pink" />
            )}
            {(summary?.footfall - (demographics.M || 0) - (demographics.F || 0)) > 0 && (
              <DemoBar 
                label="Unknown" 
                value={summary?.footfall - (demographics.M || 0) - (demographics.F || 0)} 
                total={summary?.footfall || 1} 
                color="gray" 
              />
            )}
          </div>
        </div>

        {/* Queue Metrics */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-yellow-600" />
            Queue Performance
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 font-medium">Total Events</span>
              <span className="text-2xl font-bold text-gray-900">{queue?.total_events || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 font-medium">Completed</span>
              <span className="text-lg font-semibold text-green-600">{queue?.completed || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 font-medium">Abandoned</span>
              <span className="text-lg font-semibold text-red-600">{queue?.abandoned || 0}</span>
            </div>
            <div className="pt-3 border-t">
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">Avg Wait</span>
                <span className="text-lg font-semibold">{Math.round(queue?.avg_wait_seconds || 0)}s</span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-700 font-medium">Max Wait</span>
                <span className="text-lg font-semibold">{Math.round(queue?.max_wait_seconds || 0)}s</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Zone Metrics */}
      {zones && zones.zones && zones.zones.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Zone Engagement</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Zone</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Visits</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Unique Visitors</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Type</th>
                </tr>
              </thead>
              <tbody>
                {zones.zones.map((zone: any, idx: number) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{zone.zone_name || zone.zone_id}</td>
                    <td className="text-right py-3 px-4">{zone.visits}</td>
                    <td className="text-right py-3 px-4">{zone.unique_visitors}</td>
                    <td className="text-right py-3 px-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                        {zone.zone_type}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Anomalies */}
      {anomalies && anomalies.count > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Anomaly Alerts ({anomalies.count})
          </h2>
          <div className="space-y-3">
            {anomalies.anomalies.map((anomaly: any, idx: number) => (
              <div key={idx} className="border-l-4 border-red-500 pl-4 py-2 bg-red-50">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{anomaly.description}</p>
                    <p className="text-sm text-gray-600 mt-1">Type: {anomaly.type} • Store: {anomaly.store_id}</p>
                  </div>
                  <span className={`px-3 py-1 text-xs rounded-full font-semibold ${
                    anomaly.severity === 'high' ? 'bg-red-600 text-white' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {anomaly.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Events */}
      {recentEvents && recentEvents.count > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Events (Live)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Time</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Type</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Camera</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Zone</th>
                  <th className="text-left py-2 px-3 font-semibold text-gray-700">Details</th>
                </tr>
              </thead>
              <tbody>
                {recentEvents.events.slice(0, 10).map((event: any) => (
                  <tr key={event.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 text-gray-600">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getEventTypeColor(event.event_type)}`}>
                        {event.event_type}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-600">{event.camera_id}</td>
                    <td className="py-2 px-3 text-gray-600">{event.zone_name || '-'}</td>
                    <td className="py-2 px-3 text-gray-600">
                      {event.gender && `${event.gender}, `}
                      {event.age && `${event.age}yo`}
                      {event.wait_seconds && ` • Wait: ${Math.round(event.wait_seconds)}s`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-8 text-center text-sm text-gray-500">
        Store Intelligence MVP • Hackathon Demo • Last updated: {new Date().toLocaleTimeString()}
      </footer>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  color: 'blue' | 'green' | 'red' | 'yellow'
  subtitle?: string
}

function MetricCard({ title, value, icon, color, subtitle }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          {icon}
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
      <p className="text-gray-600 font-medium">{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}

interface DemoBarProps {
  label: string
  value: number
  total: number
  color: 'blue' | 'pink' | 'gray'
}

function DemoBar({ label, value, total, color }: DemoBarProps) {
  const percentage = (value / total) * 100
  const colorClasses = {
    blue: 'bg-blue-500',
    pink: 'bg-pink-500',
    gray: 'bg-gray-500',
  }

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm text-gray-600">{value} ({percentage.toFixed(0)}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div className={`h-2.5 rounded-full ${colorClasses[color]}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  )
}

function getEventTypeColor(type: string) {
  const colors: Record<string, string> = {
    entry: 'bg-green-100 text-green-800',
    exit: 'bg-blue-100 text-blue-800',
    zone_entered: 'bg-purple-100 text-purple-800',
    zone_exited: 'bg-indigo-100 text-indigo-800',
    queue_completed: 'bg-green-100 text-green-800',
    queue_abandoned: 'bg-red-100 text-red-800',
  }
  return colors[type] || 'bg-gray-100 text-gray-800'
}
