import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, CheckCircle2, ChevronLeft, ChevronRight, ClipboardList, Search } from "lucide-react";
import { fetchSymptoms, fetchTopFeatures, predictDisease } from "../services/api";
import Skeleton from "../components/Skeleton";
import SymptomPalette from "../components/SymptomPalette";

const INITIAL_PATIENT = {
  name: "",
  fname: "",
  age: "",
  gender: "",
  basic_info: ""
};

function normalize(text) {
  return String(text || "").trim().toLowerCase();
}

function PredictPage() {
  const navigate = useNavigate();
  const [patient, setPatient] = useState(INITIAL_PATIENT);
  const [allSymptoms, setAllSymptoms] = useState([]);
  const [featuredSymptoms, setFeaturedSymptoms] = useState([]);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [desktop, setDesktop] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [symptomLoading, setSymptomLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [symptomRes, featureRes] = await Promise.all([fetchSymptoms(), fetchTopFeatures()]);
        setAllSymptoms(symptomRes.symptoms || []);
        setFeaturedSymptoms((featureRes.top_features || []).map((x) => x.symptom));
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to load symptom list.");
      } finally {
        setSymptomLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setDesktop(Boolean(mql.matches));
    onChange();
    mql.addEventListener?.("change", onChange);
    return () => mql.removeEventListener?.("change", onChange);
  }, []);

  useEffect(() => {
    function onKeyDown(event) {
      const isMac = navigator.platform.toLowerCase().includes("mac");
      const openHotkey = (isMac ? event.metaKey : event.ctrlKey) && event.key.toLowerCase() === "k";
      if (openHotkey) {
        event.preventDefault();
        setPaletteOpen(true);
      }
      if (event.key === "Escape") setPaletteOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function onPatientChange(event) {
    const { name, value } = event.target;
    setPatient((prev) => ({ ...prev, [name]: value }));
  }

  function addSymptom(symptom) {
    const cleaned = normalize(symptom);
    if (!cleaned || selectedSymptoms.includes(cleaned) || !allSymptoms.includes(cleaned)) {
      return;
    }
    setSelectedSymptoms((prev) => [...prev, cleaned]);
  }

  function removeSymptom(symptom) {
    setSelectedSymptoms((prev) => prev.filter((item) => item !== symptom));
  }

  function toggleSymptom(symptom) {
    const cleaned = normalize(symptom);
    if (!cleaned) return;
    if (selectedSymptoms.includes(cleaned)) removeSymptom(cleaned);
    else addSymptom(cleaned);
  }

  const canProceed = patient.name && patient.fname && patient.age && patient.gender;
  const showPatient = desktop || step === 1;
  const showSymptoms = desktop || step === 2;

  async function submitPrediction(event) {
    event.preventDefault();
    setError("");
    if (!selectedSymptoms.length) {
      setError("Please select at least one symptom.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...patient,
        age: Number(patient.age),
        symptoms: selectedSymptoms
      };
      const response = await predictDisease(payload);
      localStorage.setItem("latestPrediction", JSON.stringify(response));
      navigate("/results", { state: { result: response } });
    } catch (err) {
      const message = err?.response?.data?.detail;
      if (typeof message === "string") {
        setError(message);
      } else if (message?.message) {
        setError(`${message.message} ${message.invalid_symptoms?.join(", ") || ""}`);
      } else {
        setError("Prediction failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="grid gap-4">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold tracking-tight text-ink">
              Patient Intake & Symptom Selection
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Glassmorphism UI with smart search, animated chips, and premium loading states.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-ghost inline-flex items-center gap-2"
              onClick={() => setPaletteOpen(true)}
            >
              <Search className="h-4 w-4" />
              Search Symptoms
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 rounded-2xl border border-white/50 bg-white/20 p-2 text-xs font-semibold text-slate-700 sm:inline-grid sm:grid-cols-2">
          <button
            type="button"
            className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2 transition ${
              step === 1 ? "bg-white/45 shadow-glow-cyan" : "hover:bg-white/35"
            }`}
            onClick={() => setStep(1)}
          >
            <ClipboardList className="h-4 w-4" />
            Patient
          </button>
          <button
            type="button"
            className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2 transition ${
              step === 2 ? "bg-white/45 shadow-glow-cyan" : "hover:bg-white/35"
            }`}
            onClick={() => setStep(2)}
          >
            <CheckCircle2 className="h-4 w-4" />
            Symptoms
          </button>
        </div>
      </div>

      <form className="grid grid-cols-1 gap-4 lg:grid-cols-2" onSubmit={submitPrediction}>
        <AnimatePresence initial={false}>
          {showPatient ? (
            <motion.div
              key="patient"
              className="card"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.22 }}
            >
              <h3 className="font-display text-lg font-semibold tracking-tight text-ink">Patient Intake</h3>
              <p className="mt-1 text-sm text-slate-600">Add details used in the PDF report and database.</p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1 text-sm font-semibold text-slate-700">
                  Name
                  <input className="field" required name="name" value={patient.name} onChange={onPatientChange} />
                </label>
                <label className="grid gap-1 text-sm font-semibold text-slate-700">
                  Father Name
                  <input className="field" required name="fname" value={patient.fname} onChange={onPatientChange} />
                </label>
                <label className="grid gap-1 text-sm font-semibold text-slate-700">
                  Age
                  <input
                    className="field"
                    required
                    type="number"
                    min="0"
                    max="120"
                    name="age"
                    value={patient.age}
                    onChange={onPatientChange}
                  />
                </label>
                <label className="grid gap-1 text-sm font-semibold text-slate-700">
                  Gender
                  <select className="field" required name="gender" value={patient.gender} onChange={onPatientChange}>
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </label>
                <label className="grid gap-1 text-sm font-semibold text-slate-700 sm:col-span-2">
                  Basic Info (for PDF)
                  <textarea
                    className="field"
                    name="basic_info"
                    value={patient.basic_info}
                    onChange={onPatientChange}
                    rows={4}
                    placeholder="History, blood group, clinical notes…"
                  />
                </label>
              </div>

              <div className="mt-4 flex items-center justify-between gap-3">
                <div className="text-xs text-slate-600">
                  Tip: press <span className="rounded-md bg-white/40 px-1.5 py-0.5 font-semibold">Ctrl + K</span> to
                  search symptoms.
                </div>
                <motion.button
                  type="button"
                  className="btn-primary inline-flex items-center gap-2"
                  whileHover={{ scale: 1.02, boxShadow: "0 0 0 1px rgba(6,182,212,0.45), 0 0 26px rgba(6,182,212,0.25)" }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setStep(2)}
                  disabled={!canProceed || desktop}
                >
                  Next <ChevronRight className="h-4 w-4" />
                </motion.button>
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>

        <AnimatePresence initial={false}>
          {showSymptoms ? (
            <motion.div
              key="symptoms"
              className="card"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.22 }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-display text-lg font-semibold tracking-tight text-ink">Symptoms</h3>
                  <p className="mt-1 text-sm text-slate-600">Select model-valid symptoms (no duplicates).</p>
                </div>
                <motion.button
                  type="button"
                  className="btn-ghost inline-flex items-center gap-2"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setPaletteOpen(true)}
                >
                  <Search className="h-4 w-4" />
                  Search
                </motion.button>
              </div>

              <div className="mt-4">
                <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Selected</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedSymptoms.length ? (
                    selectedSymptoms.map((symptom) => (
                      <motion.button
                        key={symptom}
                        type="button"
                        className="chip chip-selected"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => removeSymptom(symptom)}
                        title="Click to remove"
                      >
                        {symptom}
                      </motion.button>
                    ))
                  ) : (
                    <div className="rounded-2xl border border-white/55 bg-white/25 p-3 text-sm text-slate-600">
                      No symptoms selected yet. Use the search palette to add symptoms quickly.
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Top Symptoms</div>
                  {symptomLoading ? (
                    <div className="text-xs text-slate-500">Loading…</div>
                  ) : (
                    <div className="text-xs text-slate-500">{featuredSymptoms.slice(0, 20).length} items</div>
                  )}
                </div>

                {symptomLoading ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Array.from({ length: 14 }).map((_, idx) => (
                      <Skeleton key={idx} className="h-8 w-[120px] rounded-full" />
                    ))}
                  </div>
                ) : (
                  <motion.div
                    className="mt-2 flex flex-wrap gap-2"
                    variants={{
                      show: { transition: { staggerChildren: 0.03, delayChildren: 0.04 } }
                    }}
                    initial="show"
                    animate="show"
                  >
                    {featuredSymptoms.slice(0, 20).map((symptom) => {
                      const cleaned = normalize(symptom);
                      const isSelected = selectedSymptoms.includes(cleaned);
                      return (
                        <motion.button
                          key={symptom}
                          type="button"
                          variants={{ show: { opacity: 1, y: 0 }, hidden: { opacity: 0, y: 6 } }}
                          initial="hidden"
                          animate="show"
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className={`chip ${isSelected ? "chip-selected" : ""}`}
                          onClick={() => toggleSymptom(symptom)}
                        >
                          {symptom}
                        </motion.button>
                      );
                    })}
                  </motion.div>
                )}
              </div>

              <div className="mt-5 flex items-center justify-between gap-3">
                <motion.button
                  type="button"
                  className="btn-ghost inline-flex items-center gap-2"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setStep(1)}
                  disabled={desktop}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </motion.button>

                <motion.button
                  disabled={loading}
                  className="btn-primary inline-flex items-center gap-2"
                  type="submit"
                  whileHover={{ scale: 1.02, boxShadow: "0 0 0 1px rgba(6,182,212,0.45), 0 0 26px rgba(6,182,212,0.25)" }}
                  whileTap={{ scale: 0.98 }}
                >
                  {loading ? "Predicting…" : "Predict Disease"}
                  <ArrowRight className="h-4 w-4" />
                </motion.button>
              </div>

              {error ? <p className="mt-3 text-sm font-semibold text-rose-700">{error}</p> : null}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </form>

      <SymptomPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        symptoms={allSymptoms}
        featured={featuredSymptoms}
        selected={selectedSymptoms}
        onSelect={(s) => toggleSymptom(s)}
      />

      <AnimatePresence>
        {loading ? (
          <motion.div
            className="fixed inset-0 z-50 grid place-items-center bg-slate-900/25 p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="glass w-full max-w-xl rounded-3xl p-5"
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-display text-lg font-semibold tracking-tight text-ink">Running model…</div>
                  <div className="mt-1 text-sm text-slate-600">Generating prediction, XAI, and PDF report.</div>
                </div>
                <div className="h-10 w-10 rounded-2xl bg-cyan-500/15 shadow-glow-cyan animate-floaty" />
              </div>
              <div className="mt-4 grid gap-3">
                <Skeleton className="h-5 w-3/4 rounded-lg" />
                <Skeleton className="h-5 w-2/3 rounded-lg" />
                <Skeleton className="h-24 w-full rounded-2xl" />
                <Skeleton className="h-10 w-full rounded-xl" />
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

export default PredictPage;
