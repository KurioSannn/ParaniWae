"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BookOpen, Camera, ClipboardList, LayoutDashboard, LineChart, PenLine, ShieldCheck } from "lucide-react";
import type { Role } from "@/lib/types";

export function AppNav({ role }: { role: Role }) {
  const path = usePathname();
  const items = [
    { href: "/app", label: "Ringkasan", icon: LayoutDashboard, exact: true },
    { href: "/academy", label: "Jalur Belajar", icon: BookOpen },
    { href: "/app/progress", label: "Progres", icon: LineChart },
    { href: "/app/practice", label: "Latihan", icon: Activity, match: (p: string) => p === "/app/practice" || p.startsWith("/app/practice/sessions") || /\/practice$/.test(p) },
    { href: "/app/practice/camera-check", label: "Uji Kamera", icon: Camera, match: (p: string) => p.startsWith("/app/practice/camera-check") || p.startsWith("/app/practice/benchmark") },
    ...(role !== "learner" ? [{ href: "/app/studio", label: "Studio Instruktur", icon: PenLine }] : []),
    ...(role !== "learner" ? [{ href: "/app/manage", label: "Kelola Konten", icon: ClipboardList }] : []),
    ...(role === "admin" ? [{ href: "/app/admin", label: "Admin", icon: ShieldCheck }] : []),
  ];
  return (
    <nav aria-label="Aplikasi" className="flex flex-wrap gap-1 lg:flex-col">
      {items.map(({ href, label, icon: Icon, exact, match }: { href: string; label: string; icon: typeof Activity; exact?: boolean; match?: (p: string) => boolean }) => {
        const active = match ? match(path) : exact ? path === href : path.startsWith(href);
        return (
          <Link key={href} href={href} aria-current={active ? "page" : undefined}
            className={`flex shrink-0 items-center gap-2 rounded-xl px-3 py-2.5 ${active ? "bg-forest-700 text-paper-50" : "hover:bg-parchment-100"}`}>
            <Icon aria-hidden className="h-4 w-4" />{label}
          </Link>
        );
      })}
    </nav>
  );
}
