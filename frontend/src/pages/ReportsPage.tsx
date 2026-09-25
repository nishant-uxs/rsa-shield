import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState, EmptyState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

export function ReportsPage() {
  const [audits, setAudits] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .listAudits()
      .then((r) => setAudits(r.items))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function generate(auditId: string) {
    setMsg(null);
    try {
      const r = await api.report(auditId);
      setMsg(`Generated ${r.report_id}`);
      const blob = new Blob([JSON.stringify(r.content, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${r.report_id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <>
      <Topbar title="Report Center" subtitle="Evidence-backed JSON audit reports" />
      <div className="p-6 space-y-4">
        {loading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}
        {msg ? <div className="text-ok text-sm">{msg}</div> : null}
        <Panel title="Completed audits">
          {audits.length === 0 && !loading ? (
            <EmptyState title="No audits" detail="Run Test Lab first." />
          ) : (
            <table className="w-full text-sm">
              <thead className="text-muted text-left">
                <tr>
                  <th className="py-2">Audit</th>
                  <th>State</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((a) => (
                  <tr key={a.audit_id} className="border-t border-border/60">
                    <td className="py-2 mono">
                      <Link className="text-cyan" to={`/app/audits/${a.audit_id}`}>{a.audit_id}</Link>
                    </td>
                    <td><RiskBadge state={a.final_state} /></td>
                    <td>
                      <button className="text-xs text-violet underline" onClick={() => generate(a.audit_id)}>
                        Generate JSON report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>
    </>
  );
}
