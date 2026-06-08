import { NavLink } from "react-router-dom";
import { Activity, BarChart3, Database, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

const navItems = [
  { to: "/", end: true, label: "Predict", icon: Activity },
  { to: "/results", label: "Results", icon: Sparkles },
  { to: "/dashboard", label: "Dashboard", icon: Database },
  { to: "/analytics", label: "Analytics", icon: BarChart3 }
];

const navLinkClasses = ({ isActive }) =>
  [
    "group relative flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-semibold transition",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200/70",
    isActive ? "text-ink" : "text-slate-600 hover:text-ink"
  ].join(" ");

function ActivePill({ active }) {
  return (
    <motion.span
      aria-hidden
      initial={false}
      animate={
        active
          ? { opacity: 1, scale: 1 }
          : { opacity: 0, scale: 0.96 }
      }
      transition={{ duration: 0.2 }}
      className="absolute inset-0 -z-10 rounded-2xl bg-white/40 shadow-glow-cyan"
    />
  );
}

export default function AppShell({ children }) {
  return (
    <div className="relative h-screen overflow-x-hidden overflow-y-auto">
      <div className="pointer-events-none absolute inset-0 opacity-60" aria-hidden>
        <div className="absolute left-[-120px] top-[-120px] h-[340px] w-[340px] rounded-full bg-cyan-400/30 blur-3xl" />
        <div className="absolute right-[-140px] top-[40px] h-[320px] w-[320px] rounded-full bg-sky-500/25 blur-3xl" />
        <div className="absolute bottom-[-160px] left-[25%] h-[360px] w-[360px] rounded-full bg-cyan-300/25 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-7xl gap-4 px-4 py-6 lg:py-10">
        <aside className="hidden w-[270px] shrink-0 lg:block">
          <div className="glass sticky top-8 rounded-3xl p-4">
            <div className="flex items-center gap-3 px-2 py-2">
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-700 shadow-glow-cyan">
                <Activity className="h-5 w-5" />
              </span>
              <div className="leading-tight">
                <div className="font-display text-sm font-semibold tracking-wide text-ink">
                  Disease Prediction
                </div>
                <div className="text-xs text-slate-600">Health-Tech Console</div>
              </div>
            </div>

            <nav className="mt-3 grid gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClasses}>
                    {({ isActive }) => (
                      <>
                        <ActivePill active={isActive} />
                        <span className="grid h-10 w-10 place-items-center rounded-2xl border border-white/50 bg-white/25 text-slate-700 transition group-hover:bg-white/40">
                          <Icon className="h-5 w-5" />
                        </span>
                        <span>{item.label}</span>
                      </>
                    )}
                  </NavLink>
                );
              })}
            </nav>

          
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="glass sticky top-3 z-20 mb-4 rounded-3xl p-3 lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-2xl bg-cyan-500/15 text-cyan-700 shadow-glow-cyan">
                  <Activity className="h-5 w-5" />
                </span>
                <div className="leading-tight">
                  <div className="font-display text-sm font-semibold tracking-wide text-ink">
                    Disease Prediction
                  </div>
                  <div className="text-xs text-slate-600">Health-Tech Console</div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) =>
                        [
                          "grid h-11 w-11 place-items-center rounded-2xl border transition",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200/70",
                          isActive
                            ? "border-cyan-200/70 bg-white/45 text-cyan-800 shadow-glow-cyan"
                            : "border-white/55 bg-white/25 text-slate-700 hover:bg-white/40"
                        ].join(" ")
                      }
                      aria-label={item.label}
                      title={item.label}
                    >
                      <Icon className="h-5 w-5" />
                    </NavLink>
                  );
                })}
              </div>
            </div>
          </header>

          {children}
        </div>
      </div>
    </div>
  );
}
