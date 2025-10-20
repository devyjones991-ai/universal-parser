'use client'

import { useState } from 'react'

export default function SettingsPage() {
  const [theme, setTheme] = useState('dark')
  const [apiUrl, setApiUrl] = useState('https://leadharvester.duckdns.org/api/v1')
  const [notifications, setNotifications] = useState(true)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Settings</h1>
        <p className="text-text-secondary">Manage your application preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Appearance</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Theme
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="input"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="auto">Auto</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">API Configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                API Base URL
              </label>
              <input
                type="url"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="input"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-text-primary">
                  Enable Notifications
                </div>
                <div className="text-sm text-text-secondary">
                  Receive alerts for price changes and updates
                </div>
              </div>
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                className="h-4 w-4 text-brand-primary focus:ring-brand-primary border-surface-border rounded"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-text-primary mb-4">Account</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Email
              </label>
              <input
                type="email"
                value="user@example.com"
                disabled
                className="input bg-surface-bg"
              />
            </div>
            <button className="btn btn-outline">
              Change Password
            </button>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-4">
        <button className="btn btn-outline">
          Reset to Defaults
        </button>
        <button className="btn btn-primary">
          Save Settings
        </button>
      </div>
    </div>
  )
}
