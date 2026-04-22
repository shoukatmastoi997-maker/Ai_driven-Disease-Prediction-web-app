import { useEffect, useMemo, useState } from "react";
import { fetchHistoryFull, fetchReportPdf } from "../services/api";

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

  useEffect(() => {
    async function load() {
      try {
        const historyRes = await fetchHistoryFull(500);
        setHistory(historyRes || []);
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to load prediction history.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const historyPreview = useMemo(() => history.slice(0, 200), [history]);

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
        <h2 className="text-xl font-bold text-slate-800">Patient Database</h2>
        <p className="mt-2 text-sm font-semibold text-rose-700">{error}</p>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="card">
        <h2 className="text-xl font-bold text-slate-800">Patient Database</h2>
        <p className="mt-1 text-sm text-slate-600">Loading prediction history...</p>
      </section>
    );
  }

  return (
    <section className="grid gap-4">
      <div className="card">
        <h2 className="text-xl font-bold text-slate-800">Patient Database</h2>
        <p className="mt-1 text-sm text-slate-600">
          Click any row to display the patient report and open the print dialog.
        </p>
      </div>

      <div className="card">
        <h3 className="text-lg font-bold text-slate-800">Stored Prediction Records</h3>
        <p className="mt-1 text-sm text-slate-600">
          Showing latest {historyPreview.length} rows from SQLite.
        </p>
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
                <th className="px-2 py-2">Report</th>
              </tr>
            </thead>
            <tbody>
              {historyPreview.map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer border-b border-slate-100 text-slate-700 hover:bg-slate-50"
                  onClick={() => viewAndPrintReport(row)}
                >
                  <td className="px-2 py-2">{row.created_at}</td>
                  <td className="px-2 py-2">{row.name}</td>
                  <td className="px-2 py-2">{row.age}</td>
                  <td className="px-2 py-2">{row.gender}</td>
                  <td className="px-2 py-2">{row.predicted_disease}</td>
                  <td className="px-2 py-2">{row.risk_level}</td>
                  <td className="px-2 py-2">{(Number(row.confidence) * 100).toFixed(2)}%</td>
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      className="rounded-md border border-cyan-200 bg-cyan-50 px-2 py-1 text-xs font-semibold text-cyan-700 hover:border-cyan-400"
                      onClick={(e) => {
                        e.stopPropagation();
                        viewAndPrintReport(row);
                      }}
                      disabled={reportLoading}
                    >
                      {reportLoading ? "Loading..." : "View/Print"}
                    </button>
                  </td>
                </tr>
              ))}
              {historyPreview.length === 0 ? (
                <tr>
                  <td className="px-2 py-3 text-slate-500" colSpan={8}>
                    No stored prediction records yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      {reportUrl ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-5xl overflow-hidden rounded-xl bg-white shadow-xl">
            <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
              <h3 className="text-sm font-bold text-slate-800">{reportTitle || "Patient Report"}</h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => openPrintWindow(reportUrl, reportTitle || "Patient Report")}
                >
                  Print
                </button>
                <button type="button" className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-700" onClick={closeReport}>
                  Close
                </button>
              </div>
            </div>
            <iframe title="Patient report" src={reportUrl} className="h-[75vh] w-full" />
          </div>
        </div>
      ) : null}
    </section>
  );
}

export default DashboardPage;
