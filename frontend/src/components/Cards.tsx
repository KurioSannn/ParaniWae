import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import type { CourseSummary, PartnerSummary, TraditionSummary } from "@/lib/types";
import { formatMinutes, LEVEL_LABEL, PARTNER_TYPE_LABEL } from "@/lib/format";
import { ProvenanceBadge } from "@/components/ui";

const shell = "flex h-full flex-col gap-2 rounded-2xl border border-line-200 bg-paper-50 p-5 transition-colors hover:border-sage-500";

type Lvl = { level?: 2 | 3 };
const H = ({ level = 3, children }: { level?: 2 | 3; children: React.ReactNode }) => {
  const Tag = level === 2 ? "h2" : "h3";
  return <Tag className="font-serif text-xl text-forest-900">{children}</Tag>;
};

export function TraditionCard({ t, level }: { t: TraditionSummary } & Lvl) {
  return (
    <li><Link href={`/heritage/${t.slug}`} className={shell}>
      <ProvenanceBadge p={t.provenance} />
      <H level={level}>{t.name}</H>
      {t.region && <p className="flex items-center gap-1 text-sm text-slate-600"><MapPin aria-hidden className="h-4 w-4" />{t.region}</p>}
      {t.public_summary && <p className="line-clamp-3 text-sm text-slate-600">{t.public_summary}</p>}
    </Link></li>
  );
}

export function PartnerCard({ p, level }: { p: PartnerSummary } & Lvl) {
  return (
    <li><Link href={`/community/${p.slug}`} className={shell}>
      <ProvenanceBadge p={p.provenance} />
      <H level={level}>{p.name}</H>
      <p className="text-sm text-slate-600">{PARTNER_TYPE_LABEL[p.partner_type] ?? p.partner_type}</p>
      {p.city && <p className="flex items-center gap-1 text-sm text-slate-600"><MapPin aria-hidden className="h-4 w-4" />{p.city}</p>}
    </Link></li>
  );
}

export function CourseCard({ c, level }: { c: CourseSummary } & Lvl) {
  return (
    <li><Link href={`/academy/courses/${c.slug}`} className={shell}>
      <ProvenanceBadge p={c.provenance} />
      <H level={level}>{c.title}</H>
      {c.summary && <p className="line-clamp-2 text-sm text-slate-600">{c.summary}</p>}
      <p className="mt-auto flex flex-wrap items-center gap-x-3 pt-2 text-sm text-slate-600">
        <span>{LEVEL_LABEL[c.level] ?? c.level}</span>
        <span>{c.lesson_count} pelajaran</span>
        {formatMinutes(c.estimated_minutes) && <span className="flex items-center gap-1"><Clock aria-hidden className="h-4 w-4" />{formatMinutes(c.estimated_minutes)}</span>}
      </p>
      {c.partner_name && <p className="text-xs text-slate-600">{c.partner_name}</p>}
    </Link></li>
  );
}
