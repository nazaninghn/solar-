"use client";

import { motion } from "framer-motion";
import { Sparkles, TrendingUp, CloudRain, ArrowRight } from "lucide-react";

export default function ForecastInsightBanner() {
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
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-lime/15 flex items-center justify-center shrink-0">
            <Sparkles size={22} className="text-lime" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-2">
              7-Day AI Forecast Summary
            </p>
            <h2 className="text-lg sm:text-xl font-semibold text-white leading-snug max-w-3xl">
              Thursday is your best production day with{" "}
              <span className="text-lime">48.9 kWh</span> forecast and a{" "}
              <span className="text-lime">€0.31/kWh</span> price peak — plan to
              export surplus then. Saturday&apos;s rain will cut solar output by{" "}
              <span className="text-lime">~68%</span>, so pre-charge batteries on
              Friday to stay grid-independent.
            </h2>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-xs font-medium text-white/80">
            <TrendingUp size={13} className="text-lime" />
            Best sell day: <span className="text-white font-semibold">Thursday</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-xs font-medium text-white/80">
            <CloudRain size={13} className="text-azure" />
            Lowest output: <span className="text-white font-semibold">Saturday</span>
          </div>
          <a
            href="#forecast-table"
            className="ml-auto inline-flex items-center gap-2 px-5 py-2 rounded-full bg-lime text-ink text-xs font-semibold hover:bg-lime/90 transition-colors"
          >
            View Full Breakdown
            <ArrowRight size={13} />
          </a>
        </div>
      </div>
    </motion.div>
  );
}
