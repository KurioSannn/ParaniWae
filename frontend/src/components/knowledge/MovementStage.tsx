"use client";
import { useState } from "react";
import type { ClipMeta } from "@/lib/character";
import { Movement3DPlayer } from "@/components/knowledge/Movement3DPlayer";

/** Panggung gerak: peraga 3D (bila klip lolos pemeriksaan) dengan pilihan ilustrasi 2D. */
export function MovementStage({ clip, title, twoD }: { clip: ClipMeta | null; title: string; twoD: React.ReactNode }) {
  const [mode, setMode] = useState<"3d" | "2d">(clip ? "3d" : "2d");
  if (!clip) return <>{twoD}</>;
  const tab = (m: "3d" | "2d", label: string) => (
    <button type="button" role="tab" aria-selected={mode === m} onClick={() => setMode(m)}
      className={`rounded-lg px-3 py-1.5 text-sm ${mode === m ? "bg-forest-700 text-paper-50" : "hover:bg-parchment-100"}`}>{label}</button>
  );
  return (
    <div>
      <div role="tablist" aria-label="Jenis peraga" className="mb-2 inline-flex rounded-xl border border-line-200 bg-paper-50 p-1">
        {tab("3d", "Peraga 3D")}{tab("2d", "Ilustrasi 2D")}
      </div>
      <div role="tabpanel">{mode === "3d" ? <Movement3DPlayer clip={clip} title={title} fallback={twoD} /> : twoD}</div>
    </div>
  );
}
