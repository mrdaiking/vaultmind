'use client'

import { useUser } from '@auth0/nextjs-auth0/client'
import Link from 'next/link'
import WaitlistForm from '@/components/WaitlistForm'

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
                    href="/validation"
                    className="text-gray-600 hover:text-gray-900 transition"
                  >
                    📊 Dashboard
                  </Link>
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
                <>
                  <Link
                    href="/validation"
                    className="text-gray-600 hover:text-gray-900 transition text-sm"
                  >
                    📊 Stats
                  </Link>
                  <a
                    href="/api/auth/login"
                    className="bg-vault-blue text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                  >
                    Login with Google
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center py-16">
          <h2 className="text-5xl font-extrabold text-gray-900 sm:text-6xl mb-6">
            Your AI Calendar Assistant<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              Powered by Auth0 for AI
            </span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Experience the future of secure AI agents. VaultMind uses <strong>real API integrations</strong> 
            (not mock data) to manage your Google Calendar with natural language. 
            Built with Auth0 for AI Agents, demonstrating true enterprise-grade security.
          </p>
          
          {user ? (
            <div className="flex justify-center space-x-4">
              <Link
                href="/chat"
                className="inline-flex items-center px-8 py-4 text-lg font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition shadow-lg"
              >
                🚀 Start Chatting →
              </Link>
              <a
                href="https://calendar.google.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-8 py-4 text-lg font-medium rounded-lg text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition"
              >
                📅 View Calendar
              </a>
            </div>
          ) : (
            <div>
              <a
                href="/api/auth/login"
                className="inline-flex items-center px-8 py-4 text-lg font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition shadow-lg mb-4"
              >
                🔐 Login with Google →
              </a>
            </div>
          )}
        </div>

        {/* Demo Video / Screenshot Section */}
        <div className="mb-20">
          <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-200">
            <div className="aspect-video bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg overflow-hidden">
              <iframe
                width="100%"
                height="100%"
                src="https://www.youtube.com/embed/Pv8nke_2LM4"
                title="VaultMind Demo - Secure AI Calendar Assistant"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="rounded-lg"
              ></iframe>
            </div>
          </div>
        </div>

        {/* Waitlist Form - NEW */}
        <div className="mb-20">
          <WaitlistForm />
        </div>

        {/* Key Features */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-4">
            Key Features
          </h3>
          <p className="text-center text-gray-600 mb-12 max-w-2xl mx-auto">
            Real AI agents with actual API integrations powered by Auth0 for AI
          </p>
          
          {/* Feature Showcase Table */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-gray-200">
              <h4 className="text-lg font-bold text-gray-900 text-center">
                ✨ What Makes VaultMind Special
              </h4>
            </div>
            <div className="divide-y divide-gray-200">
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">✅</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Real API Integration</h5>
                    <p className="text-sm text-gray-600">Google Calendar API - Every event you create actually appears in your calendar</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">🤖</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">True AI Agents</h5>
                    <p className="text-sm text-gray-600">OpenAI GPT-4o-mini for natural language understanding - Not template responses</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">💬</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Natural Language Parsing</h5>
                    <p className="text-sm text-gray-600">Say "tomorrow afternoon" and it understands - Intelligent time interpretation</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">⚠️</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Smart Conflict Detection</h5>
                    <p className="text-sm text-gray-600">Warns you about scheduling conflicts before creating events</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">🌍</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Global Timezone Support</h5>
                    <p className="text-sm text-gray-600">19 timezones with live clock - Perfect for international teams</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">🔍</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Verifiable Results</h5>
                    <p className="text-sm text-gray-600">Check Google Calendar to see events actually created - Proof of real integration</p>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 hover:bg-gray-50 transition">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">🔐</span>
                  <div className="flex-1">
                    <h5 className="font-semibold text-gray-900">Enterprise Security</h5>
                    <p className="text-sm text-gray-600">Auth0 Management API with short-lived tokens - No stored credentials ever</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-8 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <span className="text-3xl">🔍</span>
              <div>
                <h4 className="font-bold text-green-900 mb-2">Verify It's Real!</h4>
                <p className="text-sm text-green-800">
                  After creating an event with VaultMind, open <a href="https://calendar.google.com" target="_blank" rel="noopener noreferrer" className="underline font-semibold">Google Calendar</a> 
                  {' '}and see it actually appear in your calendar. That's the difference between real AI agents and mock demos.
                </p>
              </div>
            </div>
          </div>
        </div>



        {/* Use Cases Section */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-4">
            Real-World Use Cases
          </h3>
          <p className="text-center text-gray-600 mb-12 max-w-2xl mx-auto">
            See how VaultMind helps professionals manage their time with AI-powered scheduling
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {/* Use Case 1: Busy Professional */}
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200 hover:shadow-xl transition">
              <div className="text-4xl mb-4">💼</div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Busy Professionals</h4>
              <p className="text-gray-600 mb-4">
                "Schedule my 1-on-1s for next week" — VaultMind finds available slots, 
                checks for conflicts, and creates all meetings instantly.
              </p>
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>Saves 2+ hours</strong> of manual scheduling per week
                </p>
              </div>
            </div>

            {/* Use Case 2: Remote Teams */}
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200 hover:shadow-xl transition">
              <div className="text-4xl mb-4">🌍</div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Remote Teams</h4>
              <p className="text-gray-600 mb-4">
                "Am I free Friday 3pm Tokyo time?" — Automatic timezone conversion 
                across 19 global timezones for distributed teams.
              </p>
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-sm text-green-800">
                  <strong>No more timezone math</strong> or scheduling mistakes
                </p>
              </div>
            </div>

            {/* Use Case 3: Sales & Client Meetings */}
            <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200 hover:shadow-xl transition">
              <div className="text-4xl mb-4">🤝</div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Sales & Client Meetings</h4>
              <p className="text-gray-600 mb-4">
                "Find me 30 minutes this week for a client demo" — Smart availability 
                detection with conflict warnings.
              </p>
              <div className="bg-purple-50 rounded-lg p-3">
                <p className="text-sm text-purple-800">
                  <strong>Never double-book</strong> important meetings again
                </p>
              </div>
            </div>
          </div>

          {/* Coming Soon Banner */}
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-xl p-8 text-center">
            <div className="inline-block bg-yellow-400 text-yellow-900 text-sm font-bold px-4 py-2 rounded-full mb-4">
              🚀 COMING SOON
            </div>
            <h4 className="text-2xl font-bold text-gray-900 mb-4">
              We're Building More Features Based on Your Feedback!
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow">
                <p className="text-3xl mb-2">📧</p>
                <p className="font-semibold text-gray-900">Email Integration</p>
                <p className="text-sm text-gray-600">Schedule from Gmail threads</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <p className="text-3xl mb-2">🔔</p>
                <p className="font-semibold text-gray-900">Smart Reminders</p>
                <p className="text-sm text-gray-600">AI-powered prep suggestions</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <p className="text-3xl mb-2">📊</p>
                <p className="font-semibold text-gray-900">Time Analytics</p>
                <p className="text-sm text-gray-600">Meeting insights & reports</p>
              </div>
            </div>
            <p className="text-gray-700 font-medium">
              Join our waitlist to get early access and help shape VaultMind's future! 👇
            </p>
          </div>
        </div>

        {/* Feedback Section */}
        <div className="mb-20">
          <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-10 text-white shadow-2xl">
            <div className="text-center mb-8">
              <h3 className="text-3xl font-bold mb-3">💬 Help Us Build VaultMind Together</h3>
              <p className="text-blue-100 text-lg max-w-2xl mx-auto">
                We're actively developing new features based on real user feedback. 
                Your input directly shapes our roadmap!
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              <div className="bg-white/10 backdrop-blur rounded-xl p-6 border border-white/20">
                <div className="flex items-center mb-3">
                  <span className="text-3xl mr-3">✨</span>
                  <h4 className="font-bold text-xl">Feature Requests</h4>
                </div>
                <p className="text-blue-100 mb-4">
                  What calendar features would make your life easier? Share your ideas!
                </p>
                <a 
                  href={`mailto:${process.env.NEXT_PUBLIC_FEEDBACK_EMAIL}?subject=VaultMind Feature Request&body=Hi VaultMind Team,%0D%0A%0D%0AI'd like to suggest the following feature:%0D%0A%0D%0A[Describe your feature idea here]%0D%0A%0D%0AWhy this would be useful:%0D%0A[Explain the use case]%0D%0A%0D%0AThanks!`}
                  className="inline-block bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-blue-50 transition"
                >
                  Submit Feedback →
                </a>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-xl p-6 border border-white/20">
                <div className="flex items-center mb-3">
                  <span className="text-3xl mr-3">🐛</span>
                  <h4 className="font-bold text-xl">Bug Reports</h4>
                </div>
                <p className="text-blue-100 mb-4">
                  Found an issue? Help us improve by reporting bugs you encounter.
                </p>
                <a 
                  href={`mailto:${process.env.NEXT_PUBLIC_FEEDBACK_EMAIL}?subject=VaultMind Bug Report&body=Hi VaultMind Team,%0D%0A%0D%0AI found a bug:%0D%0A%0D%0AWhat happened:%0D%0A[Describe what went wrong]%0D%0A%0D%0ASteps to reproduce:%0D%0A1. [First step]%0D%0A2. [Second step]%0D%0A3. [What happened]%0D%0A%0D%0AExpected behavior:%0D%0A[What should have happened]%0D%0A%0D%0ABrowser/Device:%0D%0A[e.g., Chrome on Mac, Safari on iPhone]%0D%0A%0D%0AThanks!`}
                  className="inline-block bg-white text-blue-600 px-6 py-2 rounded-lg font-semibold hover:bg-blue-50 transition"
                >
                  Report Issue →
                </a>
              </div>
            </div>

            <div className="text-center mt-8 pt-8 border-t border-white/20">
              <p className="text-blue-100 mb-4">
                <strong>Early adopters get:</strong> Priority support, beta access to new features, and direct line to our team
              </p>
              <div className="flex justify-center gap-4">
                <span className="bg-white/20 px-4 py-2 rounded-full text-sm">🎯 Shape the Product</span>
                <span className="bg-white/20 px-4 py-2 rounded-full text-sm">🚀 Early Access</span>
                <span className="bg-white/20 px-4 py-2 rounded-full text-sm">💎 Lifetime Benefits</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security Features - Redesigned */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-4">
            Enterprise-Grade Security
          </h3>
          <p className="text-center text-gray-600 mb-12 max-w-2xl mx-auto">
            VaultMind implements Auth0 best practices for AI agent security
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-200 hover:border-blue-400 transition">
              <div className="text-3xl mb-3">🔑</div>
              <h4 className="font-semibold text-gray-900 mb-2">JWT Validation</h4>
              <p className="text-sm text-gray-600">All API requests validated against Auth0 JWKS endpoints</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-lg border border-purple-200 hover:border-purple-400 transition">
              <div className="text-3xl mb-3">🔐</div>
              <h4 className="font-semibold text-gray-900 mb-2">Secure Token Management</h4>
              <p className="text-sm text-gray-600">Auth0 Management API with short-lived tokens, zero stored credentials</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-lg border border-green-200 hover:border-green-400 transition">
              <div className="text-3xl mb-3">📝</div>
              <h4 className="font-semibold text-gray-900 mb-2">Audit Logging</h4>
              <p className="text-sm text-gray-600">Complete trail of every agent action and API call</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-lg border border-yellow-200 hover:border-yellow-400 transition">
              <div className="text-3xl mb-3">🎯</div>
              <h4 className="font-semibold text-gray-900 mb-2">Scoped Access</h4>
              <p className="text-sm text-gray-600">Minimal permissions enforced for each operation</p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center py-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl mb-12">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Experience Real AI Agents?
          </h3>
          <p className="text-blue-100 text-lg mb-8 max-w-2xl mx-auto">
            See how Auth0 for AI enables secure, intelligent calendar management 
            with actual API integrations—no mock data, no templates.
          </p>
          {user ? (
            <Link
              href="/chat"
              className="inline-flex items-center px-8 py-4 text-lg font-medium rounded-lg text-blue-700 bg-white hover:bg-gray-100 transition shadow-lg"
            >
              🚀 Open Chat Interface →
            </Link>
          ) : (
            <a
              href="/api/auth/login"
              className="inline-flex items-center px-8 py-4 text-lg font-medium rounded-lg text-blue-700 bg-white hover:bg-gray-100 transition shadow-lg"
            >
              🔐 Get Started with Google →
            </a>
          )}
        </div>
      </main>
    </div>
  )
}