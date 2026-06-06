import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Add paths that do not require authentication
const publicPaths = ['/login', '/_next', '/favicon.ico', '/api'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for public paths and static assets
  if (
    publicPaths.some(path => pathname.startsWith(path)) ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Check for the auth token in cookies
  const token = request.cookies.get('fraudlens_token')?.value;

  // If no token exists and we're not on a public path, redirect to login
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
