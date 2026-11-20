import { PARTNER_STATUS_LABEL } from "@/lib/format";
import type { PartnerVerification } from "@/lib/types";

const TONE: Record<PartnerVerification, string> = {
  draft: "bg-line-200 text-slate-600", pending_verification: "bg-bronze-500/15 text-ink-950",
  verified: "bg-forest-700/10 text-forest-900", rejected: "border border-clay-600/40 bg-clay-600/10 text-ink-950",
  suspended: "border border-clay-600/40 bg-clay-600/10 text-ink-950",
};
export function PartnerStatusPill({ status, demo }: { status: PartnerVerification; demo?: boolean }) {
  return <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${TONE[status]}`}>{demo ? "[DEMO] " : ""}{PARTNER_STATUS_LABEL[status]}</span>;
}
