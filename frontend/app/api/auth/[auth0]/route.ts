import { handleAuth, handleLogin, handleCallback } from '@auth0/nextjs-auth0'

// Next.js 15 requires async handling of dynamic route params
export const GET = handleAuth()