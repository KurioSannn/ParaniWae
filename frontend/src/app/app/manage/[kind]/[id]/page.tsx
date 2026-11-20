import Link from "next/link";
import { notFound } from "next/navigation";
import { ModulesEditor, MaterialsEditor } from "@/components/ChildEditors";
import { ManageForm } from "@/components/ManageForm";
import { TransitionPanel } from "@/components/TransitionPanel";
import { Card, ErrorState, PageHeader, StatusBadge } from "@/components/ui";
import { ACTION_LABEL, formatDate, KIND_LABEL } from "@/lib/format";
import { MANAGE_FIELDS } from "@/lib/manage-config";
import { requireUser, sGet } from "@/lib/server-api";
import type { ManageDetail } from "@/lib/types";

export default async function EditContent({ params }: { params: Promise<{ kind: string; id: string }> }) {
  const { kind, id } = await params;
  if (!MANAGE_FIELDS[kind]) notFound();
  const user = await requireUser(`/app/manage/${kind}/${id}`, ["instructor", "curator", "admin"]);
  const r = await sGet<ManageDetail>(`/manage/${kind}/${id}`);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/app/manage/${kind}/${id}`} />;
  const d = r.data;
  const title = String(d.fields.title ?? d.fields.name ?? d.fields.name_id);
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href={`/app/manage/${kind}`}>{KIND_LABEL[kind]}</Link> / {title}</nav>
      <PageHeader eyebrow={KIND_LABEL[kind]} title={title}>
        <p className="mt-3 flex items-center gap-3"><StatusBadge status={d.fields.status} />{d.fields.is_demo ? <span className="text-sm text-slate-600">[DEMO]</span> : null}</p>
        {d.fields.review_note ? <p className="mt-2 text-sm text-slate-600">Catatan review: {String(d.fields.review_note)}</p> : null}
      </PageHeader>
      <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-8">
          <Card><ManageForm key={String(d.fields.id) + d.fields.status} kind={kind} role={user.role} detail={d} /></Card>
          {kind === "courses" && <Card><ModulesEditor courseId={id} modules={d.modules ?? []} canEdit={d.can_edit} /></Card>}
          {kind === "lessons" && <Card><MaterialsEditor lessonId={id} materials={d.materials ?? []} canEdit={d.can_edit} /></Card>}
        </div>
        <div className="space-y-6">
          <Card><h2 className="mb-3 font-semibold">Alur kerja</h2>
            <TransitionPanel kind={kind} id={id} actions={d.allowed_actions} isDemo={!!d.fields.is_demo} /></Card>
          <Card><h2 className="mb-3 font-semibold">Riwayat audit</h2>
            {d.history.length === 0 ? <p className="text-sm text-slate-600">Belum ada riwayat.</p> :
              <ol className="space-y-2 text-sm">{d.history.map((h, i) => (
                <li key={i}><span className="font-medium">{ACTION_LABEL[h.action.replace("content.", "")] ?? h.action}</span> · {h.actor ?? "sistem"}<br /><span className="text-slate-600">{formatDate(h.created_at)}</span></li>))}</ol>}</Card>
        </div>
      </div>
    </>
  );
}
