import { NextResponse, type NextRequest } from "next/server";

/**
 * Meneruskan path asal ke Server Component (layout /app) agar redirect login dapat kembali ke halaman
 * semula. Header selalu DITIMPA di sini, jadi nilai kiriman klien tidak pernah dipercaya.
 */
export function proxy(req: NextRequest) {
  const headers = new Headers(req.headers);
  headers.set("x-silatara-path", req.nextUrl.pathname + req.nextUrl.search);
  return NextResponse.next({ request: { headers } });
}

export const config = { matcher: ["/app/:path*"] };
