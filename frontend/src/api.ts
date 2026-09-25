import type { AuditRecord, DashboardSummary, FixtureInfo, KeyRecord } from "./types";

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  dashboard: () => request<DashboardSummary>("/dashboard/summary"),
  listKeys: (q?: string) =>
    request<{ total: number; items: KeyRecord[] }>(`/keys${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  createKeyPem: (pem: string, label = "") =>
    request<KeyRecord>("/keys/pem", { method: "POST", body: JSON.stringify({ pem, label, source: "upload" }) }),
  createKeyRaw: (n: string, e: number, label = "") =>
    request<KeyRecord>("/keys/raw", { method: "POST", body: JSON.stringify({ n, e, label, source: "manual" }) }),
  startAudit: (key_id: string, opts?: { run_ecm?: boolean; timeout_ms?: number }) =>
    request<AuditRecord>("/audits", {
      method: "POST",
      body: JSON.stringify({ key_id, run_ecm: true, ...opts }),
    }),
  listAudits: () => request<{ total: number; items: AuditRecord[] }>("/audits"),
  getAudit: (id: string) => request<AuditRecord>(`/audits/${id}`),
  fixtures: () => request<{ items: FixtureInfo[] }>("/test-lab/fixtures"),
  runFixture: (fixture_id: string, timeout_ms?: number) =>
    request<AuditRecord>("/test-lab/run", {
      method: "POST",
      body: JSON.stringify({ fixture_id, run_ecm: true, timeout_ms }),
    }),
  report: (audit_id: string) =>
    request<{ report_id: string; content: Record<string, unknown>; created_at: string }>(`/reports/${audit_id}`, {
      method: "POST",
    }),
};
