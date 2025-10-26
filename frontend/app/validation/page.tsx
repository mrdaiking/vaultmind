'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@auth0/nextjs-auth0/client'
import { useRouter } from 'next/navigation'

interface WaitlistEntry {
  email: string
  useCase: string
  timestamp: string
  ip?: string
  userAgent?: string
}

interface WaitlistStats {
  total: number
  entries: WaitlistEntry[]
  stats: {
    withUseCase: number
    recent24h: number
  }
}

// Admin emails who can access validation dashboard
// Load from environment variable (comma-separated list)
const ADMIN_EMAILS = process.env.NEXT_PUBLIC_ADMIN_EMAILS?.split(',').map(e => e.trim()) || []

export default function ValidationDashboard() {
  const { user, isLoading } = useUser()
  const router = useRouter()
  const [data, setData] = useState<WaitlistStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Check if user is admin
  const isAdmin = user && ADMIN_EMAILS.includes(user.email || '')

  useEffect(() => {
    // Redirect if not logged in or not admin
    if (!isLoading && !user) {
      router.push('/api/auth/login?returnTo=/validation')
      return
    }
    
    if (!isLoading && user && !isAdmin) {
      router.push('/')
      return
    }

    if (isAdmin) {
      fetchWaitlist()
    }
  }, [user, isLoading, isAdmin, router])

  const fetchWaitlist = async () => {
    try {
      const response = await fetch('/api/waitlist')
      if (!response.ok) throw new Error('Failed to fetch')
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError('Failed to load waitlist data')
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    )
  }

  // If not admin, show nothing (redirect happens in useEffect)
  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md text-center">
          <span className="text-6xl mb-4 block">🔒</span>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            Only administrators can access the validation dashboard.
          </p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
          >
            Return Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow-lg mb-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-vault-blue">🔐 VaultMind - Validation Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/')}
                className="text-gray-600 hover:text-gray-900 transition"
              >
                ← Back to Home
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">SaaS Validation Metrics</h2>
          <p className="text-gray-600">
            Track interest in VaultMind to validate product-market fit
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {data && (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-xl shadow-lg p-6 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Signups</p>
                    <p className="text-4xl font-bold text-blue-600">{data.total}</p>
                  </div>
                  <div className="text-4xl">👥</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Last 24 Hours</p>
                    <p className="text-4xl font-bold text-green-600">{data.stats.recent24h}</p>
                  </div>
                  <div className="text-4xl">📈</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border border-purple-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">With Use Case</p>
                    <p className="text-4xl font-bold text-purple-600">{data.stats.withUseCase}</p>
                  </div>
                  <div className="text-4xl">💬</div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border border-yellow-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Engagement Rate</p>
                    <p className="text-4xl font-bold text-yellow-600">
                      {data.total > 0 ? Math.round((data.stats.withUseCase / data.total) * 100) : 0}%
                    </p>
                  </div>
                  <div className="text-4xl">⚡</div>
                </div>
              </div>
            </div>

            {/* Validation Insights */}
            <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200 mb-8">
              <h3 className="text-xl font-bold text-gray-900 mb-4">📊 Validation Insights</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">
                    {data.total >= 100 ? '✅' : data.total >= 50 ? '🟡' : '🔴'}
                  </span>
                  <div>
                    <p className="font-semibold text-gray-900">
                      Market Interest: {data.total >= 100 ? 'Strong' : data.total >= 50 ? 'Moderate' : 'Early Stage'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {data.total >= 100 
                        ? 'You have strong validation for a SaaS launch! Consider building an MVP.' 
                        : data.total >= 50
                        ? 'Good traction. Keep marketing to reach 100+ signups before launch.'
                        : 'Keep promoting. Aim for 100+ signups to validate demand.'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-2xl">
                    {data.stats.withUseCase / data.total >= 0.5 ? '✅' : '🟡'}
                  </span>
                  <div>
                    <p className="font-semibold text-gray-900">
                      User Engagement: {data.stats.withUseCase / data.total >= 0.5 ? 'High' : 'Moderate'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {data.stats.withUseCase / data.total >= 0.5
                        ? 'Users are highly engaged and sharing use cases - great signal!'
                        : 'Encourage more users to share their use cases for better product insights.'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Waitlist Entries */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-bold text-gray-900">📝 Waitlist Entries</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Use Case
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.entries.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                          No signups yet. Share your landing page to start collecting emails!
                        </td>
                      </tr>
                    ) : (
                      data.entries.map((entry, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {entry.email}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">
                            {entry.useCase || <span className="text-gray-400 italic">No use case provided</span>}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(entry.timestamp).toLocaleString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Export Options */}
            <div className="mt-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
              <h3 className="text-xl font-bold mb-3">📤 Export & Next Steps</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="font-semibold mb-2">Export to CSV</p>
                  <p className="text-sm text-blue-100 mb-3">
                    Download email list for Mailchimp/SendGrid
                  </p>
                  <button 
                    onClick={() => {
                      const csv = [
                        ['Email', 'Use Case', 'Timestamp'].join(','),
                        ...data.entries.map(e => 
                          [e.email, `"${e.useCase}"`, e.timestamp].join(',')
                        )
                      ].join('\n')
                      const blob = new Blob([csv], { type: 'text/csv' })
                      const url = window.URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = 'vaultmind-waitlist.csv'
                      a.click()
                    }}
                    className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition text-sm"
                  >
                    Download CSV
                  </button>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <p className="font-semibold mb-2">Email Campaign</p>
                  <p className="text-sm text-blue-100 mb-3">
                    Send updates when you launch VaultMind SaaS
                  </p>
                  <button 
                    className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition text-sm"
                    onClick={() => alert('Integrate with SendGrid/Resend/Mailchimp for automated emails')}
                  >
                    Setup Email Integration
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
