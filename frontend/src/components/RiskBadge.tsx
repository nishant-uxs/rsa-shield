import clsx from "clsx";
import type { AuditState } from "../types";

const STYLES: Record<string, string> = {
  FACTOR_FOUND: "bg-crit/15 text-crit border-crit/40",
  SUSPICIOUS: "bg-amber/15 text-amber border-amber/40",
  INCONCLUSIVE: "bg-violet/15 text-violet border-violet/40",
  NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS: "bg-ok/15 text-ok border-ok/40",
  INVALID_KEY: "bg-crit/10 text-crit border-crit/30",
};

const LABELS: Record<string, string> = {
  FACTOR_FOUND: "Factor Found",
  SUSPICIOUS: "Suspicious",
  INCONCLUSIVE: "Inconclusive",
  NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS: "No weakness by checks",
  INVALID_KEY: "Invalid key",
};

export function RiskBadge({ state }: { state?: AuditState | string | null }) {
  if (!state) return <span className="text-muted text-xs">—</span>;
  return (
    <span className={clsx("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium mono", STYLES[state] || "border-border text-muted")}>
      {LABELS[state] || state}
    </span>
  );
}
