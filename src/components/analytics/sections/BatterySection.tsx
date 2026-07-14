"use client";

import { AreaChart, Area, XAxis, ResponsiveContainer } from "recharts";
import { Zap, Thermometer, RefreshCw, Hourglass, HeartPulse, BatteryCharging } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";
import GaugeRadial from "../primitives/GaugeRadial";

const degradation = [
  { y: "26", v: 100 }, { y: "27", v: 98.2 }, { y: "28", v: 96.1 }, { y: "29", v: 93.8 }, { y: "30", v: 91.2 },
];

const chargeTimeline = [
  { label: "Charging", pct: 25, color: "bg-lime-dark" },
  { label: "Hold", pct: 12.5, color: "bg-steel" },
  { label: "Discharging", pct: 37.5, color: "bg-azure" },
  { label: "Charging", pct: 25, color: "bg-lime-dark" },
];

export default function BatterySection() {
  return (
    <section id="battery" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Battery Components"
        description="Charge state, thermal, and longevity widgets for storage system monitoring."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-ink text-white p-6 flex items-center gap-5">
          <GaugeRadial value={68} color="#D5F332" valueClassName="text-lg font-bold text-white" sublabel="SOC" />
          <div>
            <p className="text-xs text-white/50">Battery Level</p>
            <p className="text-2xl font-bold mt-1">68%</p>
            <p className="text-[11px] text-white/40 mt-1">115.2 / 120 kWh usable</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-lime/15 flex items-center justify-center shrink-0">
            <BatteryCharging size={20} className="text-lime-dark" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Charging Speed</p>
            <p className="text-lg font-bold text-ink">+12.4 kW</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-energy-orange/15 flex items-center justify-center shrink-0">
            <Thermometer size={20} className="text-energy-orange" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Temperature</p>
            <p className="text-lg font-bold text-ink">28°C</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 sm:col-span-2 xl:col-span-2">
          <p className="text-xs text-gray-400 mb-3">Charging / Discharge Timeline — next 24h</p>
          <div className="h-6 rounded-full bg-mist overflow-hidden flex">
            {chargeTimeline.map((c, i) => (
              <div key={i} className={`h-full ${c.color}`} style={{ width: `${c.pct}%` }} />
            ))}
          </div>
          <div className="flex flex-wrap gap-3 mt-3">
            {[...new Map(chargeTimeline.map((c) => [c.label, c.color])).entries()].map(([label, color]) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${color}`} />
                <span className="text-[10px] text-gray-500">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-5">
          <GaugeRadial value={96} color="#3CB54A" sublabel="Score" />
          <div>
            <div className="flex items-center gap-2">
              <HeartPulse size={15} className="text-primary-green" />
              <h4 className="text-sm font-semibold text-ink">Health Score</h4>
            </div>
            <p className="text-xs text-gray-400 mt-1">Excellent condition</p>
          </div>
        </div>

        <ChartCard title="Lifetime Capacity" tag="AreaChart" height="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={degradation}>
              <defs>
                <linearGradient id="battLife" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3CB54A" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#3CB54A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="y" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Area type="monotone" dataKey="v" stroke="#3CB54A" strokeWidth={2.5} fill="url(#battLife)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-royal/15 flex items-center justify-center shrink-0">
            <RefreshCw size={20} className="text-royal" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Charge Cycles</p>
            <p className="text-lg font-bold text-ink">842 <span className="text-xs text-gray-400 font-normal">/ 6,000</span></p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-steel/20 flex items-center justify-center shrink-0">
            <Hourglass size={20} className="text-steel" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Expected Lifespan Remaining</p>
            <p className="text-lg font-bold text-ink">7.4 yrs</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-mist flex items-center justify-center shrink-0">
            <Zap size={20} className="text-ink" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Rated Capacity</p>
            <p className="text-lg font-bold text-ink">120 kWh</p>
          </div>
        </div>
      </div>
    </section>
  );
}
