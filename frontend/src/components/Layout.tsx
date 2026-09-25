import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  KeyRound,
  FlaskConical,
  FileText,
  Shield,
  Network,
  ListTree,
} from "lucide-react";
import clsx from "clsx";

const LINKS = [
  { to: "/app", end: true, label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/auditor", label: "RSA Auditor", icon: KeyRound },
  { to: "/app/inventory", label: "Key Inventory", icon: ListTree },
  { to: "/app/ecm", label: "ECM Analysis", icon: Network },
  { to: "/app/lab", label: "Test Lab", icon: FlaskConical },
  { to: "/app/reports", label: "Report Center", icon: FileText },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-border/80 bg-panel/80 p-4 flex flex-col gap-6 min-h-screen">
      <div className="flex items-center gap-2">
        <div className="h-9 w-9 rounded-lg border border-cyan/40 bg-cyan/10 grid place-items-center">
          <Shield className="h-5 w-5 text-cyan" />
        </div>
        <div>
          <div className="font-[family-name:var(--font-display)] font-semibold tracking-tight">RSA-SHIELD</div>
          <div className="text-[10px] uppercase tracking-widest text-muted">Team Aegis</div>
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        {LINKS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
                isActive ? "bg-cyan/15 text-cyan border border-cyan/30" : "text-muted hover:text-text hover:bg-white/5",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto text-[11px] text-muted leading-relaxed">
        Bennett University
        <br />
        Mentor: Dr. Sachin Choudhary
        <br />
        <span className="text-amber">No absolute “SECURE” labels</span>
      </div>
    </aside>
  );
}

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="border-b border-border/70 px-6 py-4 flex items-end justify-between gap-4">
      <div>
        <h1 className="text-xl font-[family-name:var(--font-display)] font-semibold">{title}</h1>
        {subtitle ? <p className="text-sm text-muted mt-0.5">{subtitle}</p> : null}
      </div>
      <div className="text-xs mono text-muted">RSA Key Security Auditor</div>
    </header>
  );
}
