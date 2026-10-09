import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Play, ShieldAlert } from "lucide-react";
import { api } from "../api";
import type { AuditRecord, FixtureInfo } from "../types";
import { Topbar } from "../components/Layout";
import { LoadingState, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

export function LabPage() {
  const nav = useNavigate();
  const [fixtures, setFixtures] = useState<FixtureInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [last, setLast] = useState<AuditRecord | null>(null);

  useEffect(() => {
    api
      .fixtures()
      .then((r) => setFixtures(r.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function run(id: string) {
    setBusyId(id);
    setError(null);
    try {
      const audit = await api.runFixture(id, id === "normal-demo" ? 3000 : 12000);
      setLast(audit);
      nav(`/app/audits/${audit.audit_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <Topbar
        title="Attack & Test Lab"
        subtitle="Evaluate attack surfaces against synthetic fixtures in a local sandbox"
        breadcrumb="Cryptanalysis Engine / Test Lab / Fixtures"
      />
      <div className="p-6 space-y-4">
        <div className="rounded-xl border border-violet/40 bg-violet/10 px-4 py-3 flex gap-3 items-start">
          <ShieldAlert className="h-5 w-5 text-violet shrink-0 mt-0.5" />
          <div>
            <div className="mono text-xs text-violet font-semibold uppercase tracking-wide">
              Controlled educational fixtures only — sandbox
            </div>
            <p className="text-sm text-muted mt-1 leading-relaxed">
              Never targets external systems or live PKI. All modular arithmetic runs locally. Fixture suite is for
              demonstration of evidence tiers, not production key hunting.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-4 mono text-[11px] text-muted">
          <span className="px-2 py-1 rounded border border-border/60 bg-surface-low">
            {fixtures.length || "—"} fixtures loaded
          </span>
          <span className="px-2 py-1 rounded border border-ok/30 bg-ok/10 text-ok">0 external network calls</span>
          <span className="px-2 py-1 rounded border border-border/60 bg-surface-low">Air-gapped demo runtime</span>
        </div>

        {loading ? <LoadingState label="Loading fixtures…" /> : null}
        {error ? <ErrorState message={error} /> : null}

        <div className="grid md:grid-cols-2 gap-4">
          {fixtures.map((f) => (
            <section key={f.id} className="glass rounded-xl p-5 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-violet to-transparent" />
              <h3 className="display font-semibold text-base mb-2">{f.name}</h3>
              <p className="text-sm text-muted mb-3 leading-relaxed">{f.description}</p>
              <div className="text-xs mono text-violet mb-4 rounded-lg border border-violet/30 bg-violet/5 px-3 py-2">
                Expected: {f.expected_hint}
              </div>
              <button
                disabled={!!busyId}
                onClick={() => run(f.id)}
                className="inline-flex items-center gap-2 rounded-lg bg-violet/20 border border-violet/50 text-violet px-3 py-2 text-sm font-medium disabled:opacity-50 hover:bg-violet/30 transition"
              >
                <Play className="h-3.5 w-3.5" />
                {busyId === f.id ? "Running…" : "Run fixture audit"}
              </button>
            </section>
          ))}
        </div>

        {last ? (
          <div className="text-sm text-muted flex items-center gap-2 flex-wrap">
            Last run:{" "}
            <Link className="text-cyan mono" to={`/app/audits/${last.audit_id}`}>
              {last.audit_id}
            </Link>
            <RiskBadge state={last.final_state} />
          </div>
        ) : null}
      </div>
    </>
  );
}
