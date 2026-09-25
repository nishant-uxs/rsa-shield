import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord, FixtureInfo } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState } from "../components/StatCard";
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
        title="Attack / Test Lab"
        subtitle="Controlled educational fixtures only — never targets external systems"
      />
      <div className="p-6 space-y-4">
        {loading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}
        <div className="grid md:grid-cols-2 gap-4">
          {fixtures.map((f) => (
            <Panel key={f.id} title={f.name}>
              <p className="text-sm text-muted mb-3 leading-relaxed">{f.description}</p>
              <div className="text-xs mono text-violet mb-3">Expected demo path: {f.expected_hint}</div>
              <button
                disabled={!!busyId}
                onClick={() => run(f.id)}
                className="rounded-lg bg-violet/20 border border-violet/40 text-violet px-3 py-2 text-sm font-medium disabled:opacity-50"
              >
                {busyId === f.id ? "Running…" : "Run fixture audit"}
              </button>
            </Panel>
          ))}
        </div>
        {last ? (
          <div className="text-sm text-muted">
            Last run: <Link className="text-cyan mono" to={`/app/audits/${last.audit_id}`}>{last.audit_id}</Link>{" "}
            <RiskBadge state={last.final_state} />
          </div>
        ) : null}
      </div>
    </>
  );
}
