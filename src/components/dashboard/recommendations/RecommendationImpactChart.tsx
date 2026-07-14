"use client";

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
import { impactHistory } from "./data";

export default function RecommendationImpactChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <h3 className="text-base font-semibold text-ink">Realized Savings from AI Recommendations</h3>
      <p className="text-xs text-gray-400 mt-0.5">Weekly savings from approved recommendations · last 8 weeks</p>

      <div className="h-56 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={impactHistory}>
            <defs>
              <linearGradient id="impactGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="€" />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              formatter={(value: unknown) => [`€${value}`, "Savings"]}
            />
            <Area type="monotone" dataKey="savings" stroke="#ADC825" strokeWidth={2.5} fill="url(#impactGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
