"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { btnPrimary, Field, inputCls } from "@/components/studio/bits";
import { clientRequest } from "@/lib/client-api";
import { describeError } from "@/lib/studio-api";
import type { ProgramDetail } from "@/lib/types";

export function NewProgramForm({ partners }: { partners: { id: string; name: string; verified: boolean }[] }) {
  const router = useRouter();
  const [pid, setPid] = useState(partners[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (partners.length === 0) return <p className="max-w-xl rounded-2xl border border-dashed border-line-200 bg-paper-50 p-6">Anda belum terhubung ke mitra. Buat profil mitra di Studio Instruktur terlebih dahulu.</p>;
  const partner = partners.find((p) => p.id === pid);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body: Record<string, unknown> = { partner_id: pid };
    for (const k of ["name", "objective", "description", "start_date", "end_date"]) { const v = String(f.get(k) ?? "").trim(); if (v) body[k] = v; }
    body.capacity = Number(f.get("capacity") || 30);
    setBusy(true); setErr(null);
    const r = await clientRequest<ProgramDetail>("POST", "/pilot/programs", body);
    setBusy(false);
    if (!r.ok) return setErr(describeError(r));
    router.push(`/app/pilot/manage/${r.data.id}`);
  }
  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-6">
      <Field id="partner" label="Perguruan penyelenggara" required><select id="partner" value={pid} onChange={(e) => setPid(e.target.value)} className={inputCls}>{partners.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
      {partner && !partner.verified && <p className="rounded-xl bg-parchment-100 px-4 py-3 text-sm text-slate-600">Mitra ini belum terverifikasi: program hanya dapat disimpan sebagai draf dan tidak dapat diajukan.</p>}
      <Field id="name" label="Nama program" required><input id="name" name="name" required maxLength={200} className={inputCls} /></Field>
      <Field id="objective" label="Tujuan"><textarea id="objective" name="objective" rows={3} className={inputCls} /></Field>
      <Field id="description" label="Deskripsi"><textarea id="description" name="description" rows={3} className={inputCls} /></Field>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field id="start_date" label="Mulai"><input id="start_date" name="start_date" type="date" className={inputCls} /></Field>
        <Field id="end_date" label="Selesai"><input id="end_date" name="end_date" type="date" className={inputCls} /></Field>
        <Field id="capacity" label="Kapasitas peserta"><input id="capacity" name="capacity" type="number" min={1} max={5000} defaultValue={30} className={inputCls} /></Field>
      </div>
      <Notice kind={err ? "error" : null}>{err}</Notice>
      <button disabled={busy} className={btnPrimary}>{busy ? "Menyimpan…" : "Simpan sebagai draf"}</button>
    </form>
  );
}
