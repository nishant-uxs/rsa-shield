import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import type { AuditRecord, KeyRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";

export function AuditorPage() {
  const nav = useNavigate();
  const [tab, setTab] = useState<"pem" | "raw">("pem");
  const [pem, setPem] = useState("");
  const [n, setN] = useState("");
  const [e, setE] = useState("65537");
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [key, setKey] = useState<KeyRecord | null>(null);
  const [audit, setAudit] = useState<AuditRecord | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    setAudit(null);
    try {
      const k =
        tab === "pem"
          ? await api.createKeyPem(pem, label || "Uploaded key")
          : await api.createKeyRaw(n, Number(e), label || "Manual modulus");
      setKey(k);
      const a = await api.startAudit(k.key_id);
      setAudit(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Topbar title="RSA Key Auditor" subtitle="Upload PEM or enter modulus n and exponent e" />
      <div className="p-6 grid lg:grid-cols-2 gap-4">
        <Panel title="Key input">
          <div className="flex gap-2 mb-4">
            <button
              className={`px-3 py-1.5 rounded-lg text-sm ${tab === "pem" ? "bg-cyan/20 text-cyan border border-cyan/40" : "border border-border text-muted"}`}
              onClick={() => setTab("pem")}
            >
              PEM public key
            </button>
            <button
              className={`px-3 py-1.5 rounded-lg text-sm ${tab === "raw" ? "bg-cyan/20 text-cyan border border-cyan/40" : "border border-border text-muted"}`}
              onClick={() => setTab("raw")}
            >
              Modulus + exponent
            </button>
          </div>
          <input
            className="w-full mb-3 rounded-lg bg-bg border border-border px-3 py-2 text-sm"
            placeholder="Label (optional)"
            value={label}
            onChange={(ev) => setLabel(ev.target.value)}
          />
          {tab === "pem" ? (
            <textarea
              className="w-full h-48 rounded-lg bg-bg border border-border px-3 py-2 text-xs mono"
              placeholder="-----BEGIN PUBLIC KEY-----"
              value={pem}
              onChange={(ev) => setPem(ev.target.value)}
            />
          ) : (
            <div className="space-y-3">
              <textarea
                className="w-full h-32 rounded-lg bg-bg border border-border px-3 py-2 text-xs mono"
                placeholder="Modulus n (decimal or hex)"
                value={n}
                onChange={(ev) => setN(ev.target.value)}
              />
              <input
                className="w-full rounded-lg bg-bg border border-border px-3 py-2 text-sm mono"
                value={e}
                onChange={(ev) => setE(ev.target.value)}
              />
            </div>
          )}
          <button
            disabled={busy}
            onClick={run}
            className="mt-4 rounded-lg bg-cyan text-bg px-4 py-2 text-sm font-semibold disabled:opacity-50"
          >
            {busy ? "Running audit…" : "Validate · Analyze · Audit"}
          </button>
          {error ? <div className="mt-3"><ErrorState message={error} /></div> : null}
        </Panel>

        <Panel title="Live result">
          {!key && !audit ? (
            <p className="text-sm text-muted">Submit a public key to see parse results, ECM status, and evidence tiers.</p>
          ) : (
            <div className="space-y-3 text-sm">
              {key ? (
                <div className="rounded-lg border border-border p-3 space-y-1">
                  <div><span className="text-muted">Key ID:</span> <span className="mono text-cyan">{key.key_id}</span></div>
                  <div><span className="text-muted">Size:</span> {key.bit_length}-bit</div>
                  <div><span className="text-muted">Exponent:</span> <span className="mono">e = {key.exponent}</span></div>
                  <div><span className="text-muted">Fingerprint:</span> <span className="mono text-xs">{key.fingerprint.slice(0, 24)}…</span></div>
                </div>
              ) : null}
              {audit ? (
                <div className="rounded-lg border border-border p-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="mono text-cyan">{audit.audit_id}</span>
                    <RiskBadge state={audit.final_state} />
                  </div>
                  <div>ECM / job: <span className="mono">{audit.status}</span></div>
                  <div>Duration: <span className="mono">{audit.elapsed_ms != null ? `${Math.round(audit.elapsed_ms)} ms` : "—"}</span></div>
                  {audit.factor_found ? (
                    <div className="text-crit">Factor evidence recorded (hex prefix: {audit.factor_hex?.slice(0, 18)}…)</div>
                  ) : (
                    <div className="text-amber text-xs">No factor in budget ⇒ inconclusive — not a security proof.</div>
                  )}
                  <button
                    className="text-xs text-cyan underline"
                    onClick={() => nav(`/app/audits/${audit.audit_id}`)}
                  >
                    Open audit details
                  </button>
                </div>
              ) : null}
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
