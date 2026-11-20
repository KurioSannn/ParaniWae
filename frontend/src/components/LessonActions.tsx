"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { Notice } from "@/components/Notice";
import type { ProgressUpdate } from "@/lib/types";

export function LessonActions({ lessonId, courseSlug, enrolled, completed: initial }: {
  lessonId: string; courseSlug: string; enrolled: boolean; completed: boolean;
}) {
  const router = useRouter();
  const [completed, setCompleted] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const visited = useRef(false);

  // Catat kunjungan (untuk "lanjutkan belajar") sekali per pembukaan halaman.
  useEffect(() => {
    if (!enrolled || visited.current) return;
    visited.current = true;
    void clientRequest("PUT", `/me/lessons/${lessonId}/progress`, { status: "in_progress" });
  }, [enrolled, lessonId]);

  if (!enrolled) {
    return (
      <div className="rounded-xl border border-bronze-500/40 bg-bronze-500/10 p-4">
        <p className="mb-2">Daftar ke kurikulum ini untuk mencatat progres Anda.</p>
        <EnrollInline slug={courseSlug} />
      </div>
    );
  }
  async function toggle() {
    setBusy(true);
    const r = await clientRequest<ProgressUpdate>("PUT", `/me/lessons/${lessonId}/progress`, { status: completed ? "incomplete" : "completed" });
    setBusy(false);
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    setCompleted(!completed);
    setMsg({ kind: "success", text: completed ? "Penanda selesai dibatalkan." : `Pelajaran ditandai selesai. Progres kurikulum: ${r.data.enrollment.progress.percent}%.` });
    router.refresh();
  }
  return (
    <div>
      <button onClick={toggle} disabled={busy} aria-pressed={completed}
        className={completed ? "rounded-xl border border-forest-700 px-5 py-3 font-medium text-forest-900 hover:bg-parchment-100 disabled:opacity-60"
          : "rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60"}>
        {busy ? "Menyimpan…" : completed ? "✓ Selesai (klik untuk batalkan)" : "Tandai selesai"}
      </button>
      <Notice kind={msg?.kind ?? null}>{msg?.text}</Notice>
    </div>
  );
}

function EnrollInline({ slug }: { slug: string }) {
  const router = useRouter();
  const [err, setErr] = useState<string | null>(null);
  return (
    <>
      <button className="rounded-xl bg-forest-700 px-4 py-2 font-medium text-paper-50" onClick={async () => {
        const r = await clientRequest("POST", `/courses/${slug}/enroll`);
        if (!r.ok) setErr(r.error); else router.refresh();
      }}>Ikuti kurikulum</button>
      <Notice kind={err ? "error" : null}>{err}</Notice>
    </>
  );
}
