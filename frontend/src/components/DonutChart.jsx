import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const palette = ["#06b6d4", "#0ea5e9", "#22c55e", "#f59e0b", "#e11d48"];

function clampPercent(value) {
  const n = Number(value);
  if (Number.isNaN(n) || !Number.isFinite(n)) return 0;
  return Math.max(0, n);
}

export default function DonutChart({ items = [], title = "Top Predictions" }) {
  const [active, setActive] = useState(null);
  const data = useMemo(() => {
    const normalized = (items || []).slice(0, 5).map((x) => ({
      label: x.disease,
      value: clampPercent(x.percent ?? x.value ?? 0)
    }));
    const total = normalized.reduce((sum, x) => sum + x.value, 0) || 1;
    return normalized.map((x, i) => ({ ...x, frac: x.value / total, color: palette[i % palette.length] }));
  }, [items]);

  const size = 260;
  const stroke = 18;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-display text-lg font-semibold tracking-tight text-ink">{title}</h3>
        <div className="text-xs font-semibold text-slate-600">Semi-transparent donut</div>
      </div>

      <div className="grid items-center gap-6 lg:grid-cols-[auto,1fr]">
        <div className="relative mx-auto w-fit">
          <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              stroke="rgba(255,255,255,0.45)"
              strokeWidth={stroke}
              fill="none"
            />
            {data.map((slice, idx) => {
              const dash = c * slice.frac;
              const dashArray = `${dash} ${c - dash}`;
              const dashOffset = -offset;
              offset += dash;
              return (
                <motion.circle
                  key={slice.label}
                  cx={size / 2}
                  cy={size / 2}
                  r={r}
                  stroke={slice.color}
                  strokeOpacity={0.78}
                  strokeWidth={stroke}
                  strokeLinecap="round"
                  fill="none"
                  strokeDasharray={dashArray}
                  strokeDashoffset={dashOffset}
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: -90 }}
                  transition={{ delay: idx * 0.06, duration: 0.5 }}
                  onMouseEnter={() => setActive(slice)}
                  onMouseLeave={() => setActive(null)}
                  style={{ transformOrigin: "50% 50%" }}
                />
              );
            })}
          </svg>
          <div className="pointer-events-none absolute inset-0 grid place-items-center">
            <div className="rounded-2xl border border-white/45 bg-white/30 px-4 py-2 text-center shadow-soft backdrop-blur">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">Most likely</div>
              <div className="font-display text-sm font-semibold text-ink">{data[0]?.label || "n/a"}</div>
            </div>
          </div>

          <AnimatePresence>
            {active ? (
              <motion.div
                className="pointer-events-none absolute left-1/2 top-4 -translate-x-1/2 rounded-2xl border border-white/45 bg-white/45 px-3 py-2 text-xs font-semibold text-slate-700 shadow-soft backdrop-blur"
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
              >
                {active.label}: {active.value.toFixed(2)}%
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        <div className="grid gap-2">
          {data.map((slice) => (
            <button
              key={slice.label}
              type="button"
              className="flex items-center justify-between gap-3 rounded-2xl border border-white/55 bg-white/25 px-3 py-2 text-left text-sm font-semibold text-slate-700 transition hover:bg-white/40"
              onMouseEnter={() => setActive(slice)}
              onMouseLeave={() => setActive(null)}
            >
              <span className="inline-flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: slice.color }} />
                {slice.label}
              </span>
              <span className="text-xs font-bold text-slate-600">{slice.value.toFixed(2)}%</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

