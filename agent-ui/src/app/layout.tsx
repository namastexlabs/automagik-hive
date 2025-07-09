import type { Metadata } from 'next'
import { Alegreya_Sans, Manrope } from 'next/font/google'
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import { Toaster } from '@/components/ui/sonner'
import './globals.css'

const alegreyaSans = Alegreya_Sans({ 
  subsets: ["latin"], 
  variable: "--font-primary",
  weight: ["300", "400", "500", "700", "800", "900"]
})

const manrope = Manrope({ 
  subsets: ["latin"], 
  variable: "--font-secondary",
  weight: ["200", "300", "400", "500", "600", "700", "800"]
})

export const metadata: Metadata = {
  title: 'Automagik - AI Agent UI',
  description:
    'A modern chat interface for AI agents built with Next.js, Tailwind CSS, and TypeScript. This template provides a ready-to-use UI for interacting with Automagik agents.'
}

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${alegreyaSans.variable} ${manrope.variable} font-sans antialiased`}>
        <NuqsAdapter>{children}</NuqsAdapter>
        <Toaster />
      </body>
    </html>
  )
}
