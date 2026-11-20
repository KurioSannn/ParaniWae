import Link from "next/link";
import { ArrowRight, Building2, FileText } from "lucide-react";
import { Card, EmptyState, ErrorState, PageHeader } from "@/components/ui";
import { PartnerStatusPill } from "@/components/studio/StatusPills";
import { actionLabel, formatDateTime, STATUS_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { DashboardAttention, StudioDashboard } from "@/lib/types";

export const metadata = { title: "Studio Instruktur — SILATARA" };

function attentionHref(a: DashboardAttention): string {
  if (a.partner_id) return `/app/studio/partners/${a.partner_id}`;
  return `/app/studio/movements/${a.movement_id}`;
}

export default async function StudioDashboardPage() {
  const user = await requireUser("/app/studio", ["instructor", "curator", "admin"]);
  const r = await sGet<StudioDashboard>("/studio/dashboard");
  if (!r.ok) return <ErrorState message={r.error} retryHref="/app/studio" />;
  const d = r.data;
  const byStatus = Object.entries(d.counts.documents_by_status);
  return (
    <>
      <PageHeader eyebrow="Studio Instruktur" title="Dokumentasi gerakan dan kemitraan"
        description="Tempat instruktur dan mitra mendokumentasikan gerakan dengan kata-kata sendiri, mengajukannya untuk ditinjau, lalu menerbitkannya ke Jalur Belajar. SILATARA tidak menulis isi budaya untuk Anda.">
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/app/studio/movements/new" className="rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">+ Dokumentasikan gerakan</Link>
          <Link href="/app/studio/partners/new" className="rounded-xl border border-line-200 px-5 py-2.5 font-medium hover:bg-parchment-100">+ Profil mitra</Link>
        </div>
      </PageHeader>

      <div className="grid gap-8 xl:grid-cols-[1fr_20rem]">
        <div className="space-y-8">
          <section aria-labelledby="perhatian">
            <h2 id="perhatian" className="mb-3 font-serif text-xl text-forest-900">Perlu perhatian</h2>
            {d.attention.length === 0 ? (
              <EmptyState title="Tidak ada yang menunggu Anda">Revisi, tinjauan, konfirmasi, dan penerbitan yang memerlukan tindakan Anda akan muncul di sini.</EmptyState>
            ) : (
              <ul className="divide-y divide-line-200 overflow-hidden rounded-2xl border border-line-200 bg-paper-50">
                {d.attention.map((a, i) => (
                  <li key={`${a.kind}-${a.document_id ?? a.partner_id}-${i}`}>
                    <Link href={attentionHref(a)} className="flex items-center gap-3 px-4 py-3 hover:bg-parchment-100">
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{a.title}{a.version_no ? <span className="font-normal text-slate-600"> · v{a.version_no}</span> : null}</span>
                        <span className="block text-sm text-slate-600">{a.label}{a.note ? ` — ${a.note}` : ""}</span>
                      </span>
                      <ArrowRight aria-hidden className="h-4 w-4 shrink-0 text-slate-600" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="mitra">
            <div className="mb-3 flex items-baseline justify-between"><h2 id="mitra" className="font-serif text-xl text-forest-900">Mitra</h2>
              <Link href="/app/studio/partners" className="text-sm underline">Semua mitra</Link></div>
            {d.partners.length === 0 ? (
              <EmptyState title="Belum terhubung ke mitra">Buat profil mitra (draf) atau minta penanggung jawab mitra menambahkan Anda sebagai anggota. Profil yang dibuat belum berarti mitra resmi — verifikasi dilakukan admin dengan bukti.</EmptyState>
            ) : (
              <ul className="space-y-2">{d.partners.slice(0, 6).map((p) => (
                <li key={p.id}><Link href={`/app/studio/partners/${p.id}`} className="flex flex-wrap items-center gap-3 rounded-2xl border border-line-200 bg-paper-50 px-4 py-3 hover:bg-parchment-100">
                  <Building2 aria-hidden className="h-5 w-5 text-sage-500" />
                  <span className="min-w-0 flex-1 truncate font-medium">{p.name}{p.my_role && <span className="ml-2 text-xs font-normal text-slate-600">{p.my_role === "manager" ? "penanggung jawab" : "anggota"}</span>}</span>
                  <PartnerStatusPill status={p.verification_status} demo={p.is_demo} /></Link></li>))}</ul>
            )}
          </section>

          <section aria-labelledby="tradisi">
            <h2 id="tradisi" className="mb-3 font-serif text-xl text-forest-900">Cakupan tradisi</h2>
            {d.tradition_coverage.length === 0 ? <p className="text-sm text-slate-600">Belum ada dokumentasi gerakan.</p> : (
              <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
                <table className="w-full text-left text-sm"><caption className="sr-only">Gerakan per tradisi</caption>
                  <thead className="border-b border-line-200 text-slate-600"><tr><th scope="col" className="px-4 py-3">Tradisi</th><th scope="col" className="px-4 py-3">Gerakan</th><th scope="col" className="px-4 py-3">Terbit</th></tr></thead>
                  <tbody className="divide-y divide-line-200">{d.tradition_coverage.map((c) => (
                    <tr key={c.tradition_id}><th scope="row" className="px-4 py-3 font-medium">{c.tradition_name}</th><td className="px-4 py-3">{c.total}</td><td className="px-4 py-3">{c.published}</td></tr>))}</tbody></table></div>
            )}
          </section>
        </div>

        <aside className="space-y-6" aria-label="Ringkasan">
          <Card>
            <h2 className="mb-2 flex items-center gap-2 font-semibold"><FileText aria-hidden className="h-4 w-4 text-sage-500" />Dokumentasi saya</h2>
            {byStatus.length === 0 ? <p className="text-sm text-slate-600">Belum ada.</p> : (
              <dl className="space-y-1 text-sm">{byStatus.map(([s, n]) => (
                <div key={s} className="flex justify-between"><dt className="text-slate-600">{STATUS_LABEL[s as keyof typeof STATUS_LABEL] ?? s}</dt><dd className="font-medium">{n}</dd></div>))}</dl>)}
            <p className="mt-3 text-xs text-slate-600">{d.counts.published_movements} gerakan tayang · {d.counts.lessons_linked} tautan pelajaran{d.counts.media_awaiting_consent ? ` · ${d.counts.media_awaiting_consent} media menunggu verifikasi izin` : ""}</p>
            <Link href="/app/studio/movements" className="mt-3 inline-block text-sm underline">Buka daftar gerakan</Link>
          </Card>
          <Card>
            <h2 className="mb-2 font-semibold">Aktivitas terbaru</h2>
            {d.recent_activity.length === 0 ? <p className="text-sm text-slate-600">Belum ada aktivitas.</p> : (
              <ol className="space-y-2 text-sm">{d.recent_activity.slice(0, 8).map((a, i) => (
                <li key={i}><span className="block">{actionLabel(a.action)}</span><span className="block text-xs text-slate-600">{a.actor ?? "—"} · {formatDateTime(a.created_at)}</span></li>))}</ol>)}
          </Card>
          <p className="text-xs text-slate-600">Masuk sebagai {user.display_name}. Kategori keselamatan adalah klasifikasi administratif, bukan sertifikasi keselamatan.</p>
        </aside>
      </div>
    </>
  );
}
