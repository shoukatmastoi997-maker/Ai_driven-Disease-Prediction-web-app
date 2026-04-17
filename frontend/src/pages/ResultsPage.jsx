import { useMemo } from "react";
import Plot from "react-plotly.js";
import { Link, useLocation } from "react-router-dom";
import { reportUrl } from "../services/api";

function riskClassNames(level) {
  if (level === "High") return "bg-rose-100 text-rose-700";
  if (level === "Moderate") return "bg-amber-100 text-amber-700";
  return "bg-emerald-100 text-emerald-700";
}

function ResultsPage() {
  const location = useLocation();
  const fallback = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("latestPrediction") || "null");
    } catch {
      return null;
    }
  }, []);
  const result = location.state?.result || fallback;

  if (!result) {
    return (
      <section className="card">
        <h2 className="text-xl font-bold text-slate-800">No prediction yet</h2>
        <p className="mt-1 text-sm text-slate-600">Submit patient details on the Predict page to see results.</p>
        <Link to="/" className="btn-primary mt-3 inline-flex">
          Go to Predict
        </Link>
      </section>
    );
  }

  const labels = (result.top_predictions || []).map((item) => item.disease);
  const values = (result.top_predictions || []).map((item) => Number((item.percent || 0).toFixed(2)));

  const xai = result.xai?.top_contributors || [];

  return (
    <section className="grid gap-4">
      <div className="card">
        <h2 className="text-xl font-bold text-slate-800">Prediction Outcome</h2>
        <p className="mt-2 text-slate-700">
          Predicted Disease: <strong>{result.prediction}</strong>
        </p>
        <p
          className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${riskClassNames(
            result.risk_level
          )}`}
        >
          Risk: {result.risk_level} ({(result.confidence * 100).toFixed(2)}%)
        </p>
        <p className="mt-2 text-sm text-slate-600">{result.risk_guidance}</p>
        <p className="mt-1 text-sm text-slate-600">
          Patient: {result.patient.name} ({result.patient.age}, {result.patient.gender})
        </p>
        <a href={reportUrl(result.record_id)} target="_blank" rel="noreferrer" className="btn-primary mt-3 inline-flex">
          Download PDF Report
        </a>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Top-5 Predictions (Plotly Pie)</h3>
          <Plot
            data={[
              {
                labels,
                values,
                type: "pie",
                hole: 0.35,
                textinfo: "label+percent"
              }
            ]}
            layout={{
              autosize: true,
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: "#16223a" }
            }}
            useResizeHandler
            style={{ width: "100%", height: "360px" }}
          />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Explainable AI (Top Contributors)</h3>
          <p className="mt-1 text-sm text-slate-600">Method: {result.xai?.method || "n/a"}</p>
          <Plot
            data={[
              {
                x: xai.map((item) => item.abs_contribution?.toFixed(4)),
                y: xai.map((item) => item.symptom),
                type: "bar",
                orientation: "h",
                marker: { color: "#0f8b8d" }
              }
            ]}
            layout={{
              margin: { l: 180, r: 20, t: 20, b: 40 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: "#16223a" }
            }}
            useResizeHandler
            style={{ width: "100%", height: "360px" }}
          />
        </div>
      </div>
    </section>
  );
}

export default ResultsPage;
