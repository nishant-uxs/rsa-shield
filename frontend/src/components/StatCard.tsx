import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  accent = "cyan",
}: {
  label: string;
  value: string | number;
  hint?: string;
  accent?: "cyan" | "violet" | "amber" | "crit" | "ok";
}) {
  const ring =
    accent === "cyan"
      ? "border-cyan/30"
      : accent === "violet"
        ? "border-violet/30"
        : accent === "amber"
          ? "border-amber/30"
          : accent === "crit"
            ? "border-crit/30"
            : "border-ok/30";
  const stripe =
    accent === "cyan"
      ? "via-cyan"
      : accent === "violet"
        ? "via-violet"
        : accent === "amber"
          ? "via-amber"
          : accent === "crit"
            ? "via-crit"
            : "via-ok";
  return (
    <div className={`glass rounded-xl p-4 border ${ring} relative overflow-hidden`}>
      <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent ${stripe} to-transparent`} />
      <div className="text-[11px] uppercase tracking-wider text-muted mb-2 mono">{label}</div>
      <div className="text-2xl font-semibold display">{value}</div>
      {hint ? <div className="text-xs text-muted mt-1">{hint}</div> : null}
    </div>
  );
}

export function Panel({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="glass rounded-xl p-4 md:p-5 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan/40 to-transparent" />
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="text-xs font-semibold tracking-wide text-cyan uppercase mono">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border p-8 text-center">
      <div className="text-text font-medium mb-1 display">{title}</div>
      <div className="text-sm text-muted">{detail}</div>
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <div className="text-sm text-muted animate-pulse py-8 text-center mono">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-crit/40 bg-crit/10 p-4 text-sm text-crit">{message}</div>
  );
}
