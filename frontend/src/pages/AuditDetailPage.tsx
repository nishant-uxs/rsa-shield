import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

export function AuditDetailPage() {
  const { auditId } = useParams();
  const [audit, setAudit] = useState<AuditRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportMsg, setReportMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!auditId) return;
    api
      .getAudit(auditId)
      .then(setAudit)
      .catch((e) => setError(e.message));
  }, [auditId]);

  async function genReport() {
    if (!auditId) return;
    try {
      const r = await api.report(auditId);
      setReportMsg(`Report ${r.report_id} generated.`);
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

  if (!audit && !error) {
    return (
      <>
        <Topbar title="Audit Details" />
        <div className="p-6"><LoadingState /></div>
      </>
    );
  }

  return (
    <>
      <Topbar title="Audit Details" subtitle={audit?.audit_id} />
      <div className="p-6 space-y-4">
        {error ? <ErrorState message={error} /> : null}
        {audit ? (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <RiskBadge state={audit.final_state} />
              <span className="text-sm text-muted mono">{audit.status}</span>
              <button onClick={genReport} className="ml-auto rounded-lg border border-cyan/40 text-cyan px-3 py-1.5 text-sm">
                Generate report
              </button>
              <Link to="/app/lab" className="text-sm text-violet">Back to Test Lab</Link>
            </div>
            {reportMsg ? <div className="text-ok text-sm">{reportMsg}</div> : null}

            <div className="grid lg:grid-cols-2 gap-4">
              <Panel title="Key information">
                <dl className="text-sm space-y-2">
                  <div><dt className="text-muted inline">Key ID: </dt><dd className="inline mono">{audit.key_id}</dd></div>
                  <div><dt className="text-muted inline">Label: </dt><dd className="inline">{audit.key_label}</dd></div>
                  <div><dt className="text-muted inline">Size: </dt><dd className="inline mono">{audit.bit_length}-bit</dd></div>
                  <div><dt className="text-muted inline">Exponent: </dt><dd className="inline mono">e = {audit.exponent}</dd></div>
                </dl>
              </Panel>
              <Panel title="ECM execution">
                <pre className="text-xs mono text-muted whitespace-pre-wrap">{JSON.stringify(audit.ecm || audit.ecm_config, null, 2)}</pre>
                {audit.factor_found ? (
                  <div className="mt-2 text-crit text-sm">Factor hex: <span className="mono break-all">{audit.factor_hex}</span></div>
                ) : (
                  <div className="mt-2 text-amber text-xs">No factor discovered within budget — inconclusive, not secure.</div>
                )}
              </Panel>
            </div>

            <Panel title="Deterministic checks">
              <ul className="space-y-2 text-sm">
                {audit.checks.map((f, i) => (
                  <li key={i} className="border-b border-border/40 pb-2">
                    <div className="font-medium">{f.title}</div>
                    <div className="text-muted text-xs">{f.detail}</div>
                  </li>
                ))}
              </ul>
            </Panel>

            <Panel title="Heuristic warnings">
              {audit.warnings.length === 0 ? (
                <div className="text-sm text-muted">None.</div>
              ) : (
                <ul className="space-y-2 text-sm">
                  {audit.warnings.map((f, i) => (
                    <li key={i}>
                      <div className="text-amber">{f.title}</div>
                      <div className="text-muted text-xs">{f.detail}</div>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel title="Recommendations">
              <ul className="list-disc pl-5 text-sm text-muted space-y-1">
                {audit.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </Panel>

            <Panel title="Timeline">
              <ol className="space-y-2 text-sm">
                {audit.timeline.map((t, i) => (
                  <li key={i} className="flex gap-3">
                    <span className="mono text-xs text-cyan shrink-0">{t.event}</span>
                    <span className="text-muted">{t.detail}</span>
                  </li>
                ))}
              </ol>
            </Panel>
          </>
        ) : null}
      </div>
    </>
  );
}
