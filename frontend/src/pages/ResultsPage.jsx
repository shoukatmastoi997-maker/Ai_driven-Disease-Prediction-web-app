import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { fetchReportPdf, reportUrl } from "../services/api";
import DonutChart from "../components/DonutChart";
import RiskBadge from "../components/RiskBadge";
import RiskGauge from "../components/RiskGauge";
import XaiBars from "../components/XaiBars";
import Skeleton from "../components/Skeleton";

function confidencePercent(result) {
  const c = Number(result?.confidence ?? 0);
  return Math.max(0, Math.min(100, c * 100));
}

function ResultsPage() {
  const location = useLocation();
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const fallback = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("latestPrediction") || "null");
    } catch {
      return null;
    }
  }, []);
  const result = location.state?.result || fallback;

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  if (!result) {
    return (
      <section className="card">
        <h2 className="font-display text-xl font-semibold tracking-tight text-ink">No prediction yet</h2>
        <p className="mt-1 text-sm text-slate-600">Submit patient details on the Predict page to see results.</p>
        <Link to="/" className="btn-primary mt-3 inline-flex">
          Go to Predict
        </Link>
      </section>
    );
  }

  const topPredictions = result.top_predictions || [];
  const xai = result.xai?.top_contributors || [];
  const percent = confidencePercent(result);
  const recordId = result.record_id ?? result.id;

  async function generatePreview() {
    if (!recordId) {
      setPreviewError("Cannot generate PDF: record ID is missing.");
      return;
    }

    setPreviewError("");
    setPreviewLoading(true);
    try {
      const pdfBlob = await fetchReportPdf(recordId);
      const blobUrl = URL.createObjectURL(pdfBlob);
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return blobUrl;
      });
    } catch (err) {
      setPreviewError(err?.response?.data?.detail || "Failed to generate PDF preview.");
    } finally {
      setPreviewLoading(false);
    }
  }

  function clearPreview() {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return "";
    });
    setPreviewError("");
  }

  return (
    <section className="grid gap-4">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Prediction Outcome</h2>
            <p className="mt-2 text-sm text-slate-700">
              Predicted Disease: <span className="font-semibold text-ink">{result.prediction}</span>
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <RiskBadge percent={percent} />
              <span className="rounded-full border border-white/55 bg-white/20 px-3 py-1 text-sm font-semibold text-slate-700">
                Model Risk Level: {result.risk_level}
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-600">{result.risk_guidance}</p>
            <p className="mt-1 text-sm text-slate-600">
              Patient: {result.patient.name} ({result.patient.age}, {result.patient.gender})
            </p>

            <div className="mt-4 grid gap-2 sm:flex sm:flex-wrap sm:items-center">
              <a
                href={recordId ? reportUrl(recordId) : "#"}
                target="_blank"
                rel="noreferrer"
                className="btn-primary inline-flex items-center justify-center"
                onClick={(e) => {
                  if (!recordId) {
                    e.preventDefault();
                  }
                }}
              >
                Download PDF Report
              </a>
              <Link to="/dashboard" className="btn-ghost inline-flex items-center justify-center">
                View Database
              </Link>
            </div>

            <div className="mt-4">
              <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-600">
                <span>Risk level progress</span>
                <span>{percent.toFixed(2)}%</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-white/40">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(0, Math.min(100, percent))}%` }}
                  transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
            </div>
          </div>

          <div className="w-full max-w-[320px] rounded-3xl border border-white/55 bg-white/20 p-3 sm:w-auto">
            <RiskGauge percent={percent} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <DonutChart items={topPredictions} title="Top-5 Predictions" />
        </div>

        <div className="card">
          <XaiBars items={xai} method={result.xai?.method || "n/a"} />
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-lg font-semibold tracking-tight text-ink">PDF Preview</h3>
            <p className="mt-1 text-sm text-slate-600">
              Visual confirmation
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="btn-ghost inline-flex"
              onClick={clearPreview}
              disabled={!previewUrl || previewLoading}
            >
              Clear
            </button>
            <button type="button" className="btn-primary inline-flex" onClick={generatePreview} disabled={previewLoading}>
              {previewLoading ? "Generating…" : "Generate Preview"}
            </button>
            <a
              href={recordId ? reportUrl(recordId) : "#"}
              target="_blank"
              rel="noreferrer"
              className="btn-ghost inline-flex"
              onClick={(e) => {
                if (!recordId) {
                  e.preventDefault();
                }
              }}
            >
              Open PDF
            </a>
          </div>
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-white/55 bg-white/20">
          {previewUrl ? (
            <iframe title="Report preview" src={previewUrl} className="h-[260px] w-full bg-white" />
          ) : (
            <div className="p-4">
              <Skeleton className="h-[228px] w-full rounded-2xl" />
              <div className="mt-3 text-sm font-semibold text-slate-600">
                Preview is optional (prevents auto-download on page load).
              </div>
              {previewError ? <div className="mt-2 text-sm font-semibold text-rose-700">{previewError}</div> : null}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default ResultsPage;
