import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord, KeyRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState, EmptyState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";
import clsx from "clsx";

const SIZE_CHIPS = [
  { id: "all", label: "All lengths" },
  { id: "4096", label: "4096-bit" },
  { id: "3072", label: "3072-bit" },
  { id: "2048", label: "2048-bit" },
  { id: "lt2048", label: "<2048-bit" },
] as const;

export function InventoryPage() {
  const [keys, setKeys] = useState<KeyRecord[]>([]);
  const [audits, setAudits] = useState<AuditRecord[]>([]);
  const [q, setQ] = useState("");
  const [sizeChip, setSizeChip] = useState<(typeof SIZE_CHIPS)[number]["id"]>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<"date" | "size">("date");
  const [gcdBusy, setGcdBusy] = useState(false);
  const [gcdMsg, setGcdMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listKeys(), api.listAudits()])
      .then(([k, a]) => {
        setKeys(k.items);
        setAudits(a.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function runBatchGcd() {
    setGcdBusy(true);
    setGcdMsg(null);
    setError(null);
    try {
      const r = await api.batchGcd();
      setGcdMsg(
        `${r.message} · hits=${r.hit_count}. ${r.disclaimer}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGcdBusy(false);
    }
  }

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
          k.source.toLowerCase().includes(qq) ||
          k.fingerprint.toLowerCase().includes(qq),
      );
    }
    if (sizeChip === "4096") rows = rows.filter((k) => k.bit_length === 4096);
    else if (sizeChip === "3072") rows = rows.filter((k) => k.bit_length === 3072);
    else if (sizeChip === "2048") rows = rows.filter((k) => k.bit_length === 2048);
    else if (sizeChip === "lt2048") rows = rows.filter((k) => k.bit_length < 2048);

    rows = [...rows].sort((a, b) =>
      sort === "size" ? b.bit_length - a.bit_length : +new Date(b.created_at) - +new Date(a.created_at),
    );
    return rows;
  }, [keys, q, sort, sizeChip]);

  return (
    <>
      <Topbar
        title="Key Inventory"
        subtitle="Public key ring & modulus registry"
        breadcrumb="Cryptanalysis Engine / Key Inventory"
      />
      <div className="p-6 space-y-4">
        <div className="flex flex-wrap gap-3 items-center">
          <input
            className="rounded-lg bg-surface-low border border-border px-3 py-2 text-sm min-w-[260px] input-focus"
            placeholder="Search Key ID, label, fingerprint…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="rounded-lg bg-surface-low border border-border px-3 py-2 text-sm"
            value={sort}
            onChange={(e) => setSort(e.target.value as "date" | "size")}
          >
            <option value="date">Sort by date</option>
            <option value="size">Sort by size</option>
          </select>
          <button
            type="button"
            disabled={gcdBusy || keys.length < 2}
            onClick={runBatchGcd}
            className="rounded-lg border border-violet/40 bg-violet/15 text-violet px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            {gcdBusy ? "Running batch GCD…" : "Batch GCD (shared factors)"}
          </button>
        </div>
        {gcdMsg ? <div className="text-sm text-muted mono leading-relaxed">{gcdMsg}</div> : null}

        <div className="flex flex-wrap gap-2">
          {SIZE_CHIPS.map((c) => (
            <button
              key={c.id}
              onClick={() => setSizeChip(c.id)}
              className={clsx(
                "mono text-[11px] px-2.5 py-1 rounded-md border transition",
                sizeChip === c.id
                  ? "border-cyan/50 bg-cyan/15 text-cyan"
                  : "border-border/60 text-muted hover:text-text",
              )}
            >
              {c.label}
            </button>
          ))}
        </div>

        {loading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}

        <Panel title={`Public keys (${filtered.length})`}>
          {filtered.length === 0 && !loading ? (
            <EmptyState title="No keys" detail="Upload a key or run Test Lab fixtures." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-muted text-left mono text-[11px] uppercase tracking-wider">
                  <tr>
                    <th className="py-2 font-medium">Key ID / Label</th>
                    <th className="font-medium">Bits</th>
                    <th className="font-medium">Exponent</th>
                    <th className="font-medium">Fingerprint</th>
                    <th className="font-medium">Last audit</th>
                    <th className="font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((k) => {
                    const a = latestByKey.get(k.key_id);
                    return (
                      <tr key={k.key_id} className="border-t border-border/50 hover:bg-surface-low/40 transition">
                        <td className="py-2.5">
                          <div className="mono text-cyan text-xs">{k.key_id}</div>
                          <div className="text-xs text-muted mt-0.5">{k.label || k.source}</div>
                        </td>
                        <td className="mono">{k.bit_length}</td>
                        <td className="mono text-xs">e = {k.exponent}</td>
                        <td className="mono text-[11px] text-muted">{k.fingerprint.slice(0, 16)}…</td>
                        <td>
                          {a ? (
                            <Link to={`/app/audits/${a.audit_id}`} className="inline-flex">
                              <RiskBadge state={a.final_state} />
                            </Link>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="mono text-[11px] text-muted">
                          {new Date(k.created_at).toLocaleString()}
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
