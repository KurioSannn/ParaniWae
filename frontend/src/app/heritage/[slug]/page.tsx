import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, EmptyState, ErrorState, Grid, PageHeader, SourceBox } from "@/components/ui";
import { CourseCard, PartnerCard } from "@/components/Cards";
import { PRACTICE_MODE_LABEL } from "@/lib/format";
import { sGet } from "@/lib/server-api";
import type { TraditionDetail } from "@/lib/types";

export default async function TraditionPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const r = await sGet<TraditionDetail>(`/traditions/${encodeURIComponent(slug)}`);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/heritage/${slug}`} />;
  const t = r.data;
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/heritage">Jelajahi Warisan</Link> / {t.name}</nav>
      <PageHeader eyebrow={t.region ?? "Tradisi"} title={t.name} description={t.public_summary ?? undefined} />
      <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-10">
          <section aria-labelledby="kur"><h2 id="kur" className="mb-4 font-serif text-2xl text-forest-900">Kurikulum</h2>
            {t.courses.length ? <Grid>{t.courses.map((c) => <CourseCard key={c.id} c={c} />)}</Grid>
              : <EmptyState title="Belum ada kurikulum terbit untuk tradisi ini" />}</section>
          <section aria-labelledby="ger"><h2 id="ger" className="mb-4 font-serif text-2xl text-forest-900">Referensi gerakan</h2>
            {t.movements.length ? <ul className="space-y-3">{t.movements.map((m) => (
              <li key={m.id}><Card><h3 className="font-semibold"><Link className="underline" href={`/library/${m.id}`}>{m.name_id}</Link></h3>
                <p className="text-sm text-slate-600">{PRACTICE_MODE_LABEL[m.practice_mode] ?? m.practice_mode}</p>
                <p className="mt-1 text-xs text-slate-600">{m.provenance.verification_label}</p></Card></li>))}</ul>
              : <EmptyState title="Belum ada referensi gerakan terbit" />}</section>
          <section aria-labelledby="mit"><h2 id="mit" className="mb-4 font-serif text-2xl text-forest-900">Perguruan terkait</h2>
            {t.partners.length ? <Grid>{t.partners.map((p) => <PartnerCard key={p.id} p={p} />)}</Grid>
              : <EmptyState title="Belum ada perguruan terkait yang dipublikasikan" />}</section>
        </div>
        <SourceBox p={t.provenance} />
      </div>
    </>
  );
}
