import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@auth0/nextjs-auth0'

export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  try {
    // Get the user session (includes access token)
    // Note: This generates a Next.js 15 warning but still works
    // Auth0 SDK needs to be updated for Next.js 15 compatibility
    const session = await getSession()
    
    console.log('Session retrieved:', session ? 'Yes' : 'No')
    console.log('Has accessToken:', session?.accessToken ? 'Yes' : 'No')
    
    if (!session || !session.accessToken) {
      console.error('No session or access token found')
      return NextResponse.json(
        { error: 'Unauthorized - No valid session' },
        { status: 401 }
      )
    }

    // Get the message from request body
    const body = await request.json()
    const { message, timezone } = body

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    console.log('Calling backend with token:', session.accessToken.substring(0, 20) + '...')
    console.log('Timezone:', timezone || 'UTC')

    // Call backend API with the access token
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${apiUrl}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.accessToken}`
      },
      body: JSON.stringify({ 
        message,
        timezone: timezone || 'UTC'
      })
    })

    console.log('Backend response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error:', errorText)
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('Chat proxy error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
