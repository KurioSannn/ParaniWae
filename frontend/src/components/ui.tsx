import Link from "next/link";
import { AlertCircle, BadgeCheck, FlaskConical, Hourglass, Inbox, Search } from "lucide-react";
import type { ContentStatus, Page, Progress, Provenance } from "@/lib/types";
import { STATUS_LABEL } from "@/lib/format";

export function PageHeader({ eyebrow, title, description, children }: {
  eyebrow?: string; title: string; description?: string; children?: React.ReactNode;
}) {
  return (
    <header className="mb-8 max-w-3xl">
      {eyebrow && <p className="mb-2 text-sm font-medium uppercase tracking-widest text-bronze-700">{eyebrow}</p>}
      <h1 className="font-serif text-3xl leading-tight text-forest-900 sm:text-4xl">{title}</h1>
      {description && <p className="mt-3 text-lg text-slate-600">{description}</p>}
      {children}
    </header>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-line-200 bg-paper-50 p-5 ${className}`}>{children}</div>;
}

/** Penanda keabsahan konten. Tidak pernah menyiratkan persetujuan mitra tanpa bukti. */
export function ProvenanceBadge({ p }: { p: Provenance }) {
  const Icon = p.is_demo ? FlaskConical : p.partner_verified ? BadgeCheck : Hourglass;
  const tone = p.is_demo
    ? "bg-bronze-500/15 text-ink-950"
    : p.partner_verified ? "bg-forest-700/10 text-forest-900" : "bg-line-200 text-slate-600";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}>
      <Icon aria-hidden className="h-3.5 w-3.5" />
      {p.verification_label}
    </span>
  );
}

export function StatusBadge({ status }: { status: ContentStatus }) {
  const tone: Record<ContentStatus, string> = {
    draft: "bg-line-200 text-slate-600", pending_review: "bg-bronze-500/15 text-ink-950",
    needs_revision: "border border-bronze-700/40 bg-bronze-500/15 text-ink-950",
    rejected: "border border-clay-600/40 bg-clay-600/10 text-ink-950", verified: "bg-sage-500/20 text-forest-900",
    published: "bg-forest-700/10 text-forest-900", archived: "bg-line-200 text-slate-600",
  };
  return <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${tone[status]}`}>{STATUS_LABEL[status]}</span>;
}

export function SourceBox({ p }: { p: Provenance }) {
  return (
    <aside aria-label="Sumber dan verifikasi" className="rounded-xl border border-line-200 bg-parchment-100 p-4 text-sm">
      <div className="mb-2"><ProvenanceBadge p={p} /></div>
      <dl className="space-y-1 text-slate-600">
        <div><dt className="inline font-medium text-ink-950">Sumber: </dt>
          <dd className="inline">{p.source_citation ?? "Belum dicantumkan."}
            {p.source_url && <> (<a className="underline" href={p.source_url} rel="noopener noreferrer nofollow" target="_blank">tautan</a>)</>}
          </dd></div>
        {p.approved_by_name && <div><dt className="inline font-medium text-ink-950">Disetujui oleh: </dt><dd className="inline">{p.approved_by_name}</dd></div>}
      </dl>
      {!p.partner_verified && (
        <p className="mt-2 text-slate-600">Materi ini belum dinyatakan resmi oleh mitra budaya.</p>
      )}
    </aside>
  );
}

export function EmptyState({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line-200 bg-paper-50 px-6 py-12 text-center">
      <Inbox aria-hidden className="mx-auto mb-3 h-8 w-8 text-sage-500" />
      <p className="font-semibold text-forest-900">{title}</p>
      {children && <div className="mt-1 text-slate-600">{children}</div>}
    </div>
  );
}

export function ErrorState({ message, retryHref }: { message: string; retryHref?: string }) {
  return (
    <div role="alert" className="rounded-2xl border border-clay-600/30 bg-clay-600/5 px-6 py-8">
      <p className="flex items-center gap-2 font-semibold text-clay-600"><AlertCircle aria-hidden className="h-5 w-5" />Terjadi masalah</p>
      <p className="mt-1 text-slate-600">{message}</p>
      {retryHref && <Link className="mt-3 inline-block underline" href={retryHref}>Coba lagi</Link>}
    </div>
  );
}

export function ProgressBar({ progress, label }: { progress: Progress; label?: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm text-slate-600">
        <span>{label ?? "Progres"}</span>
        <span>{progress.completed}/{progress.total} pelajaran · {progress.percent}%</span>
      </div>
      <div role="progressbar" aria-valuenow={progress.percent} aria-valuemin={0} aria-valuemax={100}
        aria-label={label ?? "Progres belajar"} className="h-2.5 overflow-hidden rounded-full bg-line-200">
        <div className="h-full rounded-full bg-forest-700" style={{ width: `${progress.percent}%` }} />
      </div>
    </div>
  );
}

type Filter = { name: string; label: string; options: { value: string; label: string }[] };

/** Form pencarian/filter berbasis GET: berfungsi tanpa JavaScript dan menjaga URL dapat dibagikan. */
export function SearchForm({ action, values, filters = [], placeholder }: {
  action: string; values: Record<string, string | undefined>; filters?: Filter[]; placeholder: string;
}) {
  return (
    <form action={action} method="get" role="search" className="mb-6 flex flex-wrap items-end gap-3">
      <div className="min-w-[14rem] flex-1">
        <label htmlFor="q" className="mb-1 block text-sm font-medium">Cari</label>
        <div className="relative">
          <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />
          <input id="q" name="q" defaultValue={values.q ?? ""} placeholder={placeholder}
            className="w-full rounded-xl border border-line-200 bg-paper-50 py-2.5 pl-9 pr-3" />
        </div>
      </div>
      {filters.map((f) => (
        <div key={f.name}>
          <label htmlFor={f.name} className="mb-1 block text-sm font-medium">{f.label}</label>
          <select id={f.name} name={f.name} defaultValue={values[f.name] ?? ""}
            className="rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5">
            <option value="">Semua</option>
            {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      ))}
      <button type="submit" className="rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">Terapkan</button>
      {Object.values(values).some(Boolean) && (
        <Link href={action} className="py-2.5 text-sm underline">Atur ulang</Link>
      )}
    </form>
  );
}

export function Pagination({ page, basePath, params }: {
  page: Pick<Page<unknown>, "page" | "total_pages" | "total">; basePath: string; params: Record<string, string | undefined>;
}) {
  if (page.total_pages <= 1) return null;
  const href = (n: number) => {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v && k !== "page") sp.set(k, v);
    sp.set("page", String(n));
    return `${basePath}?${sp.toString()}`;
  };
  return (
    <nav aria-label="Halaman" className="mt-8 flex items-center justify-between gap-4 text-sm">
      {page.page > 1 ? <Link rel="prev" href={href(page.page - 1)} className="rounded-lg border border-line-200 px-3 py-2">← Sebelumnya</Link> : <span />}
      <span aria-live="polite">Halaman {page.page} dari {page.total_pages} · {page.total} hasil</span>
      {page.page < page.total_pages ? <Link rel="next" href={href(page.page + 1)} className="rounded-lg border border-line-200 px-3 py-2">Berikutnya →</Link> : <span />}
    </nav>
  );
}

export function Grid({ children }: { children: React.ReactNode }) {
  return <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{children}</ul>;
}
