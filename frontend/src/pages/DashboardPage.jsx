import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { fetchAnalytics, fetchHistoryFull } from "../services/api";

function DashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [analyticsRes, historyRes] = await Promise.all([fetchAnalytics(), fetchHistoryFull(100)]);
        setAnalytics(analyticsRes);
        setHistory(historyRes || []);
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to load analytics.");
      }
    }
    load();
  }, []);

  const historyPreview = useMemo(() => history.slice(0, 20), [history]);

  if (error) {
    return (
      <section className="card">
        <h2 className="text-xl font-bold text-slate-800">Dashboard</h2>
        <p className="mt-2 text-sm font-semibold text-rose-700">{error}</p>
      </section>
    );
  }

  if (!analytics) {
    return (
      <section className="card">
        <h2 className="text-xl font-bold text-slate-800">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-600">Loading analytics...</p>
      </section>
    );
  }

  const disease = analytics.disease_frequency || [];
  const symptoms = analytics.symptom_occurrence || [];
  const risks = analytics.risk_distribution || [];
  const progression = analytics.severity_progression || [];
  const topDisease = analytics.top_disease;
  const topDiseaseTrend = analytics.top_disease_trend || [];

  return (
    <section className="grid gap-4">
      <div className="card">
        <h2 className="text-xl font-bold text-slate-800">Dashboard Analytics</h2>
        <p className="mt-1 text-sm text-slate-600">
          Disease frequency, symptom occurrence, risk distribution, severity progression, and stored prediction records.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card">
          <p className="text-xs uppercase tracking-wider text-slate-500">Total Stored Predictions</p>
          <p className="mt-2 text-3xl font-bold text-cyan-700">{analytics.total_predictions ?? 0}</p>
        </div>
        <div className="card md:col-span-2">
          <p className="text-xs uppercase tracking-wider text-slate-500">Current Top Disease (Stored Data)</p>
          <p className="mt-2 text-2xl font-bold text-slate-800">{topDisease?.disease || "N/A"}</p>
          <p className="mt-1 text-sm text-slate-600">Count: {topDisease?.count ?? 0}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Disease Frequency</h3>
          <Plot
            data={[
              {
                x: disease.slice(0, 20).map((d) => d.disease),
                y: disease.slice(0, 20).map((d) => d.count),
                type: "bar",
                marker: { color: "#2563eb" }
              }
            ]}
            layout={{
              margin: { l: 50, r: 20, t: 20, b: 120 },
              xaxis: { tickangle: -35 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent"
            }}
            useResizeHandler
            style={{ width: "100%", height: "340px" }}
          />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Risk Distribution</h3>
          <Plot
            data={[
              {
                labels: risks.map((r) => r.risk_level),
                values: risks.map((r) => r.count),
                type: "pie",
                marker: { colors: ["#e11d48", "#f59e0b", "#10b981"] }
              }
            ]}
            layout={{
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent"
            }}
            useResizeHandler
            style={{ width: "100%", height: "340px" }}
          />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Top Symptom Occurrence</h3>
          <Plot
            data={[
              {
                x: symptoms.slice(0, 15).map((s) => s.count),
                y: symptoms.slice(0, 15).map((s) => s.symptom),
                type: "bar",
                orientation: "h",
                marker: { color: "#0f766e" }
              }
            ]}
            layout={{
              margin: { l: 180, r: 20, t: 20, b: 40 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent"
            }}
            useResizeHandler
            style={{ width: "100%", height: "340px" }}
          />
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-slate-800">Severity Progression Over Time</h3>
          <Plot
            data={[
              {
                x: progression.map((p) => p.date),
                y: progression.map((p) => p.high),
                name: "High",
                type: "scatter",
                mode: "lines+markers",
                line: { color: "#e11d48" }
              },
              {
                x: progression.map((p) => p.date),
                y: progression.map((p) => p.moderate),
                name: "Moderate",
                type: "scatter",
                mode: "lines+markers",
                line: { color: "#d97706" }
              },
              {
                x: progression.map((p) => p.date),
                y: progression.map((p) => p.low),
                name: "Low",
                type: "scatter",
                mode: "lines+markers",
                line: { color: "#059669" }
              }
            ]}
            layout={{
              margin: { l: 50, r: 20, t: 20, b: 50 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent"
            }}
            useResizeHandler
            style={{ width: "100%", height: "340px" }}
          />
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-bold text-slate-800">Top Disease Trend (Stored Data)</h3>
        <Plot
          data={[
            {
              x: topDiseaseTrend.map((d) => d.date),
              y: topDiseaseTrend.map((d) => d.count),
              type: "scatter",
              mode: "lines+markers",
              marker: { color: "#0891b2" },
              line: { color: "#0891b2" },
              name: topDisease?.disease || "Top disease"
            }
          ]}
          layout={{
            margin: { l: 50, r: 20, t: 20, b: 50 },
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent"
          }}
          useResizeHandler
          style={{ width: "100%", height: "320px" }}
        />
      </div>

      <div className="card">
        <h3 className="text-lg font-bold text-slate-800">Stored Prediction Records</h3>
        <p className="mt-1 text-sm text-slate-600">Showing latest {historyPreview.length} rows from SQLite.</p>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-2 py-2">Date</th>
                <th className="px-2 py-2">Name</th>
                <th className="px-2 py-2">Age</th>
                <th className="px-2 py-2">Gender</th>
                <th className="px-2 py-2">Disease</th>
                <th className="px-2 py-2">Risk</th>
                <th className="px-2 py-2">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {historyPreview.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 text-slate-700">
                  <td className="px-2 py-2">{row.created_at}</td>
                  <td className="px-2 py-2">{row.name}</td>
                  <td className="px-2 py-2">{row.age}</td>
                  <td className="px-2 py-2">{row.gender}</td>
                  <td className="px-2 py-2">{row.predicted_disease}</td>
                  <td className="px-2 py-2">{row.risk_level}</td>
                  <td className="px-2 py-2">{(Number(row.confidence) * 100).toFixed(2)}%</td>
                </tr>
              ))}
              {historyPreview.length === 0 ? (
                <tr>
                  <td className="px-2 py-3 text-slate-500" colSpan={7}>
                    No stored prediction records yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default DashboardPage;
