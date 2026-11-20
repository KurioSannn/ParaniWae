"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { Notice } from "@/components/Notice";

export function EnrollButton({ slug, enrolled, loggedIn }: { slug: string; enrolled: boolean; loggedIn: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  if (!loggedIn) {
    return <a href={`/masuk?next=${encodeURIComponent(`/academy/courses/${slug}`)}`} className="inline-block rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900">Masuk untuk mengikuti</a>;
  }
  async function act() {
    setBusy(true);
    const r = enrolled ? await clientRequest("DELETE", `/courses/${slug}/enroll`) : await clientRequest("POST", `/courses/${slug}/enroll`);
    setBusy(false);
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    setMsg({ kind: "success", text: enrolled ? "Anda berhenti mengikuti kurikulum ini. Progres tetap tersimpan." : "Berhasil mendaftar. Selamat belajar!" });
    router.refresh();
  }
  return (
    <div>
      <button onClick={act} disabled={busy}
        className={enrolled ? "rounded-xl border border-line-200 px-5 py-3 font-medium hover:bg-parchment-100 disabled:opacity-60"
          : "rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60"}>
        {busy ? "Memproses…" : enrolled ? "Berhenti mengikuti" : "Ikuti kurikulum"}
      </button>
      <Notice kind={msg?.kind ?? null}>{msg?.text}</Notice>
    </div>
  );
}
