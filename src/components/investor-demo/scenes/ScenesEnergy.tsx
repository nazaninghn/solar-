"use client";

import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, ReferenceLine, ResponsiveContainer, Tooltip } from "recharts";
import { Sun, CloudSun, Cloud, CloudRain, TrendingUp, TrendingDown } from "lucide-react";
import GaugeRadial from "@/components/analytics/primitives/GaugeRadial";
import { useCountUp } from "../useCountUp";

const forecast7d = [
  { day: "Mon", icon: Sun, high: 27 }, { day: "Tue", icon: CloudSun, high: 25 }, { day: "Wed", icon: Sun, high: 29 },
  { day: "Thu", icon: Sun, high: 30 }, { day: "Fri", icon: Cloud, high: 22 }, { day: "Sat", icon: CloudRain, high: 19 }, { day: "Sun", icon: CloudSun, high: 23 },
];

const priceData = [
  { h: "00", p: 0.14 }, { h: "04", p: 0.11 }, { h: "08", p: 0.19 }, { h: "12", p: 0.15 },
  { h: "16", p: 0.21 }, { h: "18", p: 0.31 }, { h: "20", p: 0.26 }, { h: "22", p: 0.18 },
];

export function Scene5Battery({ active }: { active: boolean }) {
  const savings = useCountUp(1840, active, 1200);

  return (
    <div className="min-h-full flex items-center justify-center bg-ink px-6 py-16">
      <div className="w-full max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">Battery Intelligence</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Storage That Optimizes Itself</h2>
        </motion.div>

        <div className="grid sm:grid-cols-3 gap-5">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="rounded-3xl bg-white/5 border border-white/10 p-6 flex flex-col items-center">
            <GaugeRadial value={active ? 68 : 0} size={100} stroke={9} color="#D5F332" valueClassName="text-xl font-bold text-white" sublabel="SOC" />
            <p className="text-xs text-white/50 mt-3">Charging · +12.4 kW</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="rounded-3xl bg-white/5 border border-white/10 p-6 flex flex-col items-center">
            <GaugeRadial value={active ? 96 : 0} size={100} stroke={9} color="#3CB54A" valueClassName="text-xl font-bold text-white" sublabel="Health" />
            <p className="text-xs text-white/50 mt-3">Excellent condition</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }} className="rounded-3xl bg-white/5 border border-white/10 p-6 flex flex-col items-center justify-center">
            <p className="text-xs text-white/50">Savings Estimate</p>
            <p className="text-3xl font-bold text-lime mt-2 tabular-nums">${Math.round(savings).toLocaleString()}</p>
            <p className="text-[11px] text-white/40 mt-1">This month, from optimized dispatch</p>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-5 rounded-3xl bg-white/5 border border-white/10 p-6">
          <p className="text-xs text-white/50 mb-3">Charging Timeline — next 24h</p>
          <div className="h-4 rounded-full bg-white/10 overflow-hidden flex">
            <div className="h-full bg-lime-dark" style={{ width: "25%" }} />
            <div className="h-full bg-steel" style={{ width: "12.5%" }} />
            <div className="h-full bg-azure" style={{ width: "37.5%" }} />
            <div className="h-full bg-lime-dark" style={{ width: "25%" }} />
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export function Scene6Forecast({ active }: { active: boolean }) {
  return (
    <div className="min-h-full flex items-center justify-center bg-warm-bg px-6 py-16">
      <div className="w-full max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">7-Day Forecast</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight">The AI Sees Tomorrow Coming</h2>
          <p className="text-gray-500 text-sm mt-2">Weather, solar generation, consumption, and price — forecast together, not separately.</p>
        </motion.div>

        <div className="grid grid-cols-4 sm:grid-cols-7 gap-3">
          {forecast7d.map((d, i) => (
            <motion.div
              key={d.day}
              initial={{ opacity: 0, y: 16 }}
              animate={active ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.1 + i * 0.08 }}
              className="rounded-2xl bg-white border border-gray-100 py-4 flex flex-col items-center gap-1.5"
            >
              <span className="text-xs font-semibold text-ink">{d.day}</span>
              <d.icon size={20} className="text-royal" />
              <span className="text-xs font-semibold text-ink">{d.high}°</span>
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="mt-6 flex items-center justify-center gap-3">
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-lime/15 text-xs font-semibold text-lime-dark">
            <TrendingUp size={12} /> Thu peak production
          </span>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-danger/10 text-xs font-semibold text-danger">
            <TrendingDown size={12} /> Sat rain, -68% output
          </span>
        </motion.div>
      </div>
    </div>
  );
}

export function Scene7Market() {
  return (
    <div className="min-h-full flex items-center justify-center bg-ink px-6 py-16">
      <div className="w-full max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">Electricity Market</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">Buy Low. Sell High. Automatically.</h2>
        </motion.div>

        <div className="rounded-3xl bg-white/5 border border-white/10 p-6">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={priceData}>
                <defs>
                  <linearGradient id="demoPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D5F332" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#D5F332" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="h" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "rgba(255,255,255,0.4)" }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} formatter={(v: unknown) => [`${Number(v).toFixed(2)}`, "Price"]} />
                <ReferenceLine x="04" stroke="#3CB54A" strokeDasharray="4 3" label={{ value: "Buy", position: "top", fill: "#3CB54A", fontSize: 11 }} />
                <ReferenceLine x="18" stroke="#EF4444" strokeDasharray="4 3" label={{ value: "Sell", position: "top", fill: "#EF4444", fontSize: 11 }} />
                <Area type="monotone" dataKey="p" stroke="#D5F332" strokeWidth={2.5} fill="url(#demoPrice)" isAnimationActive />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4 mt-5">
          <div className="rounded-2xl bg-primary-green/10 border border-primary-green/20 px-5 py-4">
            <p className="text-xs font-semibold text-primary-green uppercase tracking-wide">Best Time to Buy</p>
            <p className="text-lg font-bold text-white mt-1">04:00 · $0.11/kWh</p>
          </div>
          <div className="rounded-2xl bg-danger/10 border border-danger/20 px-5 py-4">
            <p className="text-xs font-semibold text-danger uppercase tracking-wide">Best Time to Sell</p>
            <p className="text-lg font-bold text-white mt-1">18:00 · $0.31/kWh</p>
          </div>
        </div>
      </div>
    </div>
  );
}
