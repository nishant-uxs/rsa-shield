export type AuditState =
  | "FACTOR_FOUND"
  | "SUSPICIOUS"
  | "INCONCLUSIVE"
  | "NO_WEAKNESS_DETECTED_BY_CONFIGURED_CHECKS"
  | "INVALID_KEY";

export interface Finding {
  category: string;
  code: string;
  severity: string;
  title: string;
  detail: string;
}

export interface KeyRecord {
  id: number;
  key_id: string;
  label: string;
  source: string;
  algorithm: string;
  bit_length: number;
  exponent: number;
  fingerprint: string;
  modulus_preview: string;
  created_at: string;
}

export interface AuditRecord {
  id: number;
  audit_id: string;
  key_id: string;
  status: string;
  final_state: AuditState | null;
  factor_found: boolean;
  factor_hex?: string | null;
  cofactor_hex?: string | null;
  factor_method?: string | null;
  elapsed_ms?: number | null;
  checks: Finding[];
  warnings: Finding[];
  findings: Finding[];
  recommendations: string[];
  timeline: { at: string; event: string; detail: string }[];
  ecm?: Record<string, unknown> | null;
  ecm_config?: Record<string, unknown> | null;
  probes?: Record<string, unknown> | null;
  bit_length?: number | null;
  exponent?: number | null;
  key_label?: string | null;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface DashboardSummary {
  total_keys: number;
  total_audits: number;
  factor_found: number;
  suspicious: number;
  inconclusive: number;
  no_weakness: number;
  invalid: number;
  avg_audit_ms: number | null;
  recent_audits: AuditRecord[];
  risk_distribution: Record<string, number>;
  key_size_distribution: Record<string, number>;
  activity: { audit_id: string; state: string | null; at: string | null; elapsed_ms: number | null }[];
}

export interface FixtureInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  expected_hint: string;
}
