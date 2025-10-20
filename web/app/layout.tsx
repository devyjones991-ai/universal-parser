import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Universal Parser',
  description: 'Comprehensive marketplace monitoring platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-surface-bg">
          <header className="bg-surface-card border-b border-surface-border">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-semibold text-text-primary">
                    Universal Parser
                  </h1>
                </div>
                <nav className="flex space-x-8">
                  <a href="/" className="text-text-secondary hover:text-text-primary">
                    Dashboard
                  </a>
                  <a href="/items" className="text-text-secondary hover:text-text-primary">
                    Items
                  </a>
                  <a href="/parsing" className="text-text-secondary hover:text-text-primary">
                    Parsing
                  </a>
                  <a href="/analytics" className="text-text-secondary hover:text-text-primary">
                    Analytics
                  </a>
                  <a href="/settings" className="text-text-secondary hover:text-text-primary">
                    Settings
                  </a>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
