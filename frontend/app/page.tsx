'use client'

import { useUser } from '@auth0/nextjs-auth0/client'
import Link from 'next/link'

export default function Home() {
  const { user, error, isLoading } = useUser()

  if (isLoading) return <div className="flex justify-center items-center min-h-screen">Loading...</div>
  if (error) return <div className="flex justify-center items-center min-h-screen text-red-600">Error: {error.message}</div>

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-vault-blue">🔐 VaultMind</h1>
            </div>
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <span className="text-gray-700">Hello, {user.name}</span>
                  <Link
                    href="/chat"
                    className="bg-vault-blue text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                  >
                    Open Chat
                  </Link>
                  <a
                    href="/api/auth/logout"
                    className="text-gray-600 hover:text-gray-900 transition"
                  >
                    Logout
                  </a>
                </>
              ) : (
                <a
                  href="/api/auth/login"
                  className="bg-vault-blue text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                >
                  Login with Google
                </a>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-4">
            Secure AI Agent
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Demonstrating Auth0 for AI Agents with Token Vault integration
          </p>
          
          {user ? (
            <div className="bg-white rounded-lg shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Welcome back!</h3>
              <p className="text-gray-600 mb-6">
                You're authenticated and ready to interact with your secure AI agent.
                Your identity is verified through Auth0, and all API calls are secured.
              </p>
              <Link
                href="/chat"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-vault-blue hover:bg-blue-700 transition"
              >
                Start Chatting →
              </Link>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Get Started</h3>
              <p className="text-gray-600 mb-6">
                Login with your Google account to access your secure AI agent.
                We use Auth0 for authentication and never store your credentials.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="text-center">
                  <div className="bg-vault-blue rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                    <span className="text-white text-xl">🔐</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">Secure Auth</h4>
                  <p className="text-sm text-gray-600">OAuth2 with Auth0</p>
                </div>
                <div className="text-center">
                  <div className="bg-vault-green rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                    <span className="text-white text-xl">🤖</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">AI Agent</h4>
                  <p className="text-sm text-gray-600">Natural language processing</p>
                </div>
                <div className="text-center">
                  <div className="bg-vault-gray rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                    <span className="text-white text-xl">📅</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">Calendar API</h4>
                  <p className="text-sm text-gray-600">Google Calendar integration</p>
                </div>
              </div>
              <a
                href="/api/auth/login"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-vault-blue hover:bg-blue-700 transition"
              >
                Login with Google →
              </a>
            </div>
          )}
        </div>
        
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">Security Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">JWT Validation</h4>
              <p className="text-sm text-gray-600">All API requests validated against Auth0 JWKS</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Token Vault</h4>
              <p className="text-sm text-gray-600">Short-lived tokens, no stored credentials</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Audit Logging</h4>
              <p className="text-sm text-gray-600">Complete trail of agent actions</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h4 className="font-semibold text-gray-900 mb-2">Scoped Access</h4>
              <p className="text-sm text-gray-600">Minimal permissions for each operation</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}