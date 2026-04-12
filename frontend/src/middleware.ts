import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const PUBLIC_PATHS = ["/auth/login", "/auth/register"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow public routes
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  // Allow static assets
  if (pathname.startsWith("/_next") || pathname.includes(".")) {
    return NextResponse.next()
  }

  // Proxy API requests to the backend at runtime
  if (pathname.startsWith("/api/")) {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    return NextResponse.rewrite(new URL(pathname + request.nextUrl.search, backendUrl))
  }

  // Check for auth token in cookies (set by client-side auth)
  const token = request.cookies.get("vectory_access_token")?.value
  if (!token) {
    const loginUrl = new URL("/auth/login", request.url)
    loginUrl.searchParams.set("redirect", pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
