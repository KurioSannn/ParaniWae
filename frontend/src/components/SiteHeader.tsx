import Link from "next/link";
import { Menu } from "lucide-react";
import { getCurrentUser } from "@/lib/server-api";
import { LogoutButton } from "@/components/LogoutButton";

const links = [
  { href: "/heritage", label: "Jelajahi Warisan" },
  { href: "/academy", label: "Akademi" },
  { href: "/library", label: "Pustaka Gerakan" },
  { href: "/community", label: "Perguruan" },
];

export async function SiteHeader() {
  const user = await getCurrentUser();
  const linkCls = "rounded-lg px-3 py-2 text-ink-950 hover:bg-parchment-100";
  const nav = (
    <>
      {links.map((l) => <Link key={l.href} href={l.href} className={linkCls}>{l.label}</Link>)}
      {user ? (
        <>
          <Link href="/app" className={linkCls}>Dasbor</Link>
          <LogoutButton className={`${linkCls} text-left`} />
        </>
      ) : (
        <>
          <Link href="/masuk" className={linkCls}>Masuk</Link>
          <Link href="/daftar" className="rounded-xl bg-forest-700 px-4 py-2 font-medium text-paper-50 hover:bg-forest-900">Mulai Belajar</Link>
        </>
      )}
    </>
  );
  return (
    <header className="border-b border-line-200 bg-paper-50">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between px-5 py-3">
        <Link href="/" className="font-serif text-xl font-semibold tracking-wide text-forest-900">SILATARA</Link>
        <nav aria-label="Utama" className="hidden items-center gap-1 md:flex">{nav}</nav>
        <details className="relative md:hidden">
          <summary aria-label="Buka menu" className="flex cursor-pointer list-none items-center rounded-lg p-2 hover:bg-parchment-100">
            <Menu aria-hidden className="h-6 w-6" />
          </summary>
          <nav aria-label="Utama (seluler)" className="absolute right-0 z-10 mt-2 flex w-60 flex-col gap-1 rounded-2xl border border-line-200 bg-paper-50 p-3 shadow-sm">{nav}</nav>
        </details>
      </div>
    </header>
  );
}
