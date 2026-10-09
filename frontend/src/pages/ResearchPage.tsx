import { useEffect, useState } from "react";
import { api } from "../api";
import { Topbar } from "../components/Layout";
import { Panel, LoadingState, ErrorState } from "../components/StatCard";

interface RelatedItem {
  name: string;
  focus: string;
  gap_vs_us: string;
}

interface RelatedWork {
  product: string;
  positioning: string;
  items: RelatedItem[];
  our_contributions: string[];
}

export function ResearchPage() {
  const [data, setData] = useState<RelatedWork | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .relatedWork()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Topbar
        title="Related Work & Positioning"
        subtitle="Honest academic framing — packaging + evidence tiers, not new RSA math"
        breadcrumb="Cryptanalysis Engine / Research"
      />
      <div className="p-6 space-y-4">
        {loading ? <LoadingState /> : null}
        {error ? <ErrorState message={error} /> : null}
        {data ? (
          <>
            <Panel title="Positioning">
              <p className="text-sm text-muted leading-relaxed">{data.positioning}</p>
            </Panel>
            <Panel title="Our contributions (systems / pedagogy)">
              <ul className="space-y-2 text-sm list-disc pl-5">
                {data.our_contributions.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </Panel>
            <Panel title="Prior work vs RSA-SHIELD">
              <div className="space-y-4">
                {data.items.map((item) => (
                  <div key={item.name} className="rounded-lg border border-border/60 p-4 bg-surface-low/40">
                    <div className="display font-semibold text-cyan text-sm">{item.name}</div>
                    <div className="text-sm mt-1">
                      <span className="text-muted">Focus: </span>
                      {item.focus}
                    </div>
                    <div className="text-sm mt-1">
                      <span className="text-muted">Gap vs us: </span>
                      {item.gap_vs_us}
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </>
        ) : null}
      </div>
    </>
  );
}
