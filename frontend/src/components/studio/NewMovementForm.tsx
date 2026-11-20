"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { clientRequest } from "@/lib/client-api";
import { describeError } from "@/lib/studio-api";
import type { PartnerVerification, StudioMovement } from "@/lib/types";
import { btnPrimary, Field, inputCls } from "./bits";

type P = { id: string; name: string; status: PartnerVerification; traditions: { id: string; name: string }[] };

export function NewMovementForm({ partners, initialPartner }: { partners: P[]; initialPartner?: string }) {
  const router = useRouter();
  const [pid, setPid] = useState(initialPartner && partners.some((p) => p.id === initialPartner) ? initialPartner : partners[0]?.id ?? "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const partner = partners.find((p) => p.id === pid);
  if (partners.length === 0) return (
    <div className="max-w-2xl rounded-2xl border border-dashed border-line-200 bg-paper-50 p-6">
      <p className="font-semibold">Anda belum terhubung ke mitra.</p>
      <p className="mt-1 text-slate-600">Dokumentasi gerakan selalu dimiliki sebuah mitra. Buat profil mitra (draf) atau minta penanggung jawab mitra menambahkan Anda.</p>
      <Link href="/app/studio/partners/new" className="mt-3 inline-block underline">Buat profil mitra</Link>
    </div>);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true); setErr(null);
    const r = await clientRequest<StudioMovement>("POST", "/studio/movements", {
      name_id: String(f.get("name_id")).trim(), partner_id: pid, tradition_id: String(f.get("tradition_id")),
      ...(String(f.get("name_local")).trim() ? { name_local: String(f.get("name_local")).trim() } : {}),
    });
    setBusy(false);
    if (!r.ok) return setErr(describeError(r));
    router.push(`/app/studio/movements/${r.data.id}`);
  }
  return (
    <form onSubmit={submit} className="max-w-2xl space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-6">
      <Field id="partner" label="Mitra pemilik dokumentasi" required>
        <select id="partner" value={pid} onChange={(e) => setPid(e.target.value)} className={inputCls}>{partners.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
      <Field id="tradition_id" label="Tradisi" required hint={partner && partner.traditions.length === 0 ? undefined : "Hanya tradisi dalam cakupan mitra."}>
        <select id="tradition_id" name="tradition_id" required className={inputCls} key={pid}>{partner?.traditions.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select>
        {partner && partner.traditions.length === 0 && <p className="mt-1 text-sm text-clay-600">Mitra ini belum memiliki tradisi dalam cakupan. <Link className="underline" href={`/app/studio/partners/${partner.id}#tradisi`}>Tambahkan di Partner Workspace</Link>.</p>}</Field>
      <Field id="name_id" label="Nama gerakan (Bahasa Indonesia)" required><input id="name_id" name="name_id" required maxLength={200} className={inputCls} /></Field>
      <Field id="name_local" label="Nama lokal / istilah daerah" hint="Tulis persis seperti yang dipakai perguruan."><input id="name_local" name="name_local" maxLength={200} className={inputCls} /></Field>
      {partner && partner.status !== "verified" && <p className="rounded-xl bg-parchment-100 px-4 py-3 text-sm text-slate-600">Mitra ini belum terverifikasi. Anda tetap dapat menyusun dokumentasi, tetapi penerbitan ke publik baru dapat dilakukan setelah mitra terverifikasi dan dicantumkan.</p>}
      <Notice kind={err ? "error" : null}>{err}</Notice>
      <button disabled={busy || !partner?.traditions.length} className={btnPrimary}>{busy ? "Membuat…" : "Buat draf versi 1"}</button>
    </form>
  );
}
