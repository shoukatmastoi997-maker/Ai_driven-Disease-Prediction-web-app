import { motion } from "framer-motion";
import { Info } from "lucide-react";

function fmt(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "0.0000";
  return v.toFixed(4);
}

export default function XaiBars({ items = [], method = "n/a" }) {
  const top = items?.[0]?.symptom;
  const maxAbs = Math.max(1e-9, ...items.map((x) => Math.abs(Number(x.abs_contribution ?? x.contribution ?? 0))));

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold tracking-tight text-ink">Explainable AI (XAI)</h3>
          <p className="mt-1 text-sm text-slate-600">Method: {method}</p>
        </div>
        {top ? (
          <div className="group relative inline-flex items-center gap-2 rounded-2xl border border-white/55 bg-white/25 px-3 py-2 text-xs font-semibold text-slate-700">
            <Info className="h-4 w-4 text-slate-600" />
            Tooltip
            <div className="pointer-events-none absolute right-0 top-full mt-2 w-[260px] rounded-2xl border border-white/55 bg-white/55 p-3 text-xs font-medium text-slate-700 opacity-0 shadow-soft backdrop-blur transition group-hover:opacity-100">
              The model prioritized <span className="font-semibold text-ink">"{top}"</span> as the most significant
              indicator for this prediction.
            </div>
          </div>
        ) : null}
      </div>

      <div className="grid gap-2">
        {items.map((item, idx) => {
          const contribution = Number(item.contribution ?? 0);
          const abs = Math.abs(contribution);
          const w = Math.max(0.06, abs / maxAbs);
          const positive = contribution >= 0;
          const barClass = positive ? "bg-cyan-500/35" : "bg-rose-500/30";
          const pillClass = positive
            ? "border-cyan-200/60 bg-cyan-500/10 text-cyan-900"
            : "border-rose-200/60 bg-rose-500/10 text-rose-900";

          return (
            <div key={`${item.symptom}-${idx}`} className="grid gap-1 rounded-2xl border border-white/55 bg-white/20 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold text-ink">{item.symptom}</div>
                <div className={`rounded-full border px-2 py-0.5 text-[11px] font-bold ${pillClass}`}>
                  {positive ? "Positive" : "Negative"} · {fmt(contribution)}
                </div>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-white/40">
                <motion.div
                  className={`h-full rounded-full ${barClass}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${w * 100}%` }}
                  transition={{ delay: idx * 0.06, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
            </div>
          );
        })}
        {items.length === 0 ? (
          <div className="rounded-2xl border border-white/55 bg-white/25 p-3 text-sm text-slate-600">
            No XAI contributors available for this prediction.
          </div>
        ) : null}
      </div>
    </div>
  );
}

