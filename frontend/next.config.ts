import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  typedRoutes: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/:path*`,
      },
    ]
  },
}

export default nextConfig

