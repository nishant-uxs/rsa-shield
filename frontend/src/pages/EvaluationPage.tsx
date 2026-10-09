import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

type Tab = "fixtures" | "ablation" | "comparison" | "corpus";

export function EvaluationPage() {
  const [tab, setTab] = useState<Tab>("fixtures");
  const [bundle, setBundle] = useState<Awaited<ReturnType<typeof api.researchBundle>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .researchBundle(2500, 36)
      .then(setBundle)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const tabs: { id: Tab; label: string }[] = [
    { id: "fixtures", label: "Fixture suite" },
    { id: "ablation", label: "Ablation" },
    { id: "comparison", label: "Config compare" },
    { id: "corpus", label: "Mini corpus" },
  ];

  const fixtures = bundle?.fixture_suite;
  const ablation = bundle?.ablation;
  const comparison = bundle?.configuration_comparison;
  const corpus = bundle?.mini_corpus;

  return (
    <>
      <Topbar
        title="Research Evaluation"
        subtitle="Paper-ready tables: fixtures, ablation, configuration compare, mini corpus"
        breadcrumb="Cryptanalysis Engine / Evaluation"
      />
      <div className="p-6 space-y-4">
        <div className="rounded-xl border border-amber/40 bg-amber/10 px-4 py-3 text-sm text-amber">
          Controlled / synthetic studies only. INCONCLUSIVE never means SECURE. Not an Internet-scale
          measurement.
        </div>

        <div className="flex flex-wrap gap-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-lg text-sm mono border transition ${
                tab === t.id ? "border-cyan/50 bg-cyan/15 text-cyan" : "border-border/60 text-muted"
              }`}
            >
              {t.label}
            </button>
          ))}
          {bundle ? (
            <button
              type="button"
              className="ml-auto text-xs text-cyan mono underline"
              onClick={() => {
                const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "rsa-shield-research-bundle.json";
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              Download JSON bundle
            </button>
          ) : null}
        </div>

        {loading ? <LoadingState label="Running research evaluation bundle…" /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && fixtures && tab === "fixtures" ? (
          <>
            <div className="grid sm:grid-cols-3 gap-3">
              <Stat label="Fixtures" value={fixtures.total} />
              <Stat label="Hint matches" value={`${fixtures.hint_matches}/${fixtures.total}`} accent />
              <Stat label="SECURE labels" value="0" ok />
            </div>
            <Panel title="Table — fixture suite">
              <SimpleTable
                headers={["Fixture", "Expected", "Observed", "Method", "ms", "Match"]}
                rows={fixtures.rows.map((r) => [
                  r.name,
                  r.expected_hint,
                  <RiskBadge key={r.fixture_id} state={r.final_state} />,
                  r.factor_method || "—",
                  String(Math.round(r.elapsed_ms)),
                  r.match_hint ? "yes" : "partial",
                ])}
              />
            </Panel>
          </>
        ) : null}

        {!loading && ablation && tab === "ablation" ? (
          <>
            <Panel title="Table — probe contribution (weak fixtures)">
              <SimpleTable
                headers={["Probe", "Hits / weak", "Hit rate", "Avg ms"]}
                rows={Object.entries(ablation.summary).map(([name, s]) => [
                  name,
                  `${s.factor_hits_on_weak_fixtures}/${s.weak_fixtures}`,
                  s.hit_rate == null ? "—" : String(s.hit_rate),
                  String(s.avg_ms),
                ])}
              />
            </Panel>
            <Panel title="Per-fixture probe matrix (factor_found)">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-muted mono text-[11px] uppercase text-left">
                    <tr>
                      <th className="py-2">Fixture</th>
                      {Object.keys(ablation.matrix[0]?.probes || {}).map((p) => (
                        <th key={p}>{p}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {ablation.matrix.map((row) => (
                      <tr key={row.fixture_id} className="border-t border-border/50">
                        <td className="py-2 text-xs">{row.name}</td>
                        {Object.entries(row.probes).map(([p, v]) => (
                          <td key={p} className={`mono text-xs ${v.factor_found ? "text-crit" : "text-muted"}`}>
                            {v.factor_found ? "HIT" : "—"}
                            <div className="text-[10px]">{Math.round(v.elapsed_ms)}ms</div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          </>
        ) : null}

        {!loading && comparison && tab === "comparison" ? (
          <>
            <Panel title="Table — configuration precision / recall">
              <SimpleTable
                headers={["Config", "TP", "FP", "FN", "Precision", "Recall", "Avg ms", "SECURE?"]}
                rows={comparison.aggregates.map((a) => [
                  a.label,
                  String(a.tp),
                  String(a.fp),
                  String(a.fn),
                  a.precision == null ? "—" : String(a.precision),
                  a.recall == null ? "—" : String(a.recall),
                  String(a.avg_ms),
                  a.emits_secure_label ? "yes" : "no",
                ])}
              />
            </Panel>
            <Panel title="External tools">
              <ul className="text-sm text-muted space-y-2">
                {Object.entries(comparison.external_tools).map(([name, info]) => (
                  <li key={name}>
                    <span className="text-cyan mono">{name}</span>:{" "}
                    {info.available ? "available" : "not bundled"} — {info.note}
                  </li>
                ))}
              </ul>
            </Panel>
          </>
        ) : null}

        {!loading && corpus && tab === "corpus" ? (
          <>
            <div className="grid sm:grid-cols-4 gap-3">
              <Stat label="Corpus size" value={corpus.corpus_size} />
              <Stat label="Factor evidence" value={corpus.summary.keys_with_factor_evidence} accent />
              <Stat label="Shared-factor hits" value={corpus.batch_gcd.hit_count} />
              <Stat label="SECURE labels" value={corpus.secure_labels_emitted} ok />
            </div>
            <Panel title="Class counts">
              <SimpleTable
                headers={["Class", "Count", "Factors found"]}
                rows={Object.entries(corpus.class_counts).map(([k, v]) => [
                  k,
                  String(v),
                  String(corpus.factor_finds_by_class[k] || 0),
                ])}
              />
            </Panel>
            <Panel title="Sample rows">
              <SimpleTable
                headers={["ID", "Class", "Bits", "State", "Method", "ms"]}
                rows={corpus.sample_rows.map((r) => [
                  r.id,
                  r.class,
                  String(r.bits),
                  <RiskBadge key={r.id} state={r.state} />,
                  r.method || "—",
                  String(Math.round(r.elapsed_ms)),
                ])}
              />
            </Panel>
          </>
        ) : null}
      </div>
    </>
  );
}

function Stat({
  label,
  value,
  accent,
  ok,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
  ok?: boolean;
}) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="mono text-[11px] text-muted uppercase">{label}</div>
      <div
        className={`display text-2xl font-semibold mt-1 ${accent ? "text-cyan" : ok ? "text-ok" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}

function SimpleTable({
  headers,
  rows,
}: {
  headers: string[];
  rows: (string | number | ReactNode)[][];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-muted text-left mono text-[11px] uppercase">
          <tr>
            {headers.map((h) => (
              <th key={h} className="py-2 pr-3">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-border/50">
              {row.map((cell, j) => (
                <td key={j} className="py-2 pr-3 align-top">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
