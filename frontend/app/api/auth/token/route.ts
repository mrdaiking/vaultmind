import { NextResponse } from 'next/server'
import { getSession } from '@auth0/nextjs-auth0'

// Disable static optimization to ensure this runs on the server
export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // getSession will handle cookies internally
    // The warning is from Auth0 SDK, but it still works
    const session = await getSession()
    
    if (!session || !session.accessToken) {
      return NextResponse.json(
        { error: 'No access token available' },
        { status: 401 }
      )
    }
    
    return NextResponse.json({ accessToken: session.accessToken })
  } catch (error) {
    console.error('Error getting access token:', error)
    return NextResponse.json(
      { error: 'Failed to get access token' },
      { status: 500 }
    )
  }
}