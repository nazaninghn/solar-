"use client";

import { motion } from "framer-motion";
import { useCountUp } from "../useCountUp";
import { executiveSummaryStats, investorMoments } from "../data";

function BigStat({ stat, active, delay }: { stat: (typeof executiveSummaryStats)[number]; active: boolean; delay: number }) {
  const val = useCountUp(stat.value, active, 1400);
  const display = stat.decimals ? val.toFixed(stat.decimals) : Math.round(val).toLocaleString();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-3xl bg-white/5 border border-white/10 p-6 text-center"
    >
      <p className="text-3xl sm:text-4xl font-bold text-lime tracking-tight tabular-nums">
        {stat.prefix ?? ""}
        {display}
        {stat.suffix ?? ""}
      </p>
      <p className="text-xs text-white/50 mt-2">{stat.label}</p>
    </motion.div>
  );
}

export function Scene11Summary({ active }: { active: boolean }) {
  return (
    <div className="min-h-full flex items-center justify-center bg-ink px-6 py-16">
      <div className="w-full max-w-4xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">Executive Summary</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">This Is What AI-Managed Energy Looks Like</h2>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {executiveSummaryStats.map((stat, i) => (
            <BigStat key={stat.label} stat={stat} active={active} delay={0.1 + i * 0.08} />
          ))}
        </div>

        <div className="mt-10 pt-8 border-t border-white/10">
          <p className="text-xs text-white/40 uppercase tracking-widest text-center mb-5">Why Investors Care</p>
          <div className="flex flex-wrap justify-center gap-3">
            {investorMoments.map((m) => (
              <div key={m.label} className="px-4 py-2.5 rounded-full bg-lime/10 border border-lime/20">
                <span className="text-sm font-bold text-lime">
                  {m.prefix ?? ""}
                  {m.value}
                  {m.suffix ?? ""}
                </span>
                <span className="text-xs text-white/50 ml-2">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function Scene12CTA() {
  return (
    <div className="relative min-h-full flex items-center justify-center bg-ink px-6 overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-lime/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-royal/20 rounded-full blur-3xl" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="relative z-10 text-center max-w-2xl">
        <h2 className="text-4xl sm:text-5xl font-bold text-white tracking-tight leading-[1.1]">
          Power Every Energy Decision <span className="text-lime">with AI.</span>
        </h2>
        <p className="mt-5 text-white/60 text-lg">SolarFlow — AI Energy Intelligence for Industrial Facilities.</p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button className="px-7 py-3.5 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors">
            Book Demo
          </button>
          <button className="px-7 py-3.5 rounded-full border border-white/20 text-white text-sm font-semibold hover:bg-white/10 transition-colors">
            Contact Sales
          </button>
          <button className="px-7 py-3.5 rounded-full border border-white/20 text-white text-sm font-semibold hover:bg-white/10 transition-colors">
            Request Enterprise Trial
          </button>
        </div>
      </motion.div>
    </div>
  );
}
