/**
 * WaitlistForm component
 * Allows users to sign up for the waitlist for VaultMind.
 *
 * @author Felix
 * @created 2025-10-25
 */
'use client'

import { useState } from 'react'

export default function WaitlistForm() {
  const [email, setEmail] = useState('')
  const [useCase, setUseCase] = useState('')
  const [status, setStatus] = useState<
    'idle' | 'loading' | 'success' | 'error'
  >('idle')
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setMessage('')

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          useCase,
          timestamp: new Date().toISOString(),
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage("🎉 Thank you! We'll notify you when VaultMind launches.")
        setEmail('')
        setUseCase('')
      } else {
        setStatus('error')
        // Show specific error message from server
        if (response.status === 409) {
          setMessage(
            '📧 This email is already on the waitlist! Check your inbox for our previous confirmation.'
          )
        } else if (data.error) {
          setMessage(data.error)
        } else {
          setMessage('Something went wrong. Please try again.')
        }
      }
    } catch (error) {
      setStatus('error')
      setMessage('Network error. Please check your connection and try again.')
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200 max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <span className="text-4xl mb-3 block">🚀</span>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Join the Waitlist
        </h3>
        <p className="text-gray-600">
          Be the first to know when VaultMind launches. Get exclusive early
          access and explore new features before anyone else!
        </p>
      </div>

      {status === 'success' ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <span className="text-5xl mb-3 block">✅</span>
          <p className="text-green-800 font-semibold text-lg">{message}</p>
          <p className="text-green-700 text-sm mt-2">
            Check your inbox for confirmation (and check spam folder just in
            case!)
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            />
          </div>

          <div>
            <label
              htmlFor="useCase"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              What would you use VaultMind for? (Optional)
            </label>
            <textarea
              id="useCase"
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              placeholder="e.g., Managing team calendars, scheduling customer meetings, personal productivity..."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
            />
          </div>

          {status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <span className="text-red-500 text-xl">⚠️</span>
                <p className="text-red-800 text-sm flex-1">{message}</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={status === 'loading'}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status === 'loading' ? '⏳ Joining...' : '🚀 Join Waitlist'}
          </button>

          <p className="text-xs text-gray-500 text-center">
            We respect your privacy. Unsubscribe anytime. No spam, ever.
          </p>
        </form>
      )}

      {/* Social Proof */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-center space-x-8 text-sm text-gray-600">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">0</div>
            <div className="text-xs">Early Adopters</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">🔐</div>
            <div className="text-xs">Auth0 Secured</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">✅</div>
            <div className="text-xs">Real API</div>
          </div>
        </div>
      </div>
    </div>
  )
}
