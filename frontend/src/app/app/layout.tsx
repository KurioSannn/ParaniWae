import { BrandLogo } from "@/components/Brand";
import { AppNav } from "@/components/AppNav";
import { currentPath, requireUser } from "@/lib/server-api";
import { ROLE_LABEL } from "@/lib/format";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  // Proteksi di server: tanpa sesi valid -> redirect ke /masuk. (Backend tetap memeriksa tiap API.)
  const path = await currentPath();
  const user = await requireUser(path);
  // Layar studio latihan: fokus penuh, tanpa sidebar, agar area video menjadi elemen utama.
  if (/\/lessons\/[^/?]+\/practice(\?|$)/.test(path)) return <div data-focus-layout>{children}</div>;
  return (
    <div className="grid gap-8 lg:grid-cols-[14rem_1fr]">
      <aside className="min-w-0 lg:sticky lg:top-6 lg:self-start">
        <div className="mb-4 hidden lg:block"><BrandLogo size={34} /></div>
        <p className="mb-3 text-sm text-slate-600"><span className="font-medium text-ink-950">{user.display_name}</span><br />{ROLE_LABEL[user.role]}</p>
        <AppNav role={user.role} />
      </aside>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
