"use client";
import { ErrorState } from "@/components/ui";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <ErrorState message="Terjadi kesalahan tak terduga saat memuat halaman." />
      <button onClick={reset} className="mt-4 rounded-xl border border-line-200 px-4 py-2">Coba lagi</button>
    </div>
  );
}
