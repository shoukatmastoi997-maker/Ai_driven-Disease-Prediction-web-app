import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Search, X } from "lucide-react";

function normalize(text) {
  return String(text || "").trim().toLowerCase();
}

export default function SymptomPalette({
  open,
  onClose,
  symptoms = [],
  featured = [],
  selected = [],
  onSelect
}) {
  const inputRef = useRef(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => inputRef.current?.focus(), 0);
    return () => clearTimeout(t);
  }, [open]);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const filtered = useMemo(() => {
    const q = normalize(query);
    if (!q) return symptoms.slice(0, 50);
    return symptoms
      .filter((s) => normalize(s).includes(q))
      .slice(0, 50);
  }, [symptoms, query]);

  function onKeyDown(event) {
    if (event.key === "Escape") onClose?.();
    if (event.key === "Enter") {
      const first = filtered[0];
      if (first) onSelect?.(first);
    }
  }

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-slate-900/40 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) onClose?.();
          }}
        >
          <motion.div
            className="glass w-full max-w-2xl rounded-3xl p-4 bg-white/92 backdrop-blur-xl border-white/60 shadow-[0_30px_80px_rgba(15,23,42,0.12)]"
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.98 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/35">
                  <Search className="h-5 w-5" />
                </span>
                Smart Symptom Search
              </div>
              <button
                type="button"
                className="grid h-10 w-10 place-items-center rounded-2xl border border-white/55 bg-white/25 text-slate-700 hover:bg-white/40"
                onClick={onClose}
                aria-label="Close palette"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-3 flex items-center gap-2 rounded-2xl border border-white/60 bg-white/80 px-3 py-2 shadow-sm">
              <Search className="h-5 w-5 text-slate-500" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Type to search symptoms…"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-slate-500"
              />
              <div className="hidden items-center gap-1 text-[11px] text-slate-500 sm:flex">
                <span className="rounded-md bg-white/40 px-1.5 py-0.5 font-semibold">Esc</span>
                <span>to close</span>
              </div>
            </div>

            {featured?.length ? (
              <div className="mt-3">
                <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Top Symptoms</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {featured.slice(0, 12).map((s) => {
                    const isSelected = selected.includes(normalize(s));
                    return (
                      <button
                        key={s}
                        type="button"
                        className={`chip ${isSelected ? "chip-selected" : ""}`}
                        onClick={() => onSelect?.(s)}
                      >
                        {s}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}

            <div className="mt-4 max-h-[52vh] overflow-auto pr-1">
              <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Matches</div>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                {filtered.map((s) => {
                  const cleaned = normalize(s);
                  const isSelected = selected.includes(cleaned);
                  return (
                    <button
                      key={s}
                      type="button"
                      className={`rounded-2xl border px-3 py-2 text-left text-sm font-semibold transition ${
                        isSelected
                          ? "border-cyan-200/70 bg-cyan-500/10 text-cyan-800 shadow-glow-cyan"
                          : "border-white/55 bg-white/25 text-slate-700 hover:bg-white/40 hover:text-ink"
                      }`}
                      onClick={() => onSelect?.(s)}
                    >
                      {s}
                    </button>
                  );
                })}
                {filtered.length === 0 ? (
                  <div className="rounded-2xl border border-white/55 bg-white/25 p-3 text-sm text-slate-600 sm:col-span-2">
                    No symptoms match <span className="font-semibold text-slate-700">{query}</span>.
                  </div>
                ) : null}
              </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

