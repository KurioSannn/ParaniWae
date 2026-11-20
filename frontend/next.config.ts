import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // API same-origin: browser memanggil /api/v1/* pada origin frontend, Next meneruskan ke backend.
  // Cookie sesi jadi first-party (lihat docs/adr/0002-authentication.md).
  async rewrites() {
    const target = process.env.INTERNAL_API_URL ?? "http://backend:8000";
    return [{ source: "/api/v1/:path*", destination: `${target}/api/v1/:path*` }];
  },
  // Kamera & mikrofon: hanya halaman sendiri; kamera diizinkan untuk latihan (opt-in oleh pengguna).
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(self), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
