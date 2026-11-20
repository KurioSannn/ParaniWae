"use client";
import { CheckCircle2, Circle } from "lucide-react";
import type { Readiness } from "@/lib/types";

export const inputCls = "w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5 disabled:bg-parchment-100 disabled:text-slate-600";
export const btnPrimary = "rounded-xl bg-forest-700 px-4 py-2.5 text-sm font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60";
export const btnGhost = "rounded-xl border border-line-200 px-4 py-2.5 text-sm font-medium hover:bg-parchment-100 disabled:opacity-60";

export function Field({ id, label, hint, children, required }: { id: string; label: string; hint?: string; children: React.ReactNode; required?: boolean }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}{required && <span aria-hidden className="text-clay-600"> *</span>}</label>
      {children}
      {hint && <p className="mt-1 text-xs text-slate-600">{hint}</p>}
    </div>
  );
}

export function Section({ id, title, description, children }: { id: string; title: string; description?: string; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-6 rounded-2xl border border-line-200 bg-paper-50 p-5 sm:p-6">
      <h2 id={`${id}-h`} className="font-serif text-xl text-forest-900">{title}</h2>
      {description && <p className="mt-1 max-w-2xl text-sm text-slate-600">{description}</p>}
      <div className="mt-4 space-y-4">{children}</div>
    </section>
  );
}

export function Checklist({ items, label }: { items: Readiness[]; label: string }) {
  const done = items.filter((i) => i.ok).length;
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span aria-label={`${done} dari ${items.length} terpenuhi`} className="text-slate-600">{done}/{items.length}</span>
      </div>
      <div role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={items.length} aria-valuenow={done} className="mb-3 h-1.5 overflow-hidden rounded-full bg-line-200">
        <div className="h-full bg-forest-700" style={{ width: `${items.length ? (100 * done) / items.length : 0}%` }} />
      </div>
      <ul className="space-y-1.5 text-sm">
        {items.map((i) => (
          <li key={i.key} className="flex items-start gap-2">
            {i.ok ? <CheckCircle2 aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-forest-700" /> : <Circle aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-slate-600" />}
            <span className={i.ok ? "text-slate-600" : "text-ink-950"}>{i.label}<span className="sr-only">{i.ok ? " — terpenuhi" : " — belum terpenuhi"}</span></span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Tag bebas (dipisah koma) -> array. */
export function splitTags(s: string): string[] {
  return s.split(",").map((x) => x.trim()).filter(Boolean);
}

/** Gambar referensi dari endpoint terotorisasi (bukan aset statis, jadi `next/image` tidak relevan). */
export function RefImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} className={className} />;
}
