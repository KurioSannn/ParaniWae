"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { btnPrimary } from "@/components/studio/bits";
import { clientRequest } from "@/lib/client-api";
import { formatDate, INVITE_STATUS_LABEL } from "@/lib/format";
import { describeError } from "@/lib/studio-api";
import type { InvitePreview } from "@/lib/types";

export function InvitationAccept({ token, preview, loggedIn }: { token: string; preview: InvitePreview; loggedIn: boolean }) {
  const router = useRouter();
  const [ack, setAck] = useState(false);
  const [research, setResearch] = useState(false);
  const [quote, setQuote] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const next = `/undangan?token=${encodeURIComponent(token)}`;
  async function accept() {
    setBusy(true); setErr(null);
    const r = await clientRequest<{ cohort_id: string }>("POST", "/pilot/invitations/accept", { token, operational_ack: ack, research_aggregate: research, publication_quote: quote });
    setBusy(false);
    if (!r.ok) return setErr(describeError(r));
    router.push(`/app/pilot/cohorts/${r.data.cohort_id}`);
  }
  return (
    <div className="space-y-5 rounded-2xl border border-line-200 bg-paper-50 p-6">
      <p className="text-xs uppercase tracking-widest text-bronze-700">{preview.is_demo ? "[DEMO] " : ""}Undangan program pilot</p>
      <h1 className="font-serif text-3xl text-forest-900">{preview.program_name}</h1>
      <p className="text-slate-600">Cohort <strong className="text-ink-950">{preview.cohort_name}</strong> · {preview.partner_name} · {formatDate(preview.start_date)} – {formatDate(preview.end_date)}</p>
      <p className="text-sm">Status undangan: <strong>{INVITE_STATUS_LABEL[preview.status]}</strong> · berlaku sampai {formatDate(preview.expires_at)} · program: {preview.program_status_label}.{preview.email_bound ? " Undangan ini ditujukan ke satu alamat email." : ""}</p>
      {!preview.joinable ? <p role="alert" className="rounded-xl border border-clay-600/30 bg-clay-600/5 px-4 py-3 text-sm">Undangan ini tidak dapat dipakai saat ini ({INVITE_STATUS_LABEL[preview.status].toLowerCase()}{preview.status === "pending" ? ", cohort belum dibuka atau program belum aktif" : ""}). Hubungi pengundang.</p>
        : !loggedIn ? (
          <div className="space-y-2"><p className="text-sm">Masuk atau daftar akun pelajar terlebih dahulu, lalu Anda kembali ke halaman ini.</p>
            <div className="flex gap-3"><Link className={btnPrimary} href={`/masuk?next=${encodeURIComponent(next)}`}>Masuk</Link><Link className="rounded-xl border border-line-200 px-4 py-2.5 text-sm font-medium" href="/daftar">Daftar</Link></div></div>
        ) : (
          <div className="space-y-4">
            <fieldset className="space-y-2 text-sm"><legend className="font-medium">Data dan privasi</legend>
              <label className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={ack} onChange={(e) => setAck(e.target.checked)} /><span><strong>Wajib:</strong> saya memahami program ini memakai data operasional (keikutsertaan, progres pelajaran, metadata sesi Practice Studio, jawaban survei). Video dan data biometrik tidak dikumpulkan.</span></label>
              <label className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={research} onChange={(e) => setResearch(e.target.checked)} /><span>Opsional: data saya boleh masuk laporan agregat untuk penelitian.</span></label>
              <label className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={quote} onChange={(e) => setQuote(e.target.checked)} /><span>Opsional: kutipan jawaban terbuka saya boleh dipublikasikan tanpa nama.</span></label></fieldset>
            <Notice kind={err ? "error" : null}>{err}</Notice>
            <button disabled={!ack || busy} onClick={accept} className={btnPrimary}>{busy ? "Bergabung…" : "Terima undangan dan bergabung"}</button>
          </div>)}
    </div>
  );
}
