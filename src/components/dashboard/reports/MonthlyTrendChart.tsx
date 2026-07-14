"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { monthly } from "./data";

const tabs = [
  { key: "savings", label: "Savings", unit: "€", color: "#3CB54A" },
  { key: "revenue", label: "Revenue", unit: "€", color: "#4A70BE" },
  { key: "gridCost", label: "Grid Cost", unit: "€/kWh", color: "#305293" },
  { key: "carbonTons", label: "Carbon", unit: "t CO₂", color: "#88C857" },
] as const;

export default function MonthlyTrendChart() {
  const [active, setActive] = useState<(typeof tabs)[number]>(tabs[0]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-semibold text-ink">Monthly {active.label} Trend</h3>
          <p className="text-xs text-gray-400 mt-0.5">Trailing 12 months · compare month to month</p>
        </div>
        <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setActive(t)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                active.key === t.key ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={monthly}>
            <defs>
              <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={active.color} stopOpacity={0.3} />
                <stop offset="100%" stopColor={active.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit={` ${active.unit}`} />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              formatter={(value: unknown) => [`${active.unit === "€" ? "€" : ""}${value}${active.unit !== "€" ? ` ${active.unit}` : ""}`, active.label]}
            />
            <Area type="monotone" dataKey={active.key} stroke={active.color} strokeWidth={2.5} fill="url(#trendGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
