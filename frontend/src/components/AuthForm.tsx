"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { safeNext, validateLogin, validateRegister } from "@/lib/validation";
import type { AuthPayload } from "@/lib/types";
import { Notice } from "@/components/Notice";

type Mode = "login" | "register";
const inputCls = "w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5";

function Field({ id, label, error, help, ...rest }: {
  id: string; label: string; error?: string; help?: string;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <input id={id} name={id} className={inputCls} aria-invalid={!!error}
        aria-describedby={error ? `${id}-err` : help ? `${id}-help` : undefined} {...rest} />
      {help && !error && <p id={`${id}-help`} className="mt-1 text-xs text-slate-600">{help}</p>}
      {error && <p id={`${id}-err`} className="mt-1 text-sm text-clay-600">{error}</p>}
    </div>
  );
}

export function AuthForm({ mode, next }: { mode: Mode; next?: string }) {
  const router = useRouter();
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState<string | null>(null);
  const [needsVerify, setNeedsVerify] = useState(false);
  const [resent, setResent] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const isRegister = mode === "register";

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setServerError(null);
    const f = new FormData(e.currentTarget);
    const v = {
      email: String(f.get("email") ?? ""), password: String(f.get("password") ?? ""),
      display_name: String(f.get("display_name") ?? ""), confirm: String(f.get("confirm") ?? ""),
    };
    const errs = isRegister ? validateRegister(v) : validateLogin(v);
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy(true);
    const r = await clientRequest<AuthPayload>("POST", isRegister ? "/auth/register" : "/auth/login",
      isRegister ? { email: v.email.trim(), password: v.password, display_name: v.display_name.trim() }
        : { email: v.email.trim(), password: v.password });
    if (!r.ok) {
      setBusy(false);
      if (r.code === "VALIDATION_ERROR" && Array.isArray(r.details)) {
        const m: Record<string, string> = {};
        for (const d of r.details as { field: string; message: string }[]) m[d.field] = d.message;
        setErrors(m);
      }
      setServerError(r.error);
      setNeedsVerify(r.code === "EMAIL_NOT_VERIFIED");
      return;
    }
    if (isRegister) {
      setSent(v.email.trim());
      setBusy(false);
      return;
    }
    router.push(safeNext(next));
    router.refresh();
  }

  async function resend() {
    const email = new FormData(formRef.current!).get("email");
    const r = await clientRequest("POST", "/auth/resend-verification", { email: String(email ?? "").trim() });
    setServerError(r.ok ? null : r.error);
    setNeedsVerify(!r.ok);
    if (r.ok) setResent(true);
  }

  if (sent) {
    return (
      <div role="status" className="space-y-3">
        <h2 className="font-serif text-xl text-forest-900">Periksa email Anda</h2>
        <p>Jika <strong>{sent}</strong> dapat didaftarkan, kami telah mengirim tautan verifikasi. Tautan berlaku 48 jam dan hanya dapat dipakai sekali.</p>
        <p className="text-sm text-slate-600">Belum menerima? Periksa folder spam, lalu coba <Link className="underline" href="/masuk">masuk</Link> untuk mengirim ulang verifikasi.</p>
      </div>
    );
  }
  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="space-y-4" aria-describedby="form-status">
      {isRegister && <Field id="display_name" label="Nama tampilan" autoComplete="name" error={errors.display_name} />}
      <Field id="email" type="email" label="Email" autoComplete="email" error={errors.email} />
      <Field id="password" type="password" label="Kata sandi" error={errors.password}
        autoComplete={isRegister ? "new-password" : "current-password"}
        help={isRegister ? "Minimal 12 karakter." : undefined} />
      {isRegister && <Field id="confirm" type="password" label="Ulangi kata sandi" autoComplete="new-password" error={errors.confirm} />}
      <div id="form-status"><Notice kind={serverError ? "error" : resent ? "success" : null}>{serverError ?? (resent ? "Jika akun ini ada dan belum terverifikasi, tautan baru telah dikirim." : null)}</Notice>
        {needsVerify && <button type="button" onClick={resend} className="mt-1 text-sm underline">Kirim ulang email verifikasi</button>}</div>
      <button type="submit" disabled={busy}
        className="w-full rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60">
        {busy ? "Memproses…" : isRegister ? "Buat akun" : "Masuk"}
      </button>
      <p className="text-center text-sm text-slate-600">
        {!isRegister && <><Link className="underline" href="/lupa-sandi">Lupa kata sandi?</Link><br /></>}
        {isRegister ? <>Sudah punya akun? <Link className="underline" href="/masuk">Masuk</Link></>
          : <>Belum punya akun? <Link className="underline" href="/daftar">Daftar</Link></>}
      </p>
    </form>
  );
}
