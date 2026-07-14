"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { PiggyBank, Sun, ArrowRightLeft, Battery } from "lucide-react";
import { forecast, totals } from "./data";

const breakdown = [
  { icon: Sun, label: "Self-Consumption Savings", value: 62.4, color: "text-lime-dark", bg: "bg-lime/15" },
  { icon: ArrowRightLeft, label: "Grid Export Revenue", value: 31.8, color: "text-royal", bg: "bg-royal/15" },
  { icon: Battery, label: "Battery Arbitrage", value: 10.9, color: "text-azure", bg: "bg-azure/15" },
];

export default function FinancialImpact() {
  return (
    <div className="grid lg:grid-cols-5 gap-6 lg:gap-8">
      {/* Cost comparison chart */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="lg:col-span-3 rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
      >
        <h3 className="text-base font-semibold text-ink">Financial Impact</h3>
        <p className="text-xs text-gray-400 mt-0.5">Projected daily cost — with vs. without SolarFlow optimization</p>

        <div className="h-64 mt-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={forecast} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="€" />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                formatter={(value: unknown) => [`€${Number(value).toFixed(2)}`, ""]}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="costWithoutOptimization" name="Without SolarFlow" fill="#879DBA" radius={[6, 6, 0, 0]} />
              <Bar dataKey="costWithOptimization" name="With SolarFlow" fill="#ADC825" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Savings estimation */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="lg:col-span-2 rounded-3xl bg-gradient-to-br from-royal to-ink text-white p-6 lg:p-8 flex flex-col"
      >
        <div className="flex items-center gap-2 text-white/60 text-xs font-semibold uppercase tracking-widest">
          <PiggyBank size={14} />
          Savings Estimation
        </div>
        <p className="text-4xl font-bold mt-3 tracking-tight">€{totals.savings.toFixed(0)}</p>
        <p className="text-sm text-white/60 mt-1">
          Estimated savings over the next 7 days
          <span className="text-lime font-semibold"> (+18% vs last week)</span>
        </p>

        <div className="mt-6 space-y-3 flex-1">
          {breakdown.map((b) => (
            <div key={b.label} className="flex items-center gap-3 rounded-2xl bg-white/10 backdrop-blur-sm px-4 py-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${b.bg}`}>
                <b.icon size={15} className={b.color} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-white/60 truncate">{b.label}</p>
              </div>
              <p className="text-sm font-bold shrink-0">€{b.value.toFixed(1)}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/50">
          <span>Total forecast cost (optimized)</span>
          <span className="font-semibold text-white">€{totals.costWith.toFixed(0)}</span>
        </div>
      </motion.div>
    </div>
  );
}
