"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sun, Zap, Battery, PiggyBank, Euro, Leaf, Sparkles, Check, ArrowRight } from "lucide-react";
import { useCountUp } from "../useCountUp";
import ConfidenceMeter from "@/components/analytics/primitives/ConfidenceMeter";

const summaryMetrics = [
  { icon: Sun, label: "Solar Production", value: 847, prefix: "", suffix: " kW", decimals: 0, color: "text-lime-dark", bg: "bg-lime/15" },
  { icon: Zap, label: "Consumption", value: 612, prefix: "", suffix: " kW", decimals: 0, color: "text-azure", bg: "bg-azure/15" },
  { icon: Battery, label: "Battery", value: 68, prefix: "", suffix: "%", decimals: 0, color: "text-royal", bg: "bg-royal/15" },
  { icon: PiggyBank, label: "Savings Today", value: 12400, prefix: "$", suffix: "", decimals: 0, color: "text-primary-green", bg: "bg-primary-green/15" },
  { icon: Euro, label: "Electricity Price", value: 0.184, prefix: "$", suffix: "/kWh", decimals: 3, color: "text-steel", bg: "bg-steel/20" },
  { icon: Leaf, label: "CO₂ Reduction", value: 3.3, prefix: "", suffix: " t", decimals: 1, color: "text-secondary-green", bg: "bg-secondary-green/15" },
];

function CounterTile({ metric, active, delay }: { metric: (typeof summaryMetrics)[number]; active: boolean; delay: number }) {
  const val = useCountUp(metric.value, active, 1200);
  const display = metric.decimals ? val.toFixed(metric.decimals) : Math.round(val).toLocaleString();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-3xl bg-white/5 border border-white/10 p-6"
    >
      <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${metric.bg}`}>
        <metric.icon size={20} className={metric.color} />
      </div>
      <p className="text-xs text-white/50 mt-4">{metric.label}</p>
      <p className="text-2xl font-bold text-white mt-1 tabular-nums">
        {metric.prefix}
        {display}
        {metric.suffix}
      </p>
    </motion.div>
  );
}

export function Scene3Dashboard({ active }: { active: boolean }) {
  return (
    <div className="min-h-full flex items-center justify-center bg-ink px-6 py-16">
      <div className="w-full max-w-4xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">Executive Dashboard</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Today&apos;s Summary</h2>
          <p className="text-white/40 text-sm mt-2">Everything a facility manager needs, in under 10 seconds.</p>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {summaryMetrics.map((m, i) => (
            <CounterTile key={m.label} metric={m} active={active} delay={0.1 + i * 0.08} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function Scene4Recommendation({ active }: { active: boolean }) {
  const [approved, setApproved] = useState(false);
  const savings = useCountUp(12400, active, 1200);

  return (
    <div className="min-h-full flex items-center justify-center bg-warm-bg px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-lg rounded-3xl bg-ink text-white p-8 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-lime/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-lime/15 flex items-center justify-center">
              <Sparkles size={20} className="text-lime" />
            </div>
            <p className="text-xs font-semibold text-lime uppercase tracking-widest">AI Recommendation</p>
          </div>

          <p className="text-lg font-semibold mt-5 leading-snug">
            ⚡ AI detected tomorrow&apos;s solar production will decrease by <span className="text-lime">28%</span>.
          </p>
          <p className="text-sm text-white/60 mt-2">Recommendation: Charge battery before sunset.</p>

          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="rounded-2xl bg-white/5 p-4">
              <p className="text-[11px] text-white/40">Estimated Savings</p>
              <p className="text-2xl font-bold text-lime mt-1 tabular-nums">${Math.round(savings).toLocaleString()}</p>
            </div>
            <div className="rounded-2xl bg-white/5 p-4">
              <ConfidenceMeter label="Confidence" value={92} />
            </div>
          </div>

          <button
            onClick={() => setApproved(true)}
            disabled={approved}
            className="w-full mt-6 py-3.5 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors inline-flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {approved ? (
              <>
                <Check size={16} />
                Approved
              </>
            ) : (
              <>
                Approve Recommendation
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
