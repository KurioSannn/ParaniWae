import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Hanya berlaku di `next dev`: izinkan membuka aplikasi lewat http://127.0.0.1:<port> selain localhost
  // (tanpa ini, sumber dev diblokir dan komponen klien seperti tombol login demo tidak berfungsi).
  allowedDevOrigins: ["127.0.0.1"],
  // Unggahan media (maks. 100 MB, ditegakkan backend) melewati proxy/rewrite Next: batas bawaan 10 MB membuat unggahan >10 MB
  // gagal (ECONNRESET) — terbukti oleh e2e-browser/tests/ops.spec.ts. Backend tetap pemegang batas sebenarnya (413).
  experimental: { proxyClientMaxBodySize: "110mb" },
  // API same-origin: browser memanggil /api/v1/* pada origin frontend, Next meneruskan ke backend.
  // Cookie sesi jadi first-party (lihat docs/adr/0002-authentication.md).
  // Bagian /riset dilebur ke halaman utama (ADR-0008); tautan lama dialihkan permanen ke URL kanonik.
  async redirects() {
    return [
      { source: "/riset", destination: "/heritage", permanent: true },
      { source: "/riset/gerakan", destination: "/library", permanent: true },
      { source: "/riset/gerakan/:slug", destination: "/library/:slug", permanent: true },
      { source: "/riset/kurikulum", destination: "/academy", permanent: true },
      { source: "/riset/kurikulum/:course", destination: "/academy/courses/:course", permanent: true },
      { source: "/riset/kurikulum/:course/:lesson", destination: "/academy/courses/:course/lessons/:lesson", permanent: true },
      { source: "/riset/cakupan", destination: "/heritage#wilayah", permanent: true },
      { source: "/riset/sumber", destination: "/heritage", permanent: true },
      { source: "/heritage/referensi", destination: "/heritage", permanent: true },
      { source: "/community", destination: "/community/peta", permanent: false },
    ];
  },
  async rewrites() {
    const target = process.env.INTERNAL_API_URL ?? "http://backend:8000";
    return [{ source: "/api/v1/:path*", destination: `${target}/api/v1/:path*` }];
  },
  // Kamera & lokasi: hanya halaman sendiri, opt-in lewat tombol (latihan kamera; "lokasi terdekat" di peta, tidak disimpan).
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(self), microphone=(), geolocation=(self)" },
        ],
      },
    ];
  },
};

export default nextConfig;
