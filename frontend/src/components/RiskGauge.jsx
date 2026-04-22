import { motion } from "framer-motion";
import { clamp01, riskBand, riskBandAccent, riskBandLabel } from "./risk";

export default function RiskGauge({ percent = 0 }) {
  const p = Number(percent);
  const t = clamp01(p / 100);
  const band = riskBand(p);
  const accent = riskBandAccent(band);

  const size = 220;
  const stroke = 18;
  const r = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = Math.PI * r;
  const dash = circumference;
  const dashOffset = dash * (1 - t);

  return (
    <div className="grid place-items-center">
      <svg width={size} height={size * 0.62} viewBox={`0 0 ${size} ${size * 0.62}`} className="overflow-visible">
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="rgba(15, 23, 42, 0.10)"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        <motion.path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={accent}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={dash}
          strokeDashoffset={dashOffset}
          initial={{ strokeDashoffset: dash }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>

      <div className="-mt-10 text-center">
        <div className="font-display text-2xl font-semibold tracking-tight text-ink">{p.toFixed(0)}%</div>
        <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
          {riskBandLabel(band)}
        </div>
      </div>
    </div>
  );
}

