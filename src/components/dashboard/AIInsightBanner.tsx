"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";

export default function AIInsightBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative overflow-hidden rounded-3xl bg-ink p-6 sm:p-8"
    >
      <div className="absolute top-0 right-0 w-80 h-80 bg-lime/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-royal/20 rounded-full blur-3xl" />

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center gap-6">
        <div className="w-12 h-12 rounded-2xl bg-lime/15 flex items-center justify-center shrink-0">
          <Sparkles size={22} className="text-lime" />
        </div>

        <div className="flex-1">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-2">
            AI Insight
          </p>
          <h2 className="text-lg sm:text-xl font-semibold text-white leading-snug max-w-3xl">
            Solar production is outpacing consumption by{" "}
            <span className="text-lime">38%</span> right now — an ideal window to
            charge batteries and export surplus before the{" "}
            <span className="text-lime">18:00 price peak</span>. Acting now is
            estimated to save an additional{" "}
            <span className="text-lime">€67</span> today.
          </h2>
        </div>

        <a
          href="#recommendations"
          className="inline-flex items-center gap-2 self-start lg:self-center shrink-0 px-5 py-3 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors"
        >
          View Full Analysis
          <ArrowRight size={15} />
        </a>
      </div>
    </motion.div>
  );
}
