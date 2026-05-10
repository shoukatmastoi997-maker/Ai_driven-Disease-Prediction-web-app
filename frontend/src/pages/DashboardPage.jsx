import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FileText, Printer, RefreshCw } from "lucide-react";
import { fetchHistoryFull, fetchReportPdf } from "../services/api";
import Skeleton from "../components/Skeleton";

function openPrintWindow(blobUrl, title = "Patient Report") {
  const win = window.open("", "_blank", "noopener,noreferrer,width=900,height=700");
  if (!win) return;
  win.document.write(`<!doctype html>
    <html>
      <head><title>${title}</title></head>
      <body style="margin:0">
        <iframe id="pdf" src="${blobUrl}" style="border:0;width:100%;height:100vh"></iframe>
        <script>
          const iframe = document.getElementById('pdf');
          iframe.addEventListener('load', () => {
            try { iframe.contentWindow.focus(); iframe.contentWindow.print(); } catch (e) {}
          });
        <\/script>
      </body>
    </html>`);
  win.document.close();
}

function DashboardPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reportUrl, setReportUrl] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const mountedRef = useRef(false);

  async function load(filters = {}) {
    setError("");
    setLoading(true);
    try {
      const historyRes = await fetchHistoryFull(500, filters);
      setHistory(historyRes || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load prediction history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!mountedRef.current) {
      mountedRef.current = true;
      load({ search: searchTerm, risk_level: riskFilter });
      return;
    }

    const timer = setTimeout(() => {
      load({ search: searchTerm, risk_level: riskFilter });
    }, 220);

    return () => clearTimeout(timer);
  }, [searchTerm, riskFilter]);

  const historyPreview = useMemo(() => history, [history]);

  async function viewAndPrintReport(row) {
    setError("");
    setReportLoading(true);
    try {
      const pdfBlob = await fetchReportPdf(row.id);
      const blobUrl = URL.createObjectURL(pdfBlob);
      setReportUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return blobUrl;
      });
      setReportTitle(`Report - ${row.name} (#${row.id})`);
      openPrintWindow(blobUrl, `Patient Report #${row.id}`);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load report PDF.");
    } finally {
      setReportLoading(false);
    }
  }

  function closeReport() {
    setReportUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return "";
    });
    setReportTitle("");
  }

  if (error) {
    return (
      <section className="card">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Patient Database</h2>
            <p className="mt-2 text-sm font-semibold text-rose-700">{error}</p>
          </div>
          <button
            type="button"
            className="btn-primary inline-flex items-center gap-2"
            onClick={() => load({ search: searchTerm, risk_level: riskFilter })}
          >
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
              <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Patient Database</h2>
              <p className="mt-1 text-sm text-slate-600">Loading prediction history…</p>
            </div>
            <Skeleton className="h-10 w-28 rounded-xl" />
          </div>
        </div>

        <div className="card">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div key={idx} className="rounded-2xl border border-white/55 bg-white/20 p-4">
                <Skeleton className="h-5 w-2/3 rounded-lg" />
                <Skeleton className="mt-3 h-4 w-1/2 rounded-lg" />
                <Skeleton className="mt-3 h-10 w-full rounded-xl" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-4">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">Patient Database</h2>
            <p className="mt-1 text-sm text-slate-600">
              Click a record to preview the PDF and open the print dialog.
            </p>
          </div>
          <button
            type="button"
            className="btn-ghost inline-flex items-center gap-2"
            onClick={() => load({ search: searchTerm, risk_level: riskFilter })}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="font-display text-lg font-semibold tracking-tight text-ink">Stored Prediction Records</h3>
            <p className="mt-1 text-sm text-slate-600">
              Showing {historyPreview.length} matching rows from SQLite.
            </p>
          </div>
          <div className="text-xs font-semibold text-slate-600">
            Tip: row hover + glass table for exhibition aesthetics.
          </div>
        </div>

<div className="mt-4 grid gap-3 md:grid-cols-[2fr_1fr]">
            <label className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Search</span>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Patient or disease name…"
                className="field rounded-3xl bg-white/80 border-white/60 placeholder:text-slate-500"
              />
            </label>

            <label className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Risk</span>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="field rounded-3xl bg-white/80 border-white/60 text-ink"
              >
                <option value="">All risks</option>
                <option value="High">High</option>
                <option value="Moderate">Moderate</option>
                <option value="Low">Low</option>
              </select>
            </label>
          </div>

          {(searchTerm || riskFilter) ? (
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-white/55 bg-white/20 px-4 py-3 text-sm text-slate-600 shadow-sm">
              <span>
                Filtering by {searchTerm ? `search “${searchTerm}”` : ""}
                {searchTerm && riskFilter ? ", " : ""}
                {riskFilter ? `${riskFilter} risk` : ""}
              </span>
              <button
                type="button"
                className="btn-ghost inline-flex items-center justify-center"
                onClick={() => {
                  setSearchTerm("");
                  setRiskFilter("");
              }}
            >
              Clear filters
            </button>
          </div>
        ) : null}

        <div className="mt-4 hidden lg:block">
          <div className="overflow-hidden rounded-3xl border border-white/55 bg-white/20">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-white/55 bg-white/25 text-left text-[11px] font-bold uppercase tracking-wide text-slate-600">
                  <th className="px-3 py-3">Date</th>
                  <th className="px-3 py-3">Name</th>
                  <th className="px-3 py-3">Age</th>
                  <th className="px-3 py-3">Gender</th>
                  <th className="px-3 py-3">Disease</th>
                  <th className="px-3 py-3">Risk</th>
                  <th className="px-3 py-3">Confidence</th>
                  <th className="px-3 py-3">Report</th>
                </tr>
              </thead>
              <motion.tbody
                variants={{ show: { transition: { staggerChildren: 0.03 } } }}
                initial="show"
                animate="show"
              >
                {historyPreview.map((row) => (
                  <motion.tr
                    key={row.id}
                    variants={{ show: { opacity: 1, y: 0 }, hidden: { opacity: 0, y: 6 } }}
                    initial="hidden"
                    animate="show"
                    className="cursor-pointer border-b border-white/40 text-slate-700 hover:bg-white/25"
                    onClick={() => viewAndPrintReport(row)}
                  >
                    <td className="px-3 py-3">{row.created_at}</td>
                    <td className="px-3 py-3 font-semibold text-ink">{row.name}</td>
                    <td className="px-3 py-3">{row.age}</td>
                    <td className="px-3 py-3">{row.gender}</td>
                    <td className="px-3 py-3">{row.predicted_disease}</td>
                    <td className="px-3 py-3">
                      <span className="rounded-full border border-white/55 bg-white/25 px-2 py-1 text-xs font-semibold">
                        {row.risk_level}
                      </span>
                    </td>
                    <td className="px-3 py-3">{(Number(row.confidence) * 100).toFixed(2)}%</td>
                    <td className="px-3 py-3">
                      <motion.button
                        type="button"
                        className="inline-flex items-center gap-2 rounded-xl border border-cyan-200/60 bg-cyan-500/10 px-3 py-2 text-xs font-bold text-cyan-900 shadow-glow-cyan"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          viewAndPrintReport(row);
                        }}
                        disabled={reportLoading}
                      >
                        <Printer className="h-4 w-4" />
                        {reportLoading ? "Loading…" : "View/Print"}
                      </motion.button>
                    </td>
                  </motion.tr>
                ))}
                {historyPreview.length === 0 ? (
                  <tr>
                    <td className="px-3 py-6 text-slate-600" colSpan={8}>
                      No stored prediction records yet.
                    </td>
                  </tr>
                ) : null}
              </motion.tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 grid gap-3 lg:hidden">
          <motion.div
            className="grid gap-3"
            variants={{ show: { transition: { staggerChildren: 0.05 } } }}
            initial="show"
            animate="show"
          >
            {historyPreview.map((row) => (
              <motion.button
                key={row.id}
                type="button"
                variants={{ show: { opacity: 1, y: 0 }, hidden: { opacity: 0, y: 10 } }}
                initial="hidden"
                animate="show"
                whileTap={{ scale: 0.99 }}
                className="w-full rounded-3xl border border-white/55 bg-white/20 p-4 text-left"
                onClick={() => viewAndPrintReport(row)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-ink">{row.name}</div>
                    <div className="mt-1 text-xs font-semibold text-slate-600">{row.created_at}</div>
                  </div>
                  <span className="rounded-full border border-white/55 bg-white/25 px-2 py-1 text-xs font-semibold text-slate-700">
                    {row.risk_level}
                  </span>
                </div>

                <div className="mt-3 grid gap-1 text-sm text-slate-700">
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-600">Disease</span>
                    <span className="font-semibold text-ink">{row.predicted_disease}</span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-600">Confidence</span>
                    <span className="font-semibold">{(Number(row.confidence) * 100).toFixed(2)}%</span>
                  </div>
                </div>

                <div className="mt-3 inline-flex items-center gap-2 rounded-2xl border border-white/55 bg-white/25 px-3 py-2 text-xs font-semibold text-slate-700">
                  <FileText className="h-4 w-4" />
                  Tap to preview PDF
                </div>
              </motion.button>
            ))}
            {historyPreview.length === 0 ? (
              <div className="rounded-3xl border border-white/55 bg-white/25 p-4 text-sm text-slate-600">
                No stored prediction records yet.
              </div>
            ) : null}
          </motion.div>
        </div>
      </div>

      <AnimatePresence>
        {reportUrl ? (
          <motion.div
            className="fixed inset-0 z-50 grid place-items-center bg-slate-900/35 p-4"
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) closeReport();
            }}
          >
            <motion.div
              className="glass w-full max-w-5xl overflow-hidden rounded-3xl"
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/50 bg-white/20 px-4 py-3">
                <h3 className="truncate font-display text-sm font-semibold tracking-tight text-ink">
                  {reportTitle || "Patient Report"}
                </h3>
                <div className="flex items-center gap-2">
                  <motion.button
                    type="button"
                    className="btn-primary inline-flex items-center gap-2"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => openPrintWindow(reportUrl, reportTitle || "Patient Report")}
                  >
                    <Printer className="h-4 w-4" />
                    Print
                  </motion.button>
                  <button type="button" className="btn-ghost" onClick={closeReport}>
                    Close
                  </button>
                </div>
              </div>
              <iframe title="Patient report" src={reportUrl} className="h-[75vh] w-full bg-white" />
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

export default DashboardPage;
