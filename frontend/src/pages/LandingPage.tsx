import { Link } from "react-router-dom";
import { Shield, ChevronRight, FlaskConical } from "lucide-react";

export function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-bg text-text">
      <header className="sticky top-0 z-50 border-b border-border/80 bg-bg/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="display font-bold text-lg tracking-widest flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-surface-container border border-cyan/30 grid place-items-center text-cyan shadow-[0_0_12px_rgba(34,211,238,0.25)]">
              <Shield className="h-4 w-4" />
            </span>
            RSA-SHIELD
          </div>
          <nav className="hidden md:flex items-center gap-8 display font-semibold text-sm">
            <Link className="text-muted hover:text-cyan transition" to="/app">
              Audits
            </Link>
            <Link className="text-cyan border-b-2 border-cyan pb-0.5" to="/app/ecm">
              Math Engine
            </Link>
            <Link className="text-muted hover:text-cyan transition" to="/app/lab">
              Factorization Lab
            </Link>
            <Link className="text-muted hover:text-cyan transition" to="/app/reports">
              Docs
            </Link>
          </nav>
          <Link
            to="/app/auditor"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan text-on-primary display font-semibold text-sm shadow-[0_0_20px_rgba(34,211,238,0.35)] hover:brightness-110 transition sheen"
          >
            Launch Auditor
          </Link>
        </div>
      </header>

      <main className="flex-1 math-grid-bg relative overflow-hidden">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[450px] bg-cyan/10 rounded-full blur-[140px] pointer-events-none -z-10" />
        <div className="absolute top-1/3 right-1/4 w-[400px] h-[300px] bg-violet/10 rounded-full blur-[120px] pointer-events-none -z-10" />

        <section className="max-w-7xl mx-auto px-6 pt-16 pb-20 lg:pt-20 lg:pb-28 flex flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass border border-border/40 mb-8">
            <span className="w-2 h-2 rounded-full bg-cyan animate-pulse shadow-[0_0_8px_#22d3ee]" />
            <span className="mono text-[11px] tracking-wider uppercase text-muted">
              Enterprise cryptographic assurance · Educational auditor
            </span>
          </div>

          <div className="max-w-5xl mx-auto space-y-4">
            <h2 className="display text-sm uppercase tracking-[0.28em] text-cyan font-bold">RSA-SHIELD</h2>
            <h1 className="display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.12]">
              Mathematical Assurance for{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan via-primary to-secondary">
                RSA Key Security
              </span>
            </h1>
            <p className="text-lg text-muted max-w-3xl mx-auto pt-2 leading-relaxed">
              Continuously analyze RSA public keys against factorization probes and configuration checks. Failure to
              factor is never labeled “secure”.
            </p>
          </div>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md mx-auto">
            <Link
              to="/app/auditor"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg bg-cyan text-on-primary display text-sm font-semibold shadow-[0_0_24px_rgba(34,211,238,0.4)] hover:brightness-110 transition sheen"
            >
              Start an Audit
              <ChevronRight className="h-4 w-4" />
            </Link>
            <Link
              to="/app/lab"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-lg glass text-text hover:text-cyan hover:border-cyan/40 display text-sm font-medium transition"
            >
              <FlaskConical className="h-4 w-4" />
              Explore Test Lab
            </Link>
          </div>

          <div className="mt-6 text-[11px] mono text-muted/80">
            Public keys only · Controlled fixtures · Evidence-tiered results
          </div>

          <div className="w-full max-w-5xl mt-14 text-left">
            <div className="glass-elevated rounded-xl p-6 sm:p-8 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan to-transparent" />
              <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-border/40 gap-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="px-2.5 py-1 rounded bg-surface-container border border-border/40 mono text-xs text-cyan font-semibold tracking-wide">
                    DECOMPOSITION: n = p × q
                  </span>
                  <span className="mono text-[11px] text-muted hidden sm:inline">| Modulus audit probe</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-low border border-cyan/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan shadow-[0_0_6px_#22d3ee]" />
                  <span className="mono text-[11px] text-cyan font-medium">Budgeted ECM · No absolute SECURE</span>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <span className="mono text-[11px] text-muted uppercase tracking-wider">
                    Public modulus (n) · educational profile
                  </span>
                  <span className="mono text-[11px] text-primary">e = 65537 (0x10001)</span>
                </div>
                <div className="p-3.5 rounded-lg bg-bg/90 border border-border/40 mono text-xs text-muted break-all leading-relaxed">
                  <span className="text-cyan">0xCBF1E5F8</span>
                  <span>…truncated…</span>
                  <span className="text-cyan">44E2E8E</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                {[
                  { label: "Evidence tiers", value: "FACTOR / SUSPICIOUS / INCONCLUSIVE", hint: "Never “SECURE”" },
                  { label: "Probe method", value: "Lenstra ECM", hint: "Budgeted factorization" },
                  { label: "Input scope", value: "Public keys only", hint: "PEM or n + e" },
                  { label: "Test Lab", value: "Controlled fixtures", hint: "No external targets" },
                ].map((m) => (
                  <div
                    key={m.label}
                    className="p-4 rounded-lg bg-surface-container/60 border border-border/40 hover:border-cyan/40 transition-colors"
                  >
                    <div className="mono text-[11px] text-muted mb-1.5">{m.label}</div>
                    <div className="mono text-sm font-semibold text-text">{m.value}</div>
                    <div className="mt-3 pt-2.5 border-t border-border/30 mono text-[11px] text-primary">{m.hint}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="w-full max-w-5xl mt-14 grid grid-cols-2 md:grid-cols-4 gap-6 py-8 px-4 border-y border-border/40 glass rounded-xl">
            {[
              { v: "ECM", l: "Lenstra probe", s: "Budgeted curves" },
              { v: "Evidence", l: "Tiered states", s: "Factor / Suspicious / Inconclusive" },
              { v: "Lab", l: "Fixtures only", s: "Educational demos" },
              { v: "Team Aegis", l: "Bennett University", s: "Modern Cryptography" },
            ].map((x) => (
              <div key={x.l} className="flex flex-col items-center text-center">
                <div className="display text-2xl font-bold tracking-tight">{x.v}</div>
                <div className="text-xs text-muted mt-1">{x.l}</div>
                <div className="mono text-[10px] text-outline mt-0.5">{x.s}</div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
