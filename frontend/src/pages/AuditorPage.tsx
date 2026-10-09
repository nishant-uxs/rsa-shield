import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Play, ClipboardPaste, Eraser } from "lucide-react";
import { api } from "../api";
import type { AuditRecord, KeyRecord } from "../types";
import { Topbar } from "../components/Layout";
import { Panel, ErrorState } from "../components/StatCard";
import { RiskBadge } from "../components/RiskBadge";
import clsx from "clsx";

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

  async function pasteClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      setPem(text);
      setTab("pem");
    } catch {
      setError("Clipboard access denied");
    }
  }

  return (
    <>
      <Topbar
        title="RSA Key Auditor"
        subtitle="Key ingest & factorization workbench"
        breadcrumb="Cryptanalysis Engine / RSA Auditor / Key Ingest"
      />
      <div className="p-6 grid lg:grid-cols-[1.2fr_0.8fr] gap-4">
        <Panel title="Key ingest">
          <div className="flex flex-wrap gap-2 mb-4 border-b border-border/50 pb-3">
            {(
              [
                ["pem", "PEM Public Key"],
                ["raw", "Modulus (n) + Exponent (e)"],
              ] as const
            ).map(([id, labelText]) => (
              <button
                key={id}
                className={clsx(
                  "px-3 py-1.5 rounded-lg text-sm mono transition",
                  tab === id
                    ? "bg-cyan/15 text-cyan border-b-2 border-cyan rounded-b-none"
                    : "text-muted hover:text-text border border-transparent",
                )}
                onClick={() => setTab(id)}
              >
                {labelText}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2 mb-3">
            <input
              className="flex-1 min-w-[200px] rounded-lg bg-bg border border-border px-3 py-2 text-sm input-focus"
              placeholder="Target label / service tag"
              value={label}
              onChange={(ev) => setLabel(ev.target.value)}
            />
            <span className="mono text-[10px] uppercase px-2 py-1 rounded border border-cyan/30 bg-cyan/10 text-cyan">
              Format: {tab === "pem" ? "PEM" : "n + e"}
            </span>
          </div>

          {tab === "pem" ? (
            <>
              <div className="flex justify-end gap-2 mb-2">
                <button
                  type="button"
                  onClick={pasteClipboard}
                  className="inline-flex items-center gap-1 text-[11px] mono text-muted hover:text-cyan"
                >
                  <ClipboardPaste className="h-3.5 w-3.5" /> Paste
                </button>
                <button
                  type="button"
                  onClick={() => setPem("")}
                  className="inline-flex items-center gap-1 text-[11px] mono text-muted hover:text-crit"
                >
                  <Eraser className="h-3.5 w-3.5" /> Clear
                </button>
              </div>
              <textarea
                className="w-full h-52 rounded-lg bg-bg border border-border px-3 py-2 text-xs mono input-focus"
                placeholder="-----BEGIN PUBLIC KEY-----"
                value={pem}
                onChange={(ev) => setPem(ev.target.value)}
              />
            </>
          ) : (
            <div className="space-y-3">
              <textarea
                className="w-full h-36 rounded-lg bg-bg border border-border px-3 py-2 text-xs mono input-focus"
                placeholder="Modulus n (decimal or hex)"
                value={n}
                onChange={(ev) => setN(ev.target.value)}
              />
              <input
                className="w-full rounded-lg bg-bg border border-border px-3 py-2 text-sm mono input-focus"
                value={e}
                onChange={(ev) => setE(ev.target.value)}
                placeholder="Public exponent e"
              />
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-3">
            <button
              disabled={busy}
              onClick={run}
              className="inline-flex items-center gap-2 rounded-lg bg-cyan text-on-primary px-4 py-2.5 text-sm font-semibold disabled:opacity-50 shadow-[0_0_20px_rgba(34,211,238,0.25)] sheen"
            >
              <Play className="h-4 w-4" />
              {busy ? "Running audit…" : "Validate, Analyze & Audit"}
            </button>
            <button
              type="button"
              onClick={() => {
                setPem("");
                setN("");
                setE("65537");
                setLabel("");
                setKey(null);
                setAudit(null);
                setError(null);
              }}
              className="rounded-lg border border-border px-4 py-2.5 text-sm text-muted hover:text-text"
            >
              Reset
            </button>
          </div>
          {error ? (
            <div className="mt-3">
              <ErrorState message={error} />
            </div>
          ) : null}
        </Panel>

        <Panel
          title="Live cryptanalytic result"
          action={
            audit?.elapsed_ms != null ? (
              <span className="mono text-[10px] text-muted">Latency: {Math.round(audit.elapsed_ms)} ms</span>
            ) : null
          }
        >
          {!key && !audit ? (
            <p className="text-sm text-muted leading-relaxed">
              Submit a public key to see parse metadata, ECM status, and evidence-tiered audit states. No fake SECURE
              badge is ever shown.
            </p>
          ) : (
            <div className="space-y-3 text-sm">
              {key ? (
                <div className="rounded-lg border border-border/70 bg-surface-low/50 p-3 space-y-1.5">
                  <div>
                    <span className="text-muted">Key ID:</span>{" "}
                    <span className="mono text-cyan">{key.key_id}</span>
                  </div>
                  <div>
                    <span className="text-muted">Modulus length:</span> {key.bit_length}-bit
                  </div>
                  <div>
                    <span className="text-muted">Public exponent:</span>{" "}
                    <span className="mono">e = {key.exponent}</span>
                  </div>
                  <div>
                    <span className="text-muted">Fingerprint:</span>{" "}
                    <span className="mono text-xs">{key.fingerprint.slice(0, 28)}…</span>
                  </div>
                </div>
              ) : null}
              {audit ? (
                <div className="rounded-lg border border-border/70 p-3 space-y-3">
                  {audit.final_state === "FACTOR_FOUND" ? (
                    <div className="rounded-lg border border-crit/40 bg-crit/10 px-3 py-2 text-crit mono text-xs font-medium">
                      CRITICAL ALERT: FACTOR_FOUND
                    </div>
                  ) : null}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="mono text-cyan text-xs">{audit.audit_id}</span>
                    <RiskBadge state={audit.final_state} />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {["FACTOR_FOUND", "SUSPICIOUS", "INCONCLUSIVE"].map((s) => (
                      <span
                        key={s}
                        className={clsx(
                          "mono text-[10px] px-2 py-0.5 rounded border",
                          audit.final_state === s
                            ? "border-cyan/50 text-cyan bg-cyan/10"
                            : "border-border/50 text-muted",
                        )}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                  <div className="text-muted">
                    Job status: <span className="mono text-text">{audit.status}</span>
                  </div>
                  <div className="text-muted">
                    Duration:{" "}
                    <span className="mono text-text">
                      {audit.elapsed_ms != null ? `${Math.round(audit.elapsed_ms)} ms` : "—"}
                    </span>
                  </div>
                  {audit.factor_found ? (
                    <div className="text-crit text-xs">
                      Factor evidence recorded (hex prefix: {audit.factor_hex?.slice(0, 18)}…)
                    </div>
                  ) : (
                    <div className="text-amber text-xs">
                      No factor in budget ⇒ inconclusive — not a security proof.
                    </div>
                  )}
                  <button
                    className="text-xs text-cyan mono hover:underline"
                    onClick={() => nav(`/app/audits/${audit.audit_id}`)}
                  >
                    Open complete audit details →
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
