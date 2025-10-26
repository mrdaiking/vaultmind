import { NextRequest, NextResponse } from 'next/server'
import { writeFile, readFile } from 'fs/promises'
import { join } from 'path'
import { getSession } from '@auth0/nextjs-auth0'
import { Resend } from 'resend'

// Simple JSON file storage for demo (use a proper database in production)
const WAITLIST_FILE = join(process.cwd(), 'waitlist.json')

// Admin emails who can access waitlist data
// Load from environment variable (comma-separated list)
const ADMIN_EMAILS = process.env.NEXT_PUBLIC_ADMIN_EMAILS?.split(',').map(e => e.trim()) || []

// Initialize Resend (only if API key is provided)
const resend = process.env.RESEND_API_KEY ? new Resend(process.env.RESEND_API_KEY) : null

interface WaitlistEntry {
  email: string
  useCase: string
  timestamp: string
  ip?: string
  userAgent?: string
}

async function getWaitlist(): Promise<WaitlistEntry[]> {
  try {
    const data = await readFile(WAITLIST_FILE, 'utf-8')
    return JSON.parse(data)
  } catch {
    return []
  }
}

async function addToWaitlist(entry: WaitlistEntry): Promise<void> {
  const waitlist = await getWaitlist()
  
  // Check for duplicates
  const exists = waitlist.some(e => e.email.toLowerCase() === entry.email.toLowerCase())
  if (exists) {
    throw new Error('Email already registered')
  }
  
  waitlist.push(entry)
  await writeFile(WAITLIST_FILE, JSON.stringify(waitlist, null, 2))
}

// Send email notification to admins
async function notifyAdmins(entry: WaitlistEntry): Promise<void> {
  if (!resend || ADMIN_EMAILS.length === 0) {
    console.log('⚠️ Email notification skipped:')
    console.log('  - Resend API key configured:', !!process.env.RESEND_API_KEY)
    console.log('  - Admin emails configured:', ADMIN_EMAILS.length > 0 ? ADMIN_EMAILS : 'None')
    return
  }

  try {
    const totalSignups = (await getWaitlist()).length
    const fromEmail = process.env.RESEND_FROM_EMAIL || 'VaultMind <onboarding@resend.dev>'
    
    console.log('📧 Sending email notification...')
    console.log('  - From:', fromEmail)
    console.log('  - To:', ADMIN_EMAILS)
    console.log('  - Signup #:', totalSignups)
    
    const result = await resend.emails.send({
      from: fromEmail,
      to: ADMIN_EMAILS,
      subject: `🎉 New Waitlist Signup #${totalSignups} - VaultMind`,
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: linear-gradient(to right, #2563eb, #9333ea); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">🚀 New Waitlist Signup!</h1>
          </div>
          
          <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
              <h2 style="color: #1f2937; margin-top: 0;">Signup #${totalSignups}</h2>
              
              <div style="margin: 15px 0;">
                <strong style="color: #6b7280;">Email:</strong><br/>
                <span style="color: #1f2937; font-size: 16px;">${entry.email}</span>
              </div>
              
              ${entry.useCase ? `
                <div style="margin: 15px 0;">
                  <strong style="color: #6b7280;">Use Case:</strong><br/>
                  <span style="color: #1f2937;">${entry.useCase}</span>
                </div>
              ` : ''}
              
              <div style="margin: 15px 0;">
                <strong style="color: #6b7280;">Timestamp:</strong><br/>
                <span style="color: #1f2937;">${new Date(entry.timestamp).toLocaleString()}</span>
              </div>
            </div>
            
            <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
              <p style="margin: 0; color: #1e40af;">
                <strong>📊 Total Signups:</strong> ${totalSignups}
              </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
              <a href="${process.env.AUTH0_BASE_URL}/validation" 
                 style="background: linear-gradient(to right, #2563eb, #9333ea); 
                        color: white; 
                        padding: 12px 24px; 
                        text-decoration: none; 
                        border-radius: 6px; 
                        display: inline-block;
                        font-weight: bold;">
                View Dashboard →
              </a>
            </div>
            
            <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 30px;">
              VaultMind Validation Dashboard • 
              <a href="${process.env.AUTH0_BASE_URL}" style="color: #2563eb;">Visit Site</a>
            </p>
          </div>
        </div>
      `,
      text: `
New VaultMind Waitlist Signup #${totalSignups}

Email: ${entry.email}
${entry.useCase ? `Use Case: ${entry.useCase}` : 'No use case provided'}
Timestamp: ${new Date(entry.timestamp).toLocaleString()}

Total Signups: ${totalSignups}

View Dashboard: ${process.env.AUTH0_BASE_URL}/validation
      `
    })
    
    console.log('✅ Email sent successfully!')
    console.log('  - Email ID:', result.data?.id)
    console.log('  - Check your inbox:', ADMIN_EMAILS.join(', '))
  } catch (error) {
    console.error('❌ Failed to send admin notification:')
    console.error('  - Error:', error)
    // Don't throw - email failure shouldn't block waitlist signup
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, useCase, timestamp } = body

    // Basic validation
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Valid email required' },
        { status: 400 }
      )
    }

    // Collect metadata for analytics
    const entry: WaitlistEntry = {
      email: email.toLowerCase().trim(),
      useCase: useCase?.trim() || '',
      timestamp,
      ip: request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown',
      userAgent: request.headers.get('user-agent') || 'unknown',
    }

    await addToWaitlist(entry)

    // Send notification to admins (non-blocking)
    await notifyAdmins(entry)

    return NextResponse.json({ 
      success: true,
      message: 'Successfully joined waitlist' 
    })

  } catch (error: any) {
    console.error('Waitlist error:', error)
    
    if (error.message === 'Email already registered') {
      return NextResponse.json(
        { error: 'This email is already on the waitlist' },
        { status: 409 }
      )
    }

    return NextResponse.json(
      { error: 'Failed to join waitlist' },
      { status: 500 }
    )
  }
}

// GET endpoint to view waitlist (PROTECTED - admin only)
export async function GET(request: NextRequest) {
  try {
    // Check authentication
    const session = await getSession()
    const userEmail = session?.user?.email

    // Verify admin access
    if (!userEmail || !ADMIN_EMAILS.includes(userEmail)) {
      return NextResponse.json(
        { error: 'Unauthorized - Admin access required' },
        { status: 401 }
      )
    }

    const waitlist = await getWaitlist()
    
    return NextResponse.json({
      total: waitlist.length,
      entries: waitlist,
      stats: {
        withUseCase: waitlist.filter(e => e.useCase).length,
        recent24h: waitlist.filter(e => {
          const entryTime = new Date(e.timestamp).getTime()
          const now = Date.now()
          return now - entryTime < 24 * 60 * 60 * 1000
        }).length
      }
    })

  } catch (error) {
    console.error('Waitlist GET error:', error)
    return NextResponse.json(
      { error: 'Failed to retrieve waitlist' },
      { status: 500 }
    )
  }
}
