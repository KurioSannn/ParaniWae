import Link from "next/link";
import { Footprints } from "lucide-react";
import type { AnimationRef, MovementItem } from "@/lib/research";
import { LEVEL_ID, SAFETY_CLASS_LABEL } from "@/lib/research";
import { AnimationPlayer } from "@/components/knowledge/AnimationPlayer";

/** Penanda asal informasi yang ringkas dan ramah pembaca. */
export function Pill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "warn" | "ok" }) {
  const cls = tone === "warn" ? "bg-bronze-500/15 text-ink-950" : tone === "ok" ? "bg-forest-700/10 text-forest-900" : "bg-line-200/70 text-slate-600";
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>{children}</span>;
}

export function SafetyPill({ cls }: { cls: string }) {
  return <Pill tone={cls === "solo_beginner" ? "ok" : "warn"}>{SAFETY_CLASS_LABEL[cls] ?? cls}</Pill>;
}

/** Visual gerakan: pemutar animasi bila tersedia; bila belum, panel ilustratif yang tenang (tanpa narasi internal). */
export function MovementVisual({ a, title, compact = false }: { a: AnimationRef; title: string; compact?: boolean }) {
  if (a.status === "generated" && a.url) return <AnimationPlayer src={a.url} title={title} compact={compact} />;
  return (
    <div className="flex aspect-[9/11] w-full flex-col items-center justify-center gap-2 rounded-xl border border-line-200 bg-parchment-100 p-4 text-center">
      <Footprints aria-hidden className="h-8 w-8 text-bronze-700" />
      <p className="font-serif text-lg text-forest-900">{title}</p>
      {!compact && <p className="text-xs text-slate-600">Ikuti uraian fase di halaman ini.</p>}
    </div>
  );
}

export function MovementCard({ m }: { m: MovementItem }) {
  return (
    <article className="group">
      <Link href={`/library/${m.slug}`} className="block" aria-label={m.name}>
        <MovementVisual a={m.animation} title={m.name} compact />
      </Link>
      <h3 className="mt-2 font-medium"><Link href={`/library/${m.slug}`} className="hover:underline">{m.name}</Link></h3>
      <p className="text-xs text-slate-600">{m.category_label} · {LEVEL_ID[m.level] ?? m.level} · {m.phases} fase</p>
    </article>
  );
}
