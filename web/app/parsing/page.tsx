'use client'

import { useState } from 'react'
import { apiClient, ParsingRequest } from '../../lib/api'

export default function ParsingPage() {
  const [url, setUrl] = useState('')
  const [marketplace, setMarketplace] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url || !marketplace) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const request: ParsingRequest = {
        url,
        marketplace,
      }
      
      const response = await apiClient.parseItem(request)
      setResult(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse item')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Parse Item</h1>
        <p className="text-text-secondary">Extract product data from marketplace URLs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Parse Settings</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Product URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="input"
                placeholder="https://example.com/product/123"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Marketplace
              </label>
              <select
                value={marketplace}
                onChange={(e) => setMarketplace(e.target.value)}
                className="input"
                required
              >
                <option value="">Select marketplace</option>
                <option value="wildberries">Wildberries</option>
                <option value="ozon">Ozon</option>
                <option value="yandex_market">Yandex Market</option>
                <option value="avito">Avito</option>
                <option value="amazon">Amazon</option>
                <option value="aliexpress">AliExpress</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !url || !marketplace}
              className="btn btn-primary w-full"
            >
              {loading ? 'Parsing...' : 'Parse Item'}
            </button>
          </form>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Result</h3>
          {loading && (
            <div className="text-text-secondary">Parsing in progress...</div>
          )}
          
          {error && (
            <div className="text-danger">
              Error: {error}
            </div>
          )}
          
          {result && (
            <div className="space-y-3">
              {result.success ? (
                <div>
                  <div className="text-success text-sm font-medium mb-2">
                    ✓ Parsing successful
                  </div>
                  <div className="bg-surface-bg p-3 rounded border">
                    <pre className="text-sm text-text-primary whitespace-pre-wrap">
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-danger">
                  Parsing failed: {result.error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
