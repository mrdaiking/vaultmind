/**
 * TimezoneSelector component
 * Allows users to select their timezone for event scheduling.
 *
 * @author Felix
 * @created 2025-10-25
 */
'use client'

import { useState, useEffect } from 'react'

interface TimezoneSelectorProps {
  onTimezoneChange?: (timezone: string) => void
}

// Common timezones
const TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HST)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET)' },
  { value: 'Europe/Moscow', label: 'Moscow (MSK)' },
  { value: 'Asia/Dubai', label: 'Dubai (GST)' },
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Asia/Hong_Kong', label: 'Hong Kong (HKT)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEDT)' },
  { value: 'Pacific/Auckland', label: 'Auckland (NZDT)' },
]

export default function TimezoneSelector({
  onTimezoneChange,
}: TimezoneSelectorProps) {
  const [selectedTimezone, setSelectedTimezone] = useState<string>('UTC')
  const [currentTime, setCurrentTime] = useState<string>('')
  const [isOpen, setIsOpen] = useState(false)

  // Load timezone from localStorage on mount
  useEffect(() => {
    const savedTimezone = localStorage.getItem('vaultmind_timezone')
    if (savedTimezone) {
      setSelectedTimezone(savedTimezone)
    } else {
      // Try to detect user's timezone
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone
      const matchingTimezone = TIMEZONES.find((tz) => tz.value === detected)
      if (matchingTimezone) {
        setSelectedTimezone(detected)
        localStorage.setItem('vaultmind_timezone', detected)
      }
    }
  }, [])

  // Update current time every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: selectedTimezone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      })
      setCurrentTime(formatter.format(now))
    }

    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [selectedTimezone])

  const handleTimezoneChange = (timezone: string) => {
    setSelectedTimezone(timezone)
    localStorage.setItem('vaultmind_timezone', timezone)
    setIsOpen(false)
    onTimezoneChange?.(timezone)
  }

  const selectedLabel =
    TIMEZONES.find((tz) => tz.value === selectedTimezone)?.label ||
    selectedTimezone

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition text-sm"
        title="Change timezone"
      >
        <span className="text-lg">🌍</span>
        <div className="text-left">
          <div className="font-medium text-gray-900">{currentTime}</div>
          <div className="text-xs text-gray-500 truncate max-w-[120px]">
            {selectedLabel.split(' ')[0]}
          </div>
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-96 overflow-y-auto">
            <div className="p-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
              <h3 className="font-semibold text-gray-900 text-sm">
                🌍 Select Your Timezone
              </h3>
              <p className="text-xs text-gray-600 mt-1">
                Events will be created using this timezone
              </p>
            </div>
            <div className="py-1">
              {TIMEZONES.map((timezone) => (
                <button
                  key={timezone.value}
                  onClick={() => handleTimezoneChange(timezone.value)}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-blue-50 transition ${
                    selectedTimezone === timezone.value
                      ? 'bg-blue-100 text-blue-900 font-medium'
                      : 'text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span>{timezone.label}</span>
                    {selectedTimezone === timezone.value && (
                      <span className="text-blue-600">✓</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
