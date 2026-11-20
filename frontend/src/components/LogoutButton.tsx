"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { clientRequest } from "@/lib/client-api";

export function LogoutButton({ className = "" }: { className?: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  return (
    <button type="button" disabled={busy} className={className}
      onClick={async () => {
        setBusy(true);
        await clientRequest("POST", "/auth/logout");
        router.push("/");
        router.refresh();
      }}>
      {busy ? "Keluar…" : "Keluar"}
    </button>
  );
}
