"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { clientRequest } from "@/lib/client-api";
import { ROLE_LABEL } from "@/lib/format";
import { Notice } from "@/components/Notice";
import type { AdminUser } from "@/lib/types";

export function AdminUsers({ users, selfId }: { users: AdminUser[]; selfId: string }) {
  const router = useRouter();
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  async function patch(id: string, body: Record<string, string>) {
    const r = await clientRequest("PATCH", `/admin/users/${id}`, body);
    if (!r.ok) return setMsg({ kind: "error", text: r.error });
    setMsg({ kind: "success", text: "Perubahan disimpan; sesi pengguna tersebut dicabut." });
    router.refresh();
  }
  return (
    <>
      <Notice kind={msg?.kind ?? null}>{msg?.text}</Notice>
      <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
        <table className="w-full text-left text-sm"><caption className="sr-only">Daftar pengguna</caption>
          <thead className="border-b border-line-200 text-slate-600"><tr><th scope="col" className="px-4 py-3">Pengguna</th><th scope="col" className="px-4 py-3">Peran</th><th scope="col" className="px-4 py-3">Status</th></tr></thead>
          <tbody className="divide-y divide-line-200">{users.map((u) => (
            <tr key={u.id}><td className="px-4 py-3"><span className="font-medium">{u.display_name}</span><br /><span className="text-slate-600">{u.email}</span></td>
              <td className="px-4 py-3"><label className="sr-only" htmlFor={`r-${u.id}`}>Peran {u.display_name}</label>
                <select id={`r-${u.id}`} disabled={u.id === selfId} defaultValue={u.role} onChange={(e) => patch(u.id, { role: e.target.value })} className="rounded-lg border border-line-200 bg-paper-50 px-2 py-1">
                  {Object.entries(ROLE_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></td>
              <td className="px-4 py-3"><label className="sr-only" htmlFor={`s-${u.id}`}>Status {u.display_name}</label>
                <select id={`s-${u.id}`} disabled={u.id === selfId} defaultValue={u.status} onChange={(e) => patch(u.id, { status: e.target.value })} className="rounded-lg border border-line-200 bg-paper-50 px-2 py-1">
                  <option value="active">Aktif</option><option value="suspended">Ditangguhkan</option></select></td></tr>))}</tbody></table></div>
    </>
  );
}
