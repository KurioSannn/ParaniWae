import Link from "next/link";
import { notFound } from "next/navigation";
import { EmptyState, PageHeader } from "@/components/ui";
import { sGet } from "@/lib/server-api";

export const metadata = { title: "Kotak surat dev", robots: { index: false } };
type Mail = { id: string; to: string; subject: string; body: string; created_at: string };

function Linkify({ text }: { text: string }) {
  return <>{text.split(/(https?:\/\/\S+)/g).map((p, i) => (/^https?:\/\//.test(p) ? <Link key={i} className="underline" href={p.replace(/^https?:\/\/[^/]+/, "")}>{p}</Link> : p))}</>;
}

export default async function Mailbox() {
  const r = await sGet<Mail[]>("/dev/mailbox");
  if (!r.ok) notFound(); // 404 di luar development
  return (
    <>
      <PageHeader eyebrow="Hanya development" title="Kotak surat dev"
        description="Email TIDAK benar-benar terkirim. Ini sink lokal untuk menguji verifikasi email dan reset kata sandi." />
      {r.data.length === 0 ? <EmptyState title="Belum ada email" /> : (
        <ul className="space-y-4">{r.data.map((m) => (
          <li key={m.id} className="rounded-2xl border border-line-200 bg-paper-50 p-5">
            <p className="text-sm text-slate-600">Kepada: {m.to}</p>
            <h2 className="font-semibold">{m.subject}</h2>
            <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-sm"><Linkify text={m.body} /></pre>
          </li>))}</ul>)}
    </>
  );
}
