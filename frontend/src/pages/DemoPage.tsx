import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, Play, Presentation, FlaskConical, BarChart3 } from "lucide-react";
import { api } from "../api";
import { Topbar } from "../components/Layout";
import { ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";
import type { AuditRecord } from "../types";

const SCRIPT = [
  {
    id: "weak-ecm",
    title: "1. Weak ECM key → FACTOR_FOUND",
    expect: "FACTOR_FOUND (ECM / Pollard)",
    why: "Sir ko dikhao: intentionally weak modulus pe factor milta hai.",
  },
  {
    id: "fermat-close",
    title: "2. Close primes → FACTOR_FOUND",
    expect: "FACTOR_FOUND (Fermat)",
    why: "Near-twin primes: classical Fermat probe recovers the factor.",
  },
  {
    id: "wiener-small-d",
    title: "3. Small private exponent → FACTOR_FOUND",
    expect: "FACTOR_FOUND (Wiener)",
    why: "Wiener attack path on small-d fixture.",
  },
  {
    id: "normal-demo",
    title: "4. Normal demo key → NOT SECURE",
    expect: "INCONCLUSIVE / NO_WEAKNESS… (never SECURE)",
    why: "Sabse important: factor na milna ≠ secure certificate.",
  },
];

const HEADLINES = [
  { label: "Bake-off overconfidence", us: "0.0", them: "badkeys 0.75" },
  { label: "ROCA FP (legacy → calibrated)", us: "75% → 0.2%", them: "n=500 vs badkeys" },
  { label: "Adaptive speedup", us: "1.511×", them: "recall still 1.0" },
  { label: "CT tip moduli", us: "12,010", them: "0 shared-factor hits" },
];

export function DemoPage() {
  const nav = useNavigate();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [last, setLast] = useState<AuditRecord | null>(null);
  const [done, setDone] = useState<Record<string, string>>({});

  async function run(id: string) {
    setBusy(id);
    setError(null);
    try {
      const audit = await api.runFixture(id, id === "normal-demo" ? 3000 : 12000);
      setLast(audit);
      setDone((d) => ({ ...d, [id]: audit.final_state ?? "UNKNOWN" }));
      nav(`/app/audits/${audit.audit_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <Topbar
        title="Sir Demo — Guided Test"
        subtitle="4-click script: weak keys factor, normal key never labeled SECURE"
        breadcrumb="Cryptanalysis Engine / Sir Demo"
      />
      <div className="p-6 space-y-5 max-w-5xl">
        <div className="rounded-xl border border-cyan/40 bg-cyan/10 px-4 py-3 text-sm leading-relaxed">
          <div className="font-semibold text-cyan mono text-xs uppercase tracking-wide mb-1">
            Faculty walkthrough (~3 min)
          </div>
          Run steps 1→4 in order. After each run, open the audit detail page and point at the evidence
          timeline. Emphasize: <span className="text-amber font-medium">never SECURE</span>.
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {HEADLINES.map((h) => (
            <div key={h.label} className="rounded-xl border border-border/60 bg-surface-low/50 p-3">
              <div className="text-[11px] mono text-muted uppercase tracking-wide">{h.label}</div>
              <div className="display text-lg font-semibold text-cyan mt-1">{h.us}</div>
              <div className="text-xs text-muted mt-0.5">{h.them}</div>
            </div>
          ))}
        </div>

        {error ? <ErrorState message={error} /> : null}

        <div className="space-y-3">
          {SCRIPT.map((s) => (
            <section
              key={s.id}
              className="rounded-xl border border-border/60 bg-surface-low/40 p-4 flex flex-col sm:flex-row sm:items-center gap-3"
            >
              <div className="flex-1 min-w-0">
                <div className="display font-semibold text-sm flex items-center gap-2">
                  {done[s.id] ? <CheckCircle2 className="h-4 w-4 text-ok shrink-0" /> : null}
                  {s.title}
                </div>
                <div className="text-xs mono text-violet mt-1">Expect: {s.expect}</div>
                <p className="text-sm text-muted mt-1">{s.why}</p>
                {done[s.id] ? (
                  <div className="mt-2">
                    <RiskBadge state={done[s.id]} />
                  </div>
                ) : null}
              </div>
              <button
                type="button"
                disabled={!!busy}
                onClick={() => run(s.id)}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan/20 border border-cyan/50 text-cyan px-4 py-2 text-sm font-medium disabled:opacity-50 hover:bg-cyan/30 transition shrink-0"
              >
                <Play className="h-3.5 w-3.5" />
                {busy === s.id ? "Running…" : "Run"}
              </button>
            </section>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 text-sm">
          <Link
            to="/app/evaluation"
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-muted hover:text-cyan hover:border-cyan/40"
          >
            <BarChart3 className="h-4 w-4" /> Research Evaluation tables
          </Link>
          <Link
            to="/app/lab"
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-muted hover:text-cyan hover:border-cyan/40"
          >
            <FlaskConical className="h-4 w-4" /> Full Test Lab
          </Link>
          <Link
            to="/app/research"
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-muted hover:text-cyan hover:border-cyan/40"
          >
            <Presentation className="h-4 w-4" /> Related work framing
          </Link>
        </div>

        {last ? (
          <p className="text-sm text-muted">
            Last audit:{" "}
            <Link className="text-cyan mono" to={`/app/audits/${last.audit_id}`}>
              {last.audit_id}
            </Link>
          </p>
        ) : null}
      </div>
    </>
  );
}
