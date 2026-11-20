import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: { default: "SILATARA — Warisan Pencak Silat", template: "%s — SILATARA" },
  description: "Platform pembelajaran dan pelestarian pencak silat Nusantara (tahap pengembangan awal).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="flex min-h-screen flex-col">
        <a href="#utama" className="sr-only focus:not-sr-only focus:absolute focus:m-3 focus:rounded-lg focus:bg-paper-50 focus:p-3">
          Lewati ke konten utama
        </a>
        <SiteHeader />
        <main id="utama" className="mx-auto w-full max-w-[1200px] flex-1 px-5 py-10">{children}</main>
        <footer className="border-t border-line-200 px-5 py-8 text-center text-sm text-slate-600">
          <p>Tahap pengembangan awal. Isi bertanda <strong>[DEMO]</strong> adalah contoh teknis, bukan materi budaya resmi.</p>
          <p className="mt-1">AI adalah alat bantu latihan, bukan pengganti instruktur. <Link className="underline" href="/status">Status sistem</Link></p>
        </footer>
      </body>
    </html>
  );
}
