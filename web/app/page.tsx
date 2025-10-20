'use client'

import { useEffect, useState } from 'react'
import { apiClient, HealthResponse } from '../lib/api'

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiClient.getHealth()
        setHealth(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch health status')
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-danger">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Dashboard</h1>
        <p className="text-text-secondary">Welcome to Universal Parser</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-2">API Status</h3>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              health?.status === 'healthy' ? 'bg-success' : 'bg-danger'
            }`} />
            <span className="text-text-secondary">
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-2">Version</h3>
          <p className="text-text-secondary">{health?.version || 'N/A'}</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-2">Last Update</h3>
          <p className="text-text-secondary">
            {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'N/A'}
          </p>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-2">Total Items</h3>
          <p className="text-text-secondary">0</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="btn btn-primary w-full">
              Parse New Item
            </button>
            <button className="btn btn-outline w-full">
              View Analytics
            </button>
            <button className="btn btn-outline w-full">
              Export Data
            </button>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Recent Activity</h3>
          <div className="text-text-muted">
            No recent activity
          </div>
        </div>
      </div>
    </div>
  )
}
