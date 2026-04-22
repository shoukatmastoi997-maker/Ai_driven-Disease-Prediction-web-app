export function clamp01(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return 0;
  return Math.min(1, Math.max(0, n));
}

export function riskBand(percent) {
  const p = Number(percent);
  if (p >= 71) return "urgent";
  if (p >= 31) return "monitor";
  return "safe";
}

export function riskBandLabel(band) {
  if (band === "urgent") return "Urgent Consultation";
  if (band === "monitor") return "Monitor";
  return "Safe";
}

export function riskBandStyles(band) {
  if (band === "urgent") return "bg-rose-500/15 text-rose-800 border-rose-200/60";
  if (band === "monitor") return "bg-amber-500/15 text-amber-800 border-amber-200/60";
  return "bg-emerald-500/15 text-emerald-800 border-emerald-200/60";
}

export function riskBandAccent(band) {
  if (band === "urgent") return "#e11d48"; // rose-600
  if (band === "monitor") return "#f59e0b"; // amber-500
  return "#10b981"; // emerald-500
}

