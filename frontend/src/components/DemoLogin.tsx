"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { safeNext } from "@/lib/validation";
import type { AuthPayload } from "@/lib/types";
import { Notice } from "@/components/Notice";

export type DemoAccount = { key: string; label: string; description: string; email: string };

/**
 * Login sekali klik untuk akun [DEMO]. Daftar akun diambil halaman di server (GET /auth/demo-accounts); backend
 * mengembalikan 404 di luar pengembangan sehingga panel tidak dirender. Tidak ada kata sandi di klien.
 */
export function DemoLogin({ accounts, next }: { accounts: DemoAccount[]; next?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function login(key: string) {
    setBusy(key);
    setError(null);
    const r = await clientRequest<AuthPayload>("POST", "/auth/demo-login", { key });
    if (!r.ok) {
      setBusy(null);
      setError(r.error);
      return;
    }
    router.push(safeNext(next));
    router.refresh();
  }

  return (
    <section aria-labelledby="demo-login-title" className="mt-6 rounded-2xl border border-dashed border-bronze-500 bg-parchment-100 p-4">
      <h2 id="demo-login-title" className="text-sm font-semibold text-forest-900">Masuk cepat dengan akun demo</h2>
      <p className="mt-1 text-xs text-slate-600">Khusus pengembangan &amp; presentasi. Data akun ini fiktif [DEMO].</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {accounts.map((a) => (
          <button key={a.key} type="button" onClick={() => login(a.key)} disabled={busy !== null}
            className="rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5 text-left hover:border-forest-700 disabled:opacity-60">
            <span className="block font-medium text-forest-900">{busy === a.key ? "Memproses…" : a.label}</span>
            <span className="block text-xs text-slate-600">{a.description}</span>
          </button>
        ))}
      </div>
      {error && <div className="mt-2"><Notice kind="error">{error}</Notice></div>}
    </section>
  );
}
