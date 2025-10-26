/**
 * EventsList component
 * Displays a list of events grouped by date.
 *
 * @author Felix
 * @created 2025-10-25
 */
import React from 'react'
import EventCard from './EventCard'

interface Event {
  summary: string
  start: string
  end?: string
  description?: string
}

interface EventsListProps {
  events: Event[]
  title?: string
  emptyMessage?: string
}

export default function EventsList({
  events,
  title,
  emptyMessage,
}: EventsListProps) {
  if (events.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <span className="text-4xl mb-2 block">📅</span>
        <p className="text-gray-600">{emptyMessage || 'No events found'}</p>
      </div>
    )
  }

  // Group events by date
  const groupedEvents = events.reduce((acc, event) => {
    const date = new Date(event.start).toDateString()
    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(event)
    return acc
  }, {} as Record<string, Event[]>)

  const sortedDates = Object.keys(groupedEvents).sort(
    (a, b) => new Date(a).getTime() - new Date(b).getTime()
  )

  return (
    <div className="space-y-6">
      {title && (
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
            {events.length} {events.length === 1 ? 'event' : 'events'}
          </span>
        </div>
      )}

      {sortedDates.map((dateStr, dateIndex) => {
        const date = new Date(dateStr)
        const dateEvents = groupedEvents[dateStr]
        const today = new Date()
        const isToday = date.toDateString() === today.toDateString()
        const tomorrow = new Date(today)
        tomorrow.setDate(tomorrow.getDate() + 1)
        const isTomorrow = date.toDateString() === tomorrow.toDateString()

        let dateLabel = date.toLocaleDateString('en-US', {
          weekday: 'long',
          month: 'long',
          day: 'numeric',
          year:
            date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
        })

        if (isToday) {
          dateLabel = `Today - ${dateLabel}`
        } else if (isTomorrow) {
          dateLabel = `Tomorrow - ${dateLabel}`
        }

        return (
          <div key={dateStr} className="space-y-3">
            <div className="sticky top-0 bg-white/95 backdrop-blur-sm py-2 z-10">
              <h4 className="text-sm font-bold text-gray-700 uppercase tracking-wide flex items-center">
                <span
                  className={`w-2 h-2 rounded-full mr-2 ${
                    isToday
                      ? 'bg-green-500'
                      : isTomorrow
                      ? 'bg-blue-500'
                      : 'bg-gray-400'
                  }`}
                ></span>
                {dateLabel}
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  ({dateEvents.length}{' '}
                  {dateEvents.length === 1 ? 'event' : 'events'})
                </span>
              </h4>
            </div>

            <div className="space-y-3 ml-4">
              {dateEvents
                .sort(
                  (a, b) =>
                    new Date(a.start).getTime() - new Date(b.start).getTime()
                )
                .map((event, eventIndex) => (
                  <EventCard
                    key={`${dateStr}-${eventIndex}`}
                    event={event}
                    index={events.indexOf(event)}
                  />
                ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
