import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Cinzel, Cinzel_Decorative, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { BrandLogo } from "@/components/Brand";
import { SiteHeader } from "@/components/SiteHeader";

// Font di-host sendiri oleh Next (diunduh saat build); peramban pengunjung tidak menghubungi Google.
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-plus-jakarta", display: "swap" });
const cinzel = Cinzel({ subsets: ["latin"], weight: ["600", "700", "800"], variable: "--font-cinzel-face", display: "swap" });
const cinzelDeco = Cinzel_Decorative({ subsets: ["latin"], weight: ["700", "900"], variable: "--font-cinzel-deco", display: "swap" });

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const DESC = "Jelajahi kekayaan pencak silat Nusantara: tradisi dari 38 provinsi, gerakan yang diperagakan karakter 3D fase demi fase, peta tempat latihan, dan latihan kamera yang berjalan di perangkat Anda.";
const TITLE = "SILATARA — Warisan Gerak, Generasi Bergerak";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: TITLE, template: "%s — SILATARA" },
  description: DESC,
  applicationName: "SILATARA",
  openGraph: { type: "website", siteName: "SILATARA", locale: "id_ID", title: TITLE, description: DESC },
  twitter: { card: "summary_large_image", title: TITLE, description: DESC },
};
export const viewport: Viewport = { themeColor: "#4a0d0d" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const fl = "transition-colors hover:text-red-900";
  return (
    <html lang="id" className={`${jakarta.variable} ${cinzel.variable} ${cinzelDeco.variable}`}>
      <body className="flex min-h-screen flex-col bg-[#f8fafc] font-sans text-slate-900 antialiased selection:bg-orange-500/20 selection:text-red-950">
        <a href="#utama" className="sr-only focus:not-sr-only focus:absolute focus:m-3 focus:rounded-lg focus:bg-white focus:p-3 focus:shadow-md">Lewati ke konten utama</a>
        <SiteHeader />
        <main id="utama" className="w-full flex-1 overflow-x-clip animate-page-entrance"><div className="mx-auto w-full max-w-[1200px] px-5 py-10 [&:has(>[data-fullbleed])]:max-w-none [&:has(>[data-fullbleed])]:p-0">{children}</div></main>
        <footer className="border-t border-slate-200/80 bg-white/80 backdrop-blur-md">
          <div className="mx-auto max-w-[1200px] px-6 py-12">
            <div className="grid gap-10 lg:grid-cols-[1.7fr_1fr_1fr_1fr]">
              <div className="space-y-4">
                <BrandLogo size={44} />
                <p className="max-w-md text-sm leading-relaxed text-slate-600">Platform untuk mengenal, mempelajari, dan melestarikan pencak silat Indonesia. Pengetahuan umum terbuka untuk semua; berlatihlah bersama pelatih untuk menguasai teknik.</p>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">Belajar</h4>
                <ul className="space-y-2.5 text-sm text-slate-600">
                  <li><Link className={fl} href="/library">Pustaka Gerakan</Link></li>
                  <li><Link className={fl} href="/academy">Akademi</Link></li>
                  <li><Link className={fl} href="/library/kuda-kuda-tengah/latihan">Latihan Kamera</Link></li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">Jelajahi</h4>
                <ul className="space-y-2.5 text-sm text-slate-600">
                  <li><Link className={fl} href="/heritage">Warisan 38 Provinsi</Link></li>
                  <li><Link className={fl} href="/community">Peta Perguruan</Link></li>
                  <li><Link className={fl} href="/community/kirim-tempat">Kirim Tempat Latihan</Link></li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">Akun</h4>
                <ul className="space-y-2.5 text-sm text-slate-600">
                  <li><Link className={fl} href="/masuk">Masuk</Link></li>
                  <li><Link className={fl} href="/daftar">Daftar</Link></li>
                  <li><Link className={fl} href="/status">Status Layanan</Link></li>
                </ul>
              </div>
            </div>
            <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-slate-200/80 pt-6 text-xs text-slate-500 md:flex-row">
              <p>© 2026 SILATARA. Warisan Gerak, Generasi Bergerak.</p>
              <p>Peta: © kontributor OpenStreetMap · Kamera diproses di perangkat Anda, video tidak dikirim.</p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
