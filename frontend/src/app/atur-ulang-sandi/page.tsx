import { ResetPassword } from "@/components/AuthFlows";
import { Card, PageHeader } from "@/components/ui";

export const metadata = { title: "Atur ulang kata sandi", robots: { index: false } };

export default async function Page({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  return (
    <div className="mx-auto max-w-md">
      <PageHeader title="Atur ulang kata sandi" description="Buat kata sandi baru. Semua sesi login lama akan dikeluarkan." />
      <Card><ResetPassword token={token ?? null} /></Card>
    </div>
  );
}
