import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 opacity-40 pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 rounded-full bg-cyan/10 blur-3xl" />
        <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-violet/10 blur-3xl" />
      </div>
      <header className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-border/50">
        <div className="font-[family-name:var(--font-display)] font-semibold tracking-tight text-lg">RSA-SHIELD</div>
        <div className="text-xs text-muted mono">Team Aegis · Bennett University</div>
      </header>
      <main className="relative z-10 max-w-5xl mx-auto px-6 py-20 md:py-28">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan/30 bg-cyan/10 px-3 py-1 text-[11px] uppercase tracking-widest text-cyan mb-6">
          Security Audit Platform
        </div>
        <h1 className="text-5xl md:text-6xl font-[family-name:var(--font-display)] font-bold tracking-tight text-cyan mb-4">
          RSA-SHIELD
        </h1>
        <p className="text-2xl md:text-3xl text-text font-medium mb-4 max-w-2xl">
          Mathematical Assurance for RSA Key Security
        </p>
        <p className="text-muted text-lg max-w-2xl mb-10 leading-relaxed">
          Analyze RSA cryptographic assets, investigate mathematical weaknesses, and generate evidence-backed
          security audits. Failure to factor a key is never labeled “secure”.
        </p>
        <div className="flex flex-wrap gap-3 mb-14">
          <Link
            to="/app/auditor"
            className="rounded-lg bg-cyan text-bg px-5 py-3 text-sm font-semibold hover:bg-cyan/90 transition"
          >
            Start an Audit
          </Link>
          <Link
            to="/app/lab"
            className="rounded-lg border border-violet/40 bg-violet/10 text-violet px-5 py-3 text-sm font-semibold hover:bg-violet/20 transition"
          >
            Explore Test Lab
          </Link>
        </div>
        <div className="glass rounded-2xl p-6 max-w-md">
          <div className="mono text-cyan text-xl mb-2">n = p × q</div>
          <div className="text-sm text-muted leading-relaxed">
            Lenstra ECM is used as a budgeted factorization probe for authorized keys and controlled lab fixtures —
            not as a magic break of modern strong RSA.
          </div>
        </div>
      </main>
    </div>
  );
}
