'use client'

import { useEffect, useState } from 'react'
import { apiClient, Item } from '../../lib/api'

export default function ItemsPage() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await apiClient.getItems()
        setItems(response.data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch items')
      } finally {
        setLoading(false)
      }
    }

    fetchItems()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-secondary">Loading items...</div>
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
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-text-primary">Items</h1>
        <button className="btn btn-primary">
          Add New Item
        </button>
      </div>

      {items.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-text-muted">No items found</div>
          <button className="btn btn-primary mt-4">
            Parse Your First Item
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {items.map((item) => (
            <div key={item.id} className="card">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-text-primary">
                    {item.name}
                  </h3>
                  <p className="text-text-secondary text-sm mt-1">
                    {item.marketplace} • {item.price} {item.currency}
                  </p>
                  <p className="text-text-muted text-sm mt-2">
                    Added: {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button className="btn btn-outline text-sm">
                    Edit
                  </button>
                  <button className="btn btn-outline text-sm text-danger">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
