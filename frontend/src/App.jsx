import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import AppShell from "./components/AppShell";
import PageTransition from "./components/PageTransition";
import PredictPage from "./pages/PredictPage";
import ResultsPage from "./pages/ResultsPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  const location = useLocation();
  return (
    <AppShell>
      <AnimatePresence mode="wait" initial={false}>
        <PageTransition key={location.pathname}>
          <Routes location={location}>
            <Route path="/" element={<PredictPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </PageTransition>
      </AnimatePresence>
    </AppShell>
  );
}

export default App;
