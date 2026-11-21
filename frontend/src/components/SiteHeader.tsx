import Link from "next/link";
import { Menu } from "lucide-react";
import { getCurrentUser } from "@/lib/server-api";
import { BrandLogo } from "@/components/Brand";
import { LogoutButton } from "@/components/LogoutButton";

const links = [
  { href: "/", label: "Beranda" },
  { href: "/heritage", label: "Jelajahi Warisan" },
  { href: "/library", label: "Pustaka Gerakan" },
  { href: "/academy", label: "Akademi" },
  { href: "/community", label: "Peta Perguruan" },
];
const GRAD = "rounded-full bg-gradient-to-r from-[#4a0d0d] via-[#7c1d1d] to-[#c2410c] hover:from-[#3a0808] hover:to-[#9a3412] text-white font-semibold shadow-sm shadow-orange-950/20 hover:shadow-md transition-all";

export async function SiteHeader() {
  const user = await getCurrentUser();
  const link = "whitespace-nowrap text-sm font-semibold text-slate-700 transition-colors hover:text-red-900";
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-4 px-5 py-3">
        <BrandLogo size={40} priority className="transition-transform duration-200 hover:scale-105" />
        <nav aria-label="Utama" className="hidden items-center gap-5 lg:gap-7 md:flex">
          {links.map((l) => <Link key={l.href} href={l.href} className={link}>{l.label}</Link>)}
        </nav>
        <div className="hidden shrink-0 items-center gap-3 md:flex">
          {user ? (
            <>
              <Link href="/app" className={link}>Dasbor</Link>
              <LogoutButton className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50" />
            </>
          ) : (
            <>
              <Link href="/masuk" className={link}>Masuk</Link>
              <Link href="/academy" className={`${GRAD} px-5 py-2.5 text-xs`}>Mulai Belajar</Link>
            </>
          )}
        </div>
        <details className="relative md:hidden">
          <summary aria-label="Buka menu" className="flex cursor-pointer list-none items-center rounded-xl border border-slate-200 bg-white p-2 hover:bg-slate-50">
            <Menu aria-hidden className="h-5 w-5 text-red-950" />
          </summary>
          <nav aria-label="Utama (seluler)" className="absolute right-0 z-10 mt-2 flex w-64 flex-col gap-1 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
            {links.map((l) => <Link key={l.href} href={l.href} className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:text-red-900">{l.label}</Link>)}
            <hr className="my-1 border-slate-200" />
            {user ? (
              <>
                <Link href="/app" className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Dasbor</Link>
                <LogoutButton className="rounded-xl px-3 py-2 text-left text-sm font-semibold text-slate-700 hover:bg-slate-50" />
              </>
            ) : (
              <>
                <Link href="/masuk" className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Masuk</Link>
                <Link href="/academy" className={`${GRAD} mt-1 py-2.5 text-center text-xs`}>Mulai Belajar</Link>
              </>
            )}
          </nav>
        </details>
      </div>
    </header>
  );
}
