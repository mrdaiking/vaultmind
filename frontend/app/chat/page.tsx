'use client'

import { useUser, withPageAuthRequired } from '@auth0/nextjs-auth0/client'
import { useState, useRef, useEffect } from 'react'
import EventCard from '@/components/EventCard'
import EventsList from '@/components/EventsList'
import TimezoneSelector from '@/components/TimezoneSelector'

interface Event {
  summary: string
  start: string
  end?: string
  description?: string
}

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  actionTaken?: string
  success?: boolean
  eventDetails?: Event
  events?: Event[]
  conflicts?: Event[]
}

interface ChatResponse {
  response: string
  action_taken?: string
  success: boolean
  timestamp: string
  event_details?: Event
  events?: Event[]
  conflicts?: Event[]
}

const EXAMPLE_PROMPTS = [
  "📅 What's on my calendar tomorrow?",
  "➕ Schedule team standup Monday at 9am",
  "🔍 Am I free Friday afternoon?",
  "📝 Create dentist appointment next Tuesday at 10am"
]

function ChatPage() {
  const { user } = useUser()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your secure AI calendar assistant powered by Auth0 for AI Agents. I can help you manage your Google Calendar with real-time API integration.\n\nTry one of the example prompts below or ask me anything about your calendar!',
      isUser: false,
      timestamp: new Date(),
      success: true
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showExamples, setShowExamples] = useState(true)
  const [timezone, setTimezone] = useState<string>('UTC')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const savedTimezone = localStorage.getItem('vaultmind_timezone')
    if (savedTimezone) {
      setTimezone(savedTimezone)
    }
  }, [])

  const sendMessage = async (message?: string) => {
    const messageToSend = message || inputMessage
    if (!messageToSend.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageToSend,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setShowExamples(false)

    try {
      // Call our Next.js API route which handles auth server-side
      // This avoids Next.js 15 async cookie warnings in the client
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          message: messageToSend,
          timezone: timezone 
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Request failed: ${response.status}`)
      }

      const data: ChatResponse = await response.json()

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isUser: false,
        timestamp: new Date(data.timestamp),
        actionTaken: data.action_taken,
        success: data.success,
        eventDetails: data.event_details,
        events: data.events,
        conflicts: data.conflicts
      }

      setMessages(prev => [...prev, agentMessage])

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        isUser: false,
        timestamp: new Date(),
        success: false
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleSendClick = () => {
    sendMessage()
  }

  const handleExampleClick = (prompt: string) => {
    sendMessage(prompt)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <a href="/" className="text-2xl font-bold text-vault-blue">🔐 VaultMind</a>
              <span className="ml-4 text-gray-600">Chat with AI Agent</span>
            </div>
            <div className="flex items-center space-x-4">
              <TimezoneSelector onTimezoneChange={setTimezone} />
              <span className="text-gray-700">Logged in as {user?.name}</span>
              <a
                href="/api/auth/logout"
                className="text-gray-600 hover:text-gray-900 transition"
              >
                Logout
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-xl min-h-[600px] flex flex-col">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div key={message.id}>
                <div
                  className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.isUser
                        ? 'bg-vault-blue text-white'
                        : message.success === false
                        ? 'bg-red-100 text-red-800 border border-red-300'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-line">{message.content}</p>
                    {message.actionTaken && (
                      <p className="text-xs mt-1 opacity-75">
                        Action: {message.actionTaken}
                      </p>
                    )}
                    <p className="text-xs mt-1 opacity-75">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                
                {/* Single Event Preview Card */}
                {message.eventDetails && message.success && !message.events && (
                  <div className="flex justify-start mt-2">
                    <div className="max-w-xs lg:max-w-md bg-green-50 border border-green-200 rounded-lg px-4 py-3">
                      <div className="flex items-start space-x-2">
                        <span className="text-2xl">✅</span>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-green-900">
                            Event Created Successfully!
                          </p>
                          <div className="mt-2">
                            <EventCard event={message.eventDetails} />
                          </div>
                          
                          {/* Show conflicts if any */}
                          {message.conflicts && message.conflicts.length > 0 && (
                            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-300 rounded">
                              <p className="text-xs font-semibold text-yellow-900 flex items-center">
                                <span className="mr-1">⚠️</span>
                                {message.conflicts.length === 1 ? 'Scheduling Conflict Detected' : `${message.conflicts.length} Conflicts Detected`}
                              </p>
                              <div className="mt-1 space-y-1">
                                {message.conflicts.slice(0, 2).map((conflict, idx) => (
                                  <p key={idx} className="text-xs text-yellow-800">
                                    • {conflict.summary} at {new Date(conflict.start).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                                  </p>
                                ))}
                                {message.conflicts.length > 2 && (
                                  <p className="text-xs text-yellow-700 italic">
                                    + {message.conflicts.length - 2} more...
                                  </p>
                                )}
                              </div>
                            </div>
                          )}
                          
                          <div className="mt-3 space-y-1">
                            <a
                              href="https://calendar.google.com"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-block text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition"
                            >
                              View in Google Calendar →
                            </a>
                            <p className="text-xs text-green-600 mt-2">
                              🔍 <strong>Verify it's real:</strong> Open Google Calendar and see this event in your actual calendar!
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Multiple Events List */}
                {message.events && message.events.length > 0 && (
                  <div className="flex justify-start mt-2">
                    <div className="max-w-2xl w-full bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                      <EventsList 
                        events={message.events}
                        title="Your Calendar Events"
                        emptyMessage="No events found for this period"
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm">Connecting to Google Calendar API...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Example Prompts */}
          {showExamples && (
            <div className="border-t border-gray-200 px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50">
              <p className="text-xs font-semibold text-gray-700 mb-2">💡 Try these example prompts:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {EXAMPLE_PROMPTS.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(prompt.replace(/^[^\s]+\s/, ''))}
                    disabled={isLoading}
                    className="text-left text-xs bg-white border border-gray-200 rounded-lg px-3 py-2 hover:bg-blue-50 hover:border-blue-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-4">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your calendar..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-vault-blue focus:border-transparent"
                disabled={isLoading}
              />
              <button
                onClick={handleSendClick}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-vault-blue text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                🔒 Secured with Auth0 JWT • 🔗 Real Google Calendar API
              </p>
              {!showExamples && (
                <button
                  onClick={() => setShowExamples(true)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Show examples
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Why VaultMind is Different */}
        <div className="mt-8 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-3">✨ Why VaultMind is Different</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-start space-x-3">
              <span className="text-green-600 font-bold">✅</span>
              <div>
                <p className="font-semibold text-gray-900">Real API Integration</p>
                <p className="text-gray-700">Events are created in your actual Google Calendar, not mock data</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-green-600 font-bold">✅</span>
              <div>
                <p className="font-semibold text-gray-900">True AI Agents with Tool Calling</p>
                <p className="text-gray-700">OpenAI function calling, not just template prompts</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-green-600 font-bold">✅</span>
              <div>
                <p className="font-semibold text-gray-900">Auth0 Token Vault in Action</p>
                <p className="text-gray-700">Secure token exchange for Google Calendar access without storing credentials</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-green-600 font-bold">✅</span>
              <div>
                <p className="font-semibold text-gray-900">Verifiable Results</p>
                <p className="text-gray-700">Open <a href="https://calendar.google.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">calendar.google.com</a> and see the events you create!</p>
              </div>
            </div>
          </div>
        </div>

        {/* Security Information */}
        {/* <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-md font-semibold text-blue-900 mb-2">🔐 Security Features Active</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-blue-800">
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              JWT Authentication Verified
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Auth0 Token Vault Active
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Google Calendar API Connected
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Scoped API Permissions
            </div>
          </div>
        </div> */}
      </div>
    </div>
  )
}

export default withPageAuthRequired(ChatPage)