import { InvitationAccept } from "@/components/pilot/InvitationAccept";
import { BrandLogo } from "@/components/Brand";
import { ErrorState } from "@/components/ui";
import { apiGet, qs } from "@/lib/api";
import { getCurrentUser } from "@/lib/server-api";
import type { InvitePreview } from "@/lib/types";

export const metadata = { title: "Undangan program pilot", robots: { index: false, follow: false } };

export default async function InvitationPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  if (!token) return <ErrorState message="Tautan undangan tidak lengkap." />;
  const [prev, user] = await Promise.all([apiGet<InvitePreview>(`/pilot/invitations/preview${qs({ token })}`), getCurrentUser()]);
  return (
    <div className="mx-auto max-w-lg">
      <div className="mb-6"><BrandLogo size={44} /></div>
      {!prev.ok ? <ErrorState message={prev.status === 404 ? "Undangan tidak ditemukan atau tidak valid." : prev.error} /> : <InvitationAccept token={token} preview={prev.data} loggedIn={!!user} />}
    </div>
  );
}
