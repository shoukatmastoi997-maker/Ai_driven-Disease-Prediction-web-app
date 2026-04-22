import { NavLink, Route, Routes } from "react-router-dom";
import PredictPage from "./pages/PredictPage";
import ResultsPage from "./pages/ResultsPage";
import DashboardPage from "./pages/DashboardPage";

const linkClasses = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-semibold transition ${
    isActive ? "bg-cyan-700 text-white" : "text-slate-700 hover:bg-white/80"
  }`;

function App() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/75 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-cyan-600 shadow-[0_0_0_6px_rgba(8,145,178,0.15)]" />
            <h1 className="text-sm font-bold tracking-wide text-slate-800 md:text-base">
              Disease Prediction Console
            </h1>
          </div>
          <nav className="flex items-center gap-2">
            <NavLink to="/" end className={linkClasses}>
              Predict
            </NavLink>
            <NavLink to="/results" className={linkClasses}>
              Results
            </NavLink>
            <NavLink to="/dashboard" className={linkClasses}>
              Database
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6">
        <Routes>
          <Route path="/" element={<PredictPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
