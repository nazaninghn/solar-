"use client";

import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, ResponsiveContainer } from "recharts";
import { Download, MapPin, BatteryCharging, ArrowRightLeft, Zap } from "lucide-react";
import GaugeRadial from "@/components/analytics/primitives/GaugeRadial";
import ConfidenceMeter from "@/components/analytics/primitives/ConfidenceMeter";
import { portfolioFactories } from "../data";

const monthly = [
  { m: "Feb", v: 92 }, { m: "Mar", v: 118 }, { m: "Apr", v: 142 }, { m: "May", v: 165 }, { m: "Jun", v: 178 }, { m: "Jul", v: 185 },
];

export function Scene8Financial() {
  return (
    <div className="min-h-full flex items-center justify-center bg-warm-bg px-6 py-16">
      <div className="w-full max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">Financial Report</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight">The Numbers Finance Actually Wants</h2>
        </motion.div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-ink">Monthly Savings Trend ($K)</p>
            <button className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-ink text-white text-xs font-semibold hover:bg-black transition-colors">
              <Download size={12} />
              Download PDF
            </button>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly}>
                <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
                <Bar dataKey="v" fill="#ADC825" radius={[8, 8, 0, 0]} isAnimationActive />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mt-5">
          <div className="rounded-2xl bg-white border border-gray-100 px-5 py-4">
            <p className="text-xs text-gray-400">ROI</p>
            <p className="text-xl font-bold text-ink mt-1">7.9%</p>
          </div>
          <div className="rounded-2xl bg-white border border-gray-100 px-5 py-4">
            <p className="text-xs text-gray-400">Cost Reduction</p>
            <p className="text-xl font-bold text-primary-green mt-1">-18%</p>
          </div>
          <div className="rounded-2xl bg-white border border-gray-100 px-5 py-4">
            <p className="text-xs text-gray-400">Revenue (export)</p>
            <p className="text-xl font-bold text-azure mt-1">$9,120</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Scene9Portfolio() {
  return (
    <div className="min-h-full flex items-center justify-center bg-ink px-6 py-16">
      <div className="w-full max-w-4xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">Multi-Factory View</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">One Platform, Every Facility</h2>
        </motion.div>

        <div className="grid lg:grid-cols-5 gap-5">
          <div className="lg:col-span-2 rounded-3xl bg-white/5 border border-white/10 p-6 relative overflow-hidden h-72">
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path d="M10,20 Q50,-5 90,25 Q100,60 70,90 Q40,105 15,75 Q-5,45 10,20 Z" fill="rgba(255,255,255,0.05)" />
              {portfolioFactories.map((f) => (
                <g key={f.name}>
                  <circle cx={f.x} cy={f.y} r={2.5} fill="#D5F332" />
                  <circle cx={f.x} cy={f.y} r={5} fill="#D5F332" opacity={0.25} />
                </g>
              ))}
            </svg>
          </div>

          <div className="lg:col-span-3 grid sm:grid-cols-2 gap-3">
            {portfolioFactories.map((f, i) => (
              <motion.div
                key={f.name}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.1 }}
                className="rounded-2xl bg-white/5 border border-white/10 p-4"
              >
                <div className="flex items-center gap-1.5">
                  <MapPin size={12} className="text-lime" />
                  <p className="text-xs font-semibold text-white">{f.name}</p>
                </div>
                <div className="mt-2.5 space-y-1 text-[11px] text-white/50">
                  <div className="flex justify-between"><span>Solar</span><span className="text-white font-medium">{f.solar}</span></div>
                  <div className="flex justify-between"><span>Battery</span><span className="text-white font-medium">{f.battery}%</span></div>
                  <div className="flex justify-between"><span>Savings</span><span className="text-lime font-medium">{f.savings}</span></div>
                  <div className="flex justify-between">
                    <span>Risk</span>
                    <span className={`font-medium ${f.risk === "Low" ? "text-primary-green" : "text-energy-orange"}`}>{f.risk}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const decisions = [
  { icon: BatteryCharging, label: "Charge battery 13:00–15:00 from solar surplus" },
  { icon: ArrowRightLeft, label: "Sell 120 kWh at 18:00 peak price" },
  { icon: Zap, label: "Shift EV fleet charging to 00:00–05:00" },
];

export function Scene10ControlCenter() {
  return (
    <div className="min-h-full flex items-center justify-center bg-warm-bg px-6 py-16">
      <div className="w-full max-w-3xl">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center mb-10">
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">AI Control Center</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight">Every Decision, Explained</h2>
        </motion.div>

        <div className="rounded-3xl bg-ink text-white p-8">
          <div className="grid sm:grid-cols-3 gap-6">
            <div className="sm:col-span-2">
              <p className="text-xs text-white/50 uppercase tracking-widest mb-4">Today&apos;s Decisions</p>
              <div className="space-y-3">
                {decisions.map((d) => (
                  <div key={d.label} className="flex items-start gap-3 rounded-2xl bg-white/5 px-4 py-3">
                    <d.icon size={16} className="text-lime shrink-0 mt-0.5" />
                    <p className="text-sm">{d.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-col items-center justify-center gap-4">
              <GaugeRadial value={73} color="#4A70BE" valueClassName="text-lg font-bold text-white" sublabel="Optimization" />
              <div className="w-full">
                <ConfidenceMeter label="Forecast Confidence" value={95} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
