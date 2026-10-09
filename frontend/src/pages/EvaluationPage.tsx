import { useEffect, useState } from "react";
import { api } from "../api";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

interface EvalRow {
  fixture_id: string;
  name: string;
  expected_hint: string;
  final_state: string;
  factor_found: boolean;
  factor_method?: string | null;
  elapsed_ms: number;
  match_hint: boolean;
  notes?: string;
}

interface EvalSuite {
  suite: string;
  disclaimer: string;
  total: number;
  hint_matches: number;
  rows: EvalRow[];
  related_work_gap: string[];
}

export function EvaluationPage() {
  const [data, setData] = useState<EvalSuite | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .evaluationSuite(3000)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Topbar
        title="Evaluation Suite"
        subtitle="Reproducible fixture benchmarks for demos / paper tables"
        breadcrumb="Cryptanalysis Engine / Evaluation"
      />
      <div className="p-6 space-y-4">
        {loading ? <LoadingState label="Running fixture evaluation…" /> : null}
        {error ? <ErrorState message={error} /> : null}
        {data ? (
          <>
            <div className="rounded-xl border border-amber/40 bg-amber/10 px-4 py-3 text-sm text-amber">
              {data.disclaimer}
            </div>
            <div className="grid sm:grid-cols-3 gap-3">
              <div className="glass rounded-xl p-4">
                <div className="mono text-[11px] text-muted uppercase">Fixtures</div>
                <div className="display text-2xl font-semibold mt-1">{data.total}</div>
              </div>
              <div className="glass rounded-xl p-4">
                <div className="mono text-[11px] text-muted uppercase">Hint matches</div>
                <div className="display text-2xl font-semibold mt-1 text-cyan">
                  {data.hint_matches}/{data.total}
                </div>
              </div>
              <div className="glass rounded-xl p-4">
                <div className="mono text-[11px] text-muted uppercase">SECURE labels</div>
                <div className="display text-2xl font-semibold mt-1 text-ok">0</div>
              </div>
            </div>
            <Panel title="Fixture results">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-muted text-left mono text-[11px] uppercase">
                    <tr>
                      <th className="py-2">Fixture</th>
                      <th>Expected</th>
                      <th>Observed</th>
                      <th>Method</th>
                      <th>ms</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((r) => (
                      <tr key={r.fixture_id} className="border-t border-border/50">
                        <td className="py-2">
                          <div className="font-medium">{r.name}</div>
                          <div className="mono text-[10px] text-muted">{r.fixture_id}</div>
                        </td>
                        <td className="text-xs text-muted max-w-[140px]">{r.expected_hint}</td>
                        <td>
                          <RiskBadge state={r.final_state} />
                        </td>
                        <td className="mono text-xs">{r.factor_method || "—"}</td>
                        <td className="mono text-xs">{Math.round(r.elapsed_ms)}</td>
                        <td className={r.match_hint ? "text-ok" : "text-amber"}>{r.match_hint ? "yes" : "partial"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
            <Panel title="Related-work gap (honest)">
              <ul className="text-sm text-muted space-y-2 list-disc pl-5">
                {data.related_work_gap.map((g) => (
                  <li key={g}>{g}</li>
                ))}
              </ul>
            </Panel>
          </>
        ) : null}
      </div>
    </>
  );
}
