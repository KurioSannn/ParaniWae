import Link from "next/link";
import { FlaskConical } from "lucide-react";
import type { PracticeSession } from "@/lib/types";
import { formatDateTime, formatDuration, PRACTICE_STATUS_LABEL } from "@/lib/format";

export function SessionRow({ s }: { s: PracticeSession }) {
  return (
    <li className="rounded-2xl border border-line-200 bg-paper-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link className="font-medium underline-offset-2 hover:underline" href={`/app/practice/sessions/${s.id}`}>{s.lesson.title}</Link>
          <p className="text-sm text-slate-600">{s.lesson.course_title} · {formatDateTime(s.started_at)}</p>
          {s.lesson.is_demo && <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-600"><FlaskConical aria-hidden className="h-3 w-3" />{s.lesson.verification_label}</p>}
        </div>
        <div className="text-right text-sm">
          <p className="font-medium">{formatDuration(s.active_duration_ms)}</p>
          <p className="text-slate-600">{PRACTICE_STATUS_LABEL[s.status] ?? s.status}{s.quality_summary?.simulated ? " · simulasi" : ""}</p>
        </div>
      </div>
      <p className="mt-2 text-sm"><Link className="underline" href={`/app/courses/${s.lesson.course_slug}/lessons/${s.lesson.slug}`}>Kembali ke materi</Link></p>
    </li>
  );
}
