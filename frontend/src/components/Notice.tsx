"use client";
import { CheckCircle2, XCircle } from "lucide-react";

/** Umpan balik sukses/gagal yang dibacakan pembaca layar (aria-live). */
export function Notice({ kind, children }: { kind: "success" | "error" | null; children?: React.ReactNode }) {
  return (
    <div aria-live="polite" role={kind === "error" ? "alert" : "status"} className="min-h-[1.5rem]">
      {kind && children && (
        <p className={`flex items-start gap-2 text-sm ${kind === "success" ? "text-forest-700" : "text-clay-600"}`}>
          {kind === "success" ? <CheckCircle2 aria-hidden className="mt-0.5 h-4 w-4 shrink-0" /> : <XCircle aria-hidden className="mt-0.5 h-4 w-4 shrink-0" />}
          <span>{children}</span>
        </p>
      )}
    </div>
  );
}
