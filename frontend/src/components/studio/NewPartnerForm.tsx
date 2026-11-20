"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { clientRequest } from "@/lib/client-api";
import { PARTNER_TYPE_LABEL } from "@/lib/format";
import { describeError } from "@/lib/studio-api";
import type { StudioPartnerDetail } from "@/lib/types";
import { btnPrimary, Field, inputCls } from "./bits";

export function NewPartnerForm() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const body: Record<string, string> = {};
    for (const [k, v] of f.entries()) if (String(v).trim()) body[k] = String(v).trim();
    setBusy(true);
    setErr(null);
    const r = await clientRequest<StudioPartnerDetail>("POST", "/studio/partners", body);
    setBusy(false);
    if (!r.ok) return setErr(describeError(r));
    router.push(`/app/studio/partners/${r.data.id}`);
  }
  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-6">
      <Field id="name" label="Nama organisasi" required><input id="name" name="name" required maxLength={200} className={inputCls} /></Field>
      <Field id="partner_type" label="Jenis" required>
        <select id="partner_type" name="partner_type" required defaultValue="school" className={inputCls}>
          {Object.entries(PARTNER_TYPE_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="region" label="Wilayah"><input id="region" name="region" maxLength={120} className={inputCls} /></Field>
        <Field id="city" label="Kota"><input id="city" name="city" maxLength={120} className={inputCls} /></Field>
      </div>
      <Field id="official_description" label="Deskripsi resmi organisasi" hint="Ditulis oleh organisasi sendiri.">
        <textarea id="official_description" name="official_description" rows={4} className={inputCls} /></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="responsible_name" label="Penanggung jawab"><input id="responsible_name" name="responsible_name" className={inputCls} /></Field>
        <Field id="responsible_role" label="Peran penanggung jawab"><input id="responsible_role" name="responsible_role" className={inputCls} /></Field>
        <Field id="contact_email" label="Email kontak resmi"><input id="contact_email" name="contact_email" type="email" className={inputCls} /></Field>
        <Field id="contact_phone" label="Telepon"><input id="contact_phone" name="contact_phone" className={inputCls} /></Field>
      </div>
      <p className="text-sm text-slate-600">Anda otomatis menjadi penanggung jawab (manager) profil ini. Anggota, tradisi, dan dokumen dapat ditambahkan setelah profil dibuat.</p>
      <Notice kind={err ? "error" : null}>{err}</Notice>
      <button disabled={busy} className={btnPrimary}>{busy ? "Menyimpan…" : "Simpan sebagai draf"}</button>
    </form>
  );
}
