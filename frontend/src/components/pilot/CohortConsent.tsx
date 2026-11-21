"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { clientRequest } from "@/lib/client-api";

export function CohortConsent({ programId, cohortId, initial, policy }: { programId: string; cohortId: string; initial: { research_aggregate: boolean; publication_quote: boolean }; policy: string }) {
  const router = useRouter();
  const [c, setC] = useState(initial);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  async function toggle(k: "research_aggregate" | "publication_quote", v: boolean) {
    const r = await clientRequest<typeof c>("PUT", `/pilot/me/programs/${programId}/consents`, { [k]: v });
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    setC(r.data); setMsg({ kind: "success", text: "Pilihan Anda disimpan." });
  }
  async function leave() {
    if (!window.confirm("Keluar dari cohort ini? Progres belajar tetap tersimpan di akun Anda.")) return;
    const r = await clientRequest("DELETE", `/pilot/me/cohorts/${cohortId}`);
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    router.push("/app/pilot");
  }
  return (
    <div className="space-y-4 rounded-2xl border border-line-200 bg-paper-50 p-5 text-sm">
      <h2 className="font-semibold">Data dan privasi Anda</h2>
      <p className="text-slate-600"><strong className="text-ink-950">Wajib untuk ikut:</strong> data operasional program (keikutsertaan, progres pelajaran, metadata sesi Practice Studio, jawaban survei). Video dan data biometrik tidak pernah dikumpulkan.</p>
      <fieldset className="space-y-2"><legend className="font-medium">Opsional (dapat dicabut kapan saja)</legend>
        <label className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={c.research_aggregate} onChange={(e) => toggle("research_aggregate", e.target.checked)} /><span>Data saya boleh masuk ke laporan agregat untuk penelitian.</span></label>
        <label className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={c.publication_quote} onChange={(e) => toggle("publication_quote", e.target.checked)} /><span>Kutipan jawaban terbuka saya boleh dipublikasikan tanpa nama.</span></label></fieldset>
      <p className="text-xs text-slate-600">Kebijakan versi {policy}. Setelah program selesai dan masa retensi berakhir, jawaban survei dianonimkan dan catatan instruktur dihapus.</p>
      <Notice kind={msg?.kind ?? null}>{msg?.text}</Notice>
      <button onClick={leave} className="text-clay-600 underline">Keluar dari cohort</button>
    </div>
  );
}
