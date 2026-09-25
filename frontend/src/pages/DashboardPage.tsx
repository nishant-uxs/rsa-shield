import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { api } from "../api";
import type { DashboardSummary } from "../types";
import { Topbar } from "../components/Layout";
import { StatCard, Panel, LoadingState, ErrorState, EmptyState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

const COLORS = ["#f87171", "#f59e0b", "#a78bfa", "#34d399", "#94a3b8"];

export function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <Topbar title="Overview Dashboard" subtitle="RSA cryptographic asset posture" />
        <div className="p-6">
          <LoadingState label="Loading dashboard…" />
        </div>
      </>
    );
  }
  if (error) {
    return (
      <>
        <Topbar title="Overview Dashboard" />
        <div className="p-6">
          <ErrorState message={error} />
        </div>
      </>
    );
  }
  if (!data) {
    return (
      <>
        <Topbar title="Overview Dashboard" />
        <div className="p-6">
          <EmptyState title="No data" detail="Run an audit from Test Lab to populate metrics." />
        </div>
      </>
    );
  }

  const pie = Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }));
  const sizes = Object.entries(data.key_size_distribution).map(([name, value]) => ({ name, value }));

  return (
    <>
      <Topbar title="Overview Dashboard" subtitle="Evidence-tiered RSA key auditing metrics" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <StatCard label="Keys audited" value={data.total_keys} />
          <StatCard label="Factor evidence" value={data.factor_found} accent="crit" />
          <StatCard label="Suspicious" value={data.suspicious} accent="amber" />
          <StatCard label="Inconclusive" value={data.inconclusive} accent="violet" />
          <StatCard
            label="Avg audit (ms)"
            value={data.avg_audit_ms != null ? Math.round(data.avg_audit_ms) : "—"}
            accent="ok"
          />
        </div>

        <div className="grid lg:grid-cols-2 gap-4">
          <Panel title="Risk distribution">
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pie} dataKey="value" nameKey="name" outerRadius={90} label={false}>
                    {pie.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Panel>
          <Panel title="Key-size distribution">
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sizes}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>

        <Panel title="Recent audits" action={<Link className="text-xs text-cyan" to="/app/inventory">View inventory</Link>}>
          {data.recent_audits.length === 0 ? (
            <EmptyState title="No audits yet" detail="Open Test Lab and run the weak-key demo." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-muted text-left">
                  <tr>
                    <th className="py-2">Audit</th>
                    <th>Key</th>
                    <th>State</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_audits.map((a) => (
                    <tr key={a.audit_id} className="border-t border-border/60">
                      <td className="py-2 mono text-cyan">
                        <Link to={`/app/audits/${a.audit_id}`}>{a.audit_id}</Link>
                      </td>
                      <td className="mono text-muted">{a.key_id}</td>
                      <td>
                        <RiskBadge state={a.final_state} />
                      </td>
                      <td className="mono">{a.elapsed_ms != null ? `${Math.round(a.elapsed_ms)} ms` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
