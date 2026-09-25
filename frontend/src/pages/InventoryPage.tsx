import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord, KeyRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState, EmptyState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

export function InventoryPage() {
  const [keys, setKeys] = useState<KeyRecord[]>([]);
  const [audits, setAudits] = useState<AuditRecord[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<"date" | "size">("date");

  useEffect(() => {
    Promise.all([api.listKeys(), api.listAudits()])
      .then(([k, a]) => {
        setKeys(k.items);
        setAudits(a.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const latestByKey = useMemo(() => {
    const m = new Map<string, AuditRecord>();
    for (const a of audits) {
      if (!m.has(a.key_id)) m.set(a.key_id, a);
    }
    return m;
  }, [audits]);

  const filtered = useMemo(() => {
    let rows = keys;
    if (q.trim()) {
      const qq = q.toLowerCase();
      rows = rows.filter(
        (k) =>
          k.key_id.toLowerCase().includes(qq) ||
          k.label.toLowerCase().includes(qq) ||
          k.source.toLowerCase().includes(qq),
      );
    }
    rows = [...rows].sort((a, b) =>
      sort === "size" ? b.bit_length - a.bit_length : +new Date(b.created_at) - +new Date(a.created_at),
    );
    return rows;
  }, [keys, q, sort]);

  return (
    <>
      <Topbar title="Key Inventory" subtitle="Search, filter, and review audited RSA public keys" />
      <div className="p-6 space-y-4">
        <div className="flex flex-wrap gap-3">
          <input
            className="rounded-lg bg-panel border border-border px-3 py-2 text-sm min-w-[240px]"
            placeholder="Search key id, label, source…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="rounded-lg bg-panel border border-border px-3 py-2 text-sm"
            value={sort}
            onChange={(e) => setSort(e.target.value as "date" | "size")}
          >
            <option value="date">Sort by date</option>
            <option value="size">Sort by size</option>
          </select>
        </div>
        {loading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}
        <Panel title={`Keys (${filtered.length})`}>
          {filtered.length === 0 && !loading ? (
            <EmptyState title="No keys" detail="Upload a key or run Test Lab fixtures." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-muted text-left">
                  <tr>
                    <th className="py-2">Key ID</th>
                    <th>Source</th>
                    <th>Algo</th>
                    <th>Size</th>
                    <th>Latest state</th>
                    <th>Audited</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((k) => {
                    const a = latestByKey.get(k.key_id);
                    return (
                      <tr key={k.key_id} className="border-t border-border/60">
                        <td className="py-2 mono text-cyan">{k.key_id}</td>
                        <td>{k.source}</td>
                        <td>{k.algorithm}</td>
                        <td className="mono">{k.bit_length}</td>
                        <td>{a ? <RiskBadge state={a.final_state} /> : "—"}</td>
                        <td className="mono text-xs">
                          {a ? <Link to={`/app/audits/${a.audit_id}`}>{a.audit_id}</Link> : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
