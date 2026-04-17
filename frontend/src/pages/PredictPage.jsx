import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchSymptoms, fetchTopFeatures, predictDisease } from "../services/api";

const INITIAL_PATIENT = {
  name: "",
  fname: "",
  age: "",
  gender: "",
  basic_info: ""
};

function PredictPage() {
  const navigate = useNavigate();
  const [patient, setPatient] = useState(INITIAL_PATIENT);
  const [allSymptoms, setAllSymptoms] = useState([]);
  const [featuredSymptoms, setFeaturedSymptoms] = useState([]);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [newSymptom, setNewSymptom] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [symptomRes, featureRes] = await Promise.all([fetchSymptoms(), fetchTopFeatures()]);
        setAllSymptoms(symptomRes.symptoms || []);
        setFeaturedSymptoms((featureRes.top_features || []).map((x) => x.symptom));
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to load symptom list.");
      }
    }
    load();
  }, []);

  const availableOptions = useMemo(
    () => allSymptoms.filter((symptom) => !selectedSymptoms.includes(symptom)),
    [allSymptoms, selectedSymptoms]
  );

  function onPatientChange(event) {
    const { name, value } = event.target;
    setPatient((prev) => ({ ...prev, [name]: value }));
  }

  function addSymptom(symptom) {
    const cleaned = String(symptom).trim().toLowerCase();
    if (!cleaned || selectedSymptoms.includes(cleaned) || !allSymptoms.includes(cleaned)) {
      return;
    }
    setSelectedSymptoms((prev) => [...prev, cleaned]);
    setNewSymptom("");
  }

  function removeSymptom(symptom) {
    setSelectedSymptoms((prev) => prev.filter((item) => item !== symptom));
  }

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
    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="card">
        <h2 className="text-xl font-bold text-slate-800">Patient Intake</h2>
        <p className="mt-1 text-sm text-slate-600">
          Enter patient details and select valid symptoms from the trained model schema.
        </p>

        <form className="mt-4 grid gap-3" onSubmit={submitPrediction}>
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
          <label className="grid gap-1 text-sm font-semibold text-slate-700">
            Basic Info (for PDF)
            <textarea
              className="field"
              name="basic_info"
              value={patient.basic_info}
              onChange={onPatientChange}
              rows={3}
              placeholder="History, blood group, clinical notes..."
            />
          </label>

          <button disabled={loading} className="btn-primary mt-1" type="submit">
            {loading ? "Predicting..." : "Predict Disease"}
          </button>
          {error ? <p className="text-sm font-semibold text-rose-700">{error}</p> : null}
        </form>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold text-slate-800">Dynamic Symptom Selection</h2>
        <p className="mt-1 text-sm text-slate-600">No duplicates allowed. Only model-valid symptoms can be added.</p>

        <div className="mt-4 flex gap-2">
          <select className="field" value={newSymptom} onChange={(e) => setNewSymptom(e.target.value)}>
            <option value="">Select symptom</option>
            {availableOptions.map((symptom) => (
              <option key={symptom} value={symptom}>
                {symptom}
              </option>
            ))}
          </select>
          <button type="button" className="btn-primary whitespace-nowrap" onClick={() => addSymptom(newSymptom)}>
            Add
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {selectedSymptoms.map((symptom) => (
            <button key={symptom} type="button" className="chip" onClick={() => removeSymptom(symptom)}>
              {symptom} x
            </button>
          ))}
        </div>

        <h3 className="mt-4 text-sm font-bold uppercase tracking-wide text-slate-500">Top Symptoms</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {featuredSymptoms.slice(0, 20).map((symptom) => (
            <button
              key={symptom}
              type="button"
              className="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 text-sm text-cyan-700 transition hover:border-cyan-500"
              onClick={() => addSymptom(symptom)}
            >
              {symptom}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PredictPage;
