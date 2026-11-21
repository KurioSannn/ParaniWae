"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Notice";
import { btnPrimary, Field, inputCls } from "@/components/studio/bits";
import { clientRequest } from "@/lib/client-api";
import { describeError } from "@/lib/studio-api";
import type { SurveyOut } from "@/lib/types";

export function SurveyForm({ survey }: { survey: SurveyOut }) {
  const router = useRouter();
  const [a, setA] = useState<Record<string, string | number>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr(null);
    const r = await clientRequest("POST", `/pilot/surveys/${survey.id}/responses`, { answers: a });
    setBusy(false);
    if (!r.ok) return setErr(describeError(r));
    router.push("/app/pilot");
  }
  return (
    <form onSubmit={submit} className="max-w-2xl space-y-6">
      <p role="note" className="rounded-xl border border-line-200 bg-parchment-100 px-4 py-3 text-sm text-slate-600">{survey.instrument_note} Jawaban Anda dilaporkan secara agregat; kelompok kecil tidak ditampilkan.</p>
      {survey.questions.map((q, i) => (
        <fieldset key={q.id} className="space-y-2"><legend className="font-medium">{i + 1}. {q.text}{q.required && <span aria-hidden className="text-clay-600"> *</span>}</legend>
          {q.type === "single_choice" && q.options?.map((o) => (
            <label key={o} className="flex items-center gap-2"><input type="radio" name={q.id} value={o} required={q.required} checked={a[q.id] === o} onChange={() => setA({ ...a, [q.id]: o })} />{o}</label>))}
          {q.type === "rating" && (
            <div className="flex flex-wrap items-center gap-3">{q.min_label && <span className="text-sm text-slate-600">{q.min_label}</span>}
              {Array.from({ length: (q.scale_max ?? 5) - (q.scale_min ?? 1) + 1 }, (_, k) => (q.scale_min ?? 1) + k).map((n) => (
                <label key={n} className="flex flex-col items-center gap-1 text-sm"><input type="radio" name={q.id} value={n} required={q.required} checked={a[q.id] === n} onChange={() => setA({ ...a, [q.id]: n })} />{n}</label>))}
              {q.max_label && <span className="text-sm text-slate-600">{q.max_label}</span>}</div>)}
          {q.type === "open_text" && <Field id={`q-${q.id}`} label="Jawaban"><textarea id={`q-${q.id}`} rows={3} maxLength={2000} value={String(a[q.id] ?? "")} onChange={(e) => setA({ ...a, [q.id]: e.target.value })} className={inputCls} /></Field>}
        </fieldset>))}
      <Notice kind={err ? "error" : null}>{err}</Notice>
      <button disabled={busy} className={btnPrimary}>{busy ? "Mengirim…" : "Kirim jawaban"}</button>
    </form>
  );
}
