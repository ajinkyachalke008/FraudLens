import type { Metadata } from 'next'
import './globals.css'
import Providers from './providers'
import GlobalSidebar from '@/components/layout/GlobalSidebar'
import TopBar from '@/components/layout/TopBar'
import { Toaster } from 'sonner'

export const metadata: Metadata = {
  title: 'FraudLens — Cybercrime Intelligence Platform',
  description: 'GNN-powered fraud investigation platform for Pune Police Cybercrime Cell',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-background-base text-white font-sans antialiased">
        <Providers>
          <GlobalSidebar />
          <div className="ml-[72px] min-h-screen flex flex-col">
            <TopBar />
            <main className="flex-1">
              {children}
            </main>
          </div>
        </Providers>
        <Toaster theme="dark" position="top-right" richColors />
      </body>
    </html>
  )
}
