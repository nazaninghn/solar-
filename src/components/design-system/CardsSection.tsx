"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";
import { Sun, ArrowUpRight, MoreHorizontal } from "lucide-react";
import SectionHeader from "./SectionHeader";

const spark = [40, 55, 48, 62, 70, 65, 80, 76, 90, 84].map((v, i) => ({ i, v }));

export default function CardsSection() {
  return (
    <section id="cards" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Cards"
        description="rounded-3xl is the standard card radius across the product. Cards nest icon chips, trend badges, and sparklines."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* KPI card */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-start justify-between">
            <div className="w-11 h-11 rounded-2xl bg-lime/15 flex items-center justify-center">
              <Sun size={20} className="text-lime-dark" />
            </div>
            <div className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full text-primary-green bg-primary-green/10">
              <ArrowUpRight size={12} />
              +12%
            </div>
          </div>
          <p className="mt-5 text-sm text-gray-500">Solar Production</p>
          <p className="mt-1 text-3xl font-bold text-ink tracking-tight">847<span className="text-lg font-semibold text-gray-400 ml-1">kW</span></p>
          <p className="mt-1 text-xs text-gray-400">4.2 MWh generated today</p>
          <div className="h-10 mt-3 -mx-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={spark}>
                <Line type="monotone" dataKey="v" stroke="#ADC825" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-[11px] font-mono text-gray-300">KPI Card</p>
        </div>

        {/* Basic card */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-start justify-between">
            <h4 className="text-sm font-semibold text-ink">Facility A — Munich</h4>
            <button className="text-gray-400 hover:text-ink">
              <MoreHorizontal size={16} />
            </button>
          </div>
          <p className="mt-2 text-sm text-gray-500 leading-relaxed">
            120 kWh battery, 340 kWp solar array. Connected since March 2024.
          </p>
          <div className="mt-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary-green" />
            <span className="text-xs text-gray-500">Online · Last sync 2m ago</span>
          </div>
          <p className="mt-4 text-[11px] font-mono text-gray-300">Basic Card</p>
        </div>

        {/* Dark stat card */}
        <div className="rounded-3xl bg-ink text-white p-6">
          <p className="text-xs text-white/50 uppercase tracking-widest">Savings Estimation</p>
          <p className="text-3xl font-bold mt-2 tracking-tight">€391</p>
          <p className="text-sm text-white/60 mt-1">If all pending recommendations are approved</p>
          <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/50">
            <span>Confidence</span>
            <span className="font-semibold text-lime">High</span>
          </div>
          <p className="mt-4 text-[11px] font-mono text-white/20">Dark Stat Card</p>
        </div>

        {/* List card */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6 sm:col-span-2 lg:col-span-1">
          <h4 className="text-sm font-semibold text-ink mb-4">Recent Alerts</h4>
          <div className="space-y-3">
            {["Price spike expected at 18:00", "Monthly report ready", "Inverter 2 efficiency drift"].map((t) => (
              <div key={t} className="flex items-center gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-lime-dark shrink-0" />
                <p className="text-sm text-gray-600 truncate">{t}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-[11px] font-mono text-gray-300">List Card</p>
        </div>

        {/* Bordered accent card */}
        <div className="rounded-3xl bg-lime/10 border border-lime-dark/20 p-6 sm:col-span-2 lg:col-span-2">
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-wide">Next Scheduled Action</p>
          <p className="text-sm text-ink mt-2 leading-relaxed">
            Charging scheduled 13:00–15:00 from solar surplus — adds an estimated 18% SOC before the evening price peak.
          </p>
          <p className="mt-4 text-[11px] font-mono text-lime-dark/50">Accent Card</p>
        </div>
      </div>
    </section>
  );
}
