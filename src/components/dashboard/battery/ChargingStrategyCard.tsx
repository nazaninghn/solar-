"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Settings2, Zap } from "lucide-react";
import { strategies, activeStrategyId, nextAction } from "./data";

export default function ChargingStrategyCard() {
  const [selected, setSelected] = useState(activeStrategyId);
  const active = strategies.find((s) => s.id === selected)!;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex items-center gap-2">
        <Settings2 size={16} className="text-gray-400" />
        <h3 className="text-base font-semibold text-ink">Charging Strategy</h3>
      </div>
      <p className="text-xs text-gray-400 mt-0.5">Choose how SolarFlow manages battery charge and discharge</p>

      <div className="flex flex-wrap gap-2 mt-5">
        {strategies.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelected(s.id)}
            className={`px-4 py-2 rounded-full text-xs font-semibold transition-colors ${
              selected === s.id ? "bg-ink text-white" : "bg-mist/60 text-gray-500 hover:text-ink"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <p className="text-sm text-gray-600 leading-relaxed mt-4">{active.description}</p>

      <div className="mt-5 flex items-start gap-3 rounded-2xl bg-lime/10 border border-lime-dark/20 px-4 py-3.5">
        <div className="w-8 h-8 rounded-full bg-lime/20 flex items-center justify-center shrink-0">
          <Zap size={15} className="text-lime-dark" />
        </div>
        <div>
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-wide">Next Scheduled Action</p>
          <p className="text-sm text-ink mt-1 leading-relaxed">{nextAction}</p>
        </div>
      </div>
    </motion.div>
  );
}
