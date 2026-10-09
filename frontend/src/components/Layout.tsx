import { Link, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  KeyRound,
  FlaskConical,
  FileText,
  Shield,
  Network,
  ListTree,
  Plus,
  BarChart3,
  BookOpen,
} from "lucide-react";
import clsx from "clsx";

const LINKS = [
  { to: "/app", end: true, label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/auditor", label: "RSA Auditor", icon: KeyRound, badge: "v4.12" },
  { to: "/app/inventory", label: "Key Inventory", icon: ListTree },
  { to: "/app/ecm", label: "ECM Analysis", icon: Network },
  { to: "/app/lab", label: "Test Lab", icon: FlaskConical },
  { to: "/app/evaluation", label: "Evaluation", icon: BarChart3 },
  { to: "/app/research", label: "Related Work", icon: BookOpen },
  { to: "/app/reports", label: "Report Center", icon: FileText },
];

export function Sidebar() {
  return (
    <aside className="w-64 shrink-0 border-r border-border/80 bg-bg p-4 flex flex-col justify-between min-h-screen sticky top-0 h-screen">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="h-9 w-9 rounded-lg border border-border bg-surface-high grid place-items-center shadow-[0_0_12px_rgba(34,211,238,0.2)]">
            <Shield className="h-5 w-5 text-cyan" />
          </div>
          <div>
            <div className="display font-semibold tracking-tight text-primary text-lg leading-tight">RSA-SHIELD</div>
            <div className="text-[11px] mono text-muted flex items-center gap-1.5">
              Engine v4.12 · Active
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" />
            </div>
          </div>
        </div>

        <Link
          to="/app/auditor"
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-cyan text-on-primary text-xs font-semibold mono hover:brightness-110 transition shadow-[0_2px_12px_rgba(34,211,238,0.25)]"
        >
          <Plus className="h-4 w-4" />
          Ingest PEM / Keys
        </Link>

        <nav className="flex flex-col gap-1 mt-1">
          {LINKS.map(({ to, label, icon: Icon, end, badge }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm mono transition",
                  isActive
                    ? "bg-surface-high text-cyan border-l-2 border-cyan"
                    : "text-muted hover:text-text hover:bg-surface-container",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="flex-1">{label}</span>
              {badge ? (
                <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-cyan/10 text-cyan border border-cyan/20">
                  {badge}
                </span>
              ) : null}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="pt-3 border-t border-border/60 space-y-2">
        <div className="p-2.5 rounded-lg bg-surface-low border border-border/60">
          <div className="text-xs text-text font-medium">Team Aegis</div>
          <div className="text-[11px] mono text-muted mt-0.5">Bennett University</div>
          <div className="text-[10px] text-amber mt-1.5 leading-snug">No absolute “SECURE” labels</div>
        </div>
      </div>
    </aside>
  );
}

export function Topbar({
  title,
  subtitle,
  breadcrumb,
}: {
  title: string;
  subtitle?: string;
  breadcrumb?: string;
}) {
  return (
    <header className="border-b border-border/70 px-6 py-4 flex items-end justify-between gap-4 sticky top-0 z-20 bg-bg/90 backdrop-blur-md">
      <div>
        {breadcrumb ? (
          <div className="text-[11px] mono text-muted mb-1 tracking-wide">{breadcrumb}</div>
        ) : null}
        <h1 className="text-xl display font-semibold tracking-tight">{title}</h1>
        {subtitle ? <p className="text-sm text-muted mt-0.5">{subtitle}</p> : null}
      </div>
      <div className="hidden md:flex items-center gap-3 text-[11px] mono text-muted">
        <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md border border-ok/30 bg-ok/10 text-ok">
          <span className="w-1.5 h-1.5 rounded-full bg-ok" />
          Cluster online
        </span>
        <span>RSA Key Security Auditor</span>
      </div>
    </header>
  );
}
