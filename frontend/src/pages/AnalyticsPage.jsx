import { useEffect, useMemo, useState } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import { RefreshCw } from "lucide-react";
import { fetchAnalytics } from "../services/api";
import Skeleton from "../components/Skeleton";

const Plot = createPlotlyComponent(Plotly);

function sanitizeLabel(value) {
  const text = String(value ?? "").trim();
  return text || "Unknown";
}

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    setLoading(true);
    try {
      const res = await fetchAnalytics();
      setData(res || null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const diseaseFrequency = useMemo(() => {
    const items = (data?.disease_frequency || [])
      .map((row) => ({
        disease: sanitizeLabel(row?.disease),
        count: Number(row?.count ?? 0)
      }))
      .filter((row) => Number.isFinite(row.count) && row.count >= 0);

    items.sort((a, b) => b.count - a.count);
    return items;
  }, [data]);

  const barTrace = useMemo(() => {
    const x = diseaseFrequency.map((d) => d.disease);
    const y = diseaseFrequency.map((d) => d.count);
    return [
      {
        type: "bar",
        x,
        y,
        marker: { color: "rgba(6,182,212,0.85)", line: { color: "rgba(14,165,233,0.65)", width: 1 } },
        text: y.map((v) => String(v)),
        textposition: "outside",
        hovertemplate: "<b>%{x}</b><br>Predictions: %{y}<extra></extra>"
      }
    ];
  }, [diseaseFrequency]);

  const barLayout = useMemo(
    () => ({
      autosize: true,
      height: 440,
      margin: { l: 54, r: 18, t: 18, b: 140 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(255,255,255,0.14)",
      xaxis: {
        tickangle: -45,
        automargin: true,
        tickfont: { size: 11, color: "#334155" }
      },
      yaxis: {
        title: { text: "Prediction Count" },
        gridcolor: "rgba(148,163,184,0.25)",
        zerolinecolor: "rgba(148,163,184,0.25)"
      },
      font: { family: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial", color: "#0f172a" }
    }),
    []
  );

  if (error) {
    return (
      <section className="card">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Analytics Overview</h2>
            <p className="mt-2 text-sm font-semibold text-rose-700">{error}</p>
          </div>
          <button type="button" className="btn-primary inline-flex items-center gap-2" onClick={load}>
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="grid gap-4">
        <div className="card">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Analytics Overview</h2>
              <p className="mt-1 text-sm text-slate-600">Loading aggregated statistics…</p>
            </div>
            <Skeleton className="h-10 w-28 rounded-xl" />
          </div>
        </div>
        <div className="card">
          <Skeleton className="h-[440px] w-full rounded-3xl" />
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-4">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Analytics Overview</h2>
            <p className="mt-1 text-sm text-slate-600">
              summaries of stored predictions for monitoring disease patterns.
            </p>
          </div>
          <button type="button" className="btn-ghost inline-flex items-center gap-2" onClick={load}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-lg font-semibold tracking-tight text-ink">Disease Frequency</h3>
            <p className="mt-1 text-sm text-slate-600">
              Counts of predicted disease classes across all stored records (sorted by frequency).
            </p>
          </div>
        </div>

        <div className="mt-4 overflow-hidden rounded-3xl border border-white/55 bg-white/20 p-3">
          {diseaseFrequency.length ? (
            <Plot
              data={barTrace}
              layout={barLayout}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          ) : (
            <div className="grid place-items-center py-14 text-sm font-semibold text-slate-600">
              No prediction history found yet.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
