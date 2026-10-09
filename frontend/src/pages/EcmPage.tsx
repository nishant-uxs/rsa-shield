import { Topbar } from "../components/Layout";
import { Panel } from "../components/StatCard";

const STEPS = [
  "RSA modulus n",
  "Factorization attempt (budgeted)",
  "Elliptic curve based search (Lenstra ECM)",
  "Factor discovered / not discovered",
  "Evidence recorded (never ‘SECURE’)",
];

export function EcmPage() {
  return (
    <>
      <Topbar
        title="ECM Analysis"
        subtitle="Lenstra Elliptic Curve Method as an auditing probe"
        breadcrumb="Cryptanalysis Engine / ECM Analysis"
      />
      <div className="p-6 grid lg:grid-cols-2 gap-4">
        <Panel title="Conceptual workflow">
          <ol className="space-y-3">
            {STEPS.map((s, i) => (
              <li key={s} className="flex gap-3 items-start">
                <span className="mono text-cyan text-xs mt-0.5">{String(i + 1).padStart(2, "0")}</span>
                <div>
                  <div className="text-sm font-medium">{s}</div>
                  {i < STEPS.length - 1 ? <div className="text-muted text-xs mt-1">↓</div> : null}
                </div>
              </li>
            ))}
          </ol>
        </Panel>
        <Panel title="Interpretation rules">
          <ul className="text-sm text-muted space-y-2 leading-relaxed">
            <li>
              <span className="text-crit font-medium mono text-xs">FACTOR_FOUND</span> — non-trivial factor is
              mathematical evidence of weakness.
            </li>
            <li>
              <span className="text-amber font-medium mono text-xs">SUSPICIOUS</span> — heuristic warnings only (e.g.,
              legacy size).
            </li>
            <li>
              <span className="text-violet font-medium mono text-xs">INCONCLUSIVE</span> — no factor within configured
              budget.
            </li>
            <li>
              <span className="text-ok font-medium mono text-xs">NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS</span> —
              configured checks only; not a proof.
            </li>
            <li className="text-amber">ECM does not instantly factor properly generated modern RSA keys.</li>
          </ul>
        </Panel>
      </div>
    </>
  );
}
