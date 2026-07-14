"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Download, CheckCircle2, Loader2 } from "lucide-react";
import { executiveSummary } from "./data";

export default function ExecutiveSummaryCard() {
  const [status, setStatus] = useState<"idle" | "loading" | "done">("idle");

  function handleDownload() {
    if (status !== "idle") return;
    setStatus("loading");
    setTimeout(() => setStatus("done"), 1400);
    setTimeout(() => setStatus("idle"), 3200);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative overflow-hidden rounded-3xl bg-ink p-6 sm:p-8"
    >
      <div className="absolute top-0 right-0 w-80 h-80 bg-lime/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-royal/20 rounded-full blur-3xl" />

      <div className="relative z-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-lime/15 flex items-center justify-center shrink-0">
              <FileText size={20} className="text-lime" />
            </div>
            <div>
              <p className="text-xs font-semibold text-lime uppercase tracking-widest">Executive Summary</p>
              <p className="text-xs text-white/40 mt-0.5">Trailing 12 months · Aug 2025 – Jul 2026</p>
            </div>
          </div>

          <button
            onClick={handleDownload}
            disabled={status !== "idle"}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-lime text-ink text-xs font-semibold hover:bg-lime/90 transition-colors disabled:opacity-80"
          >
            {status === "idle" && (
              <>
                <Download size={14} />
                Download PDF
              </>
            )}
            {status === "loading" && (
              <>
                <Loader2 size={14} className="animate-spin" />
                Generating report…
              </>
            )}
            {status === "done" && (
              <>
                <CheckCircle2 size={14} />
                Downloaded
              </>
            )}
          </button>
        </div>

        <ul className="mt-6 grid sm:grid-cols-2 gap-x-8 gap-y-3">
          {executiveSummary.map((line, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-white/70 leading-relaxed">
              <span className="w-1.5 h-1.5 rounded-full bg-lime mt-1.5 shrink-0" />
              {line}
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
