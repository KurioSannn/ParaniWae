"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { ACTION_LABEL } from "@/lib/format";
import { Notice } from "@/components/Notice";

export function TransitionPanel({ kind, id, actions, isDemo }: { kind: string; id: string; actions: string[]; isDemo: boolean }) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [evidence, setEvidence] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  if (actions.length === 0) return <p className="text-sm text-slate-600">Tidak ada aksi alur kerja yang tersedia untuk Anda pada status ini.</p>;
  async function run(action: string) {
    setBusy(action);
    const body: Record<string, string> = { action };
    if (note.trim()) body.note = note.trim();
    if (evidence.trim()) body.approval_evidence_ref = evidence.trim();
    const r = await clientRequest("POST", `/manage/${kind}/${id}/transition`, body);
    setBusy(null);
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    setMsg({ kind: "success", text: `${ACTION_LABEL[action]}: berhasil.` });
    setNote("");
    router.refresh();
  }
  return (
    <div className="space-y-3">
      {actions.includes("approve") && !isDemo && (
        <div><label htmlFor="evidence" className="mb-1 block text-sm font-medium">Rujukan bukti persetujuan mitra</label>
          <input id="evidence" value={evidence} onChange={(e) => setEvidence(e.target.value)} className="w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2" placeholder="mis. surat/berita acara validasi, tanggal" />
          <p className="mt-1 text-xs text-slate-600">Wajib untuk konten non-demo. Jangan mengisi bila mitra belum benar-benar menyetujui.</p></div>)}
      <div><label htmlFor="note" className="mb-1 block text-sm font-medium">Catatan (wajib untuk menolak)</label>
        <textarea id="note" rows={2} value={note} onChange={(e) => setNote(e.target.value)} className="w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2" /></div>
      <div className="flex flex-wrap gap-2">{actions.map((a) => (
        <button key={a} disabled={!!busy} onClick={() => run(a)}
          className={`rounded-xl px-4 py-2 text-sm font-medium disabled:opacity-60 ${a === "publish" || a === "approve" || a === "submit" ? "bg-forest-700 text-paper-50 hover:bg-forest-900" : "border border-line-200 hover:bg-parchment-100"}`}>
          {busy === a ? "…" : ACTION_LABEL[a]}</button>))}</div>
      <Notice kind={msg?.kind ?? null}>{msg?.text}</Notice>
    </div>
  );
}
