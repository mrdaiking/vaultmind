/**
 * EventCard component
 * Displays individual event details including summary, date, time, duration, and description.
 * 
 * @author Felix
 * @created 2025-10-25
 */
import React from 'react'

interface EventCardProps {
  event: {
    summary: string
    start: string
    end?: string
    description?: string
  }
  index?: number
}

export default function EventCard({ event, index }: EventCardProps) {
  const startDate = new Date(event.start)
  const endDate = event.end ? new Date(event.end) : null
  
  // Format date in a friendly way
  const formatDate = (date: Date) => {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    
    const dateStr = date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
    })
    
    if (date.toDateString() === today.toDateString()) {
      return '📅 Today'
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return '📅 Tomorrow'
    } else {
      const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'short' })
      return `📅 ${dayOfWeek}, ${dateStr}`
    }
  }
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric',
      minute: '2-digit',
      hour12: true 
    })
  }
  
  const getEventIcon = (summary: string) => {
    // const lower = summary.toLowerCase()
    // if (lower.includes('meeting') || lower.includes('会議')) return '👥'
    // if (lower.includes('standup') || lower.includes('scrum')) return '🏃'
    // if (lower.includes('lunch') || lower.includes('dinner')) return '🍽️'
    // if (lower.includes('break') || lower.includes('休憩')) return '☕'
    // if (lower.includes('interview')) return '💼'
    // if (lower.includes('review')) return '📋'
    // if (lower.includes('準備') || lower.includes('prepare')) return '📝'
    // if (lower.includes('緊急') || lower.includes('urgent')) return '🚨'
    // if (lower.includes('確認') || lower.includes('check')) return '✅'
    return '📌'
  }
  
  const getEventColor = (summary: string) => {
    // const lower = summary.toLowerCase()
    // if (lower.includes('緊急') || lower.includes('urgent')) {
    //   return 'border-red-300 bg-gradient-to-br from-red-50 to-pink-50'
    // }
    // if (lower.includes('standup') || lower.includes('scrum')) {
    //   return 'border-blue-300 bg-gradient-to-br from-blue-50 to-cyan-50'
    // }
    // if (lower.includes('meeting') || lower.includes('会議')) {
    //   return 'border-purple-300 bg-gradient-to-br from-purple-50 to-indigo-50'
    // }
    // if (lower.includes('準備') || lower.includes('prepare')) {
    //   return 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-amber-50'
    // }
    return 'border-gray-300 bg-gradient-to-br from-gray-50 to-slate-50'
  }
  
  const duration = endDate 
    ? Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60))
    : null

  return (
    <div className={`border-l-4 ${getEventColor(event.summary)} rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow duration-200`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl">{getEventIcon(event.summary)}</span>
            <h4 className="font-semibold text-gray-900 text-base">
              {event.summary}
            </h4>
          </div>
          
          <div className="space-y-1 text-sm">
            <div className="flex items-center text-gray-700">
              <span className="font-medium">{formatDate(startDate)}</span>
            </div>
            
            <div className="flex items-center space-x-3 text-gray-600">
              <span className="flex items-center">
                🕐 {formatTime(startDate)}
                {endDate && (
                  <>
                    <span className="mx-1">→</span>
                    {formatTime(endDate)}
                  </>
                )}
              </span>
              {duration && (
                <span className="text-xs bg-white/60 px-2 py-0.5 rounded-full">
                  {duration} min
                </span>
              )}
            </div>
          </div>
          
          {event.description && (
            <p className="mt-2 text-xs text-gray-600 italic">
              {event.description}
            </p>
          )}
        </div>
        
        {index !== undefined && (
          <span className="ml-3 flex-shrink-0 w-6 h-6 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">
            {index + 1}
          </span>
        )}
      </div>
    </div>
  )
}
