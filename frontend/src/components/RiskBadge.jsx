import { riskBand, riskBandLabel, riskBandStyles } from "./risk";

export default function RiskBadge({ percent }) {
  const band = riskBand(percent);
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold ${riskBandStyles(
        band
      )}`}
      title={riskBandLabel(band)}
    >
      Risk: {riskBandLabel(band)} ({Number(percent).toFixed(2)}%)
    </span>
  );
}

