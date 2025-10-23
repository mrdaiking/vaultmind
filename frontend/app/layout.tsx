import './globals.css'
import { UserProvider } from '@auth0/nextjs-auth0/client'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'VaultMind - Secure AI Agent',
  description: 'Secure AI Agent with Auth0 for AI demonstration',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50`}>
        <UserProvider>
          {children}
        </UserProvider>
      </body>
    </html>
  )
}