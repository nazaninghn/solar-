"use client";

import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { monthly, forecast } from "./data";

const history = monthly.slice(-6).map((m) => ({ label: m.month, actual: m.savings, projected: null as number | null }));
const bridge = history[history.length - 1];
bridge.projected = bridge.actual;

const future = forecast.map((f) => ({ label: f.month, actual: null as number | null, projected: f.savings }));

const chartData = [...history, ...future];

export default function ForecastSavingsChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h3 className="text-base font-semibold text-ink">Forecast Future Savings</h3>
          <p className="text-xs text-gray-400 mt-0.5">Last 6 months actual, next 4 months projected</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 rounded bg-primary-green" />
            <span className="text-xs text-gray-500">Actual</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 rounded bg-royal" style={{ backgroundImage: "repeating-linear-gradient(90deg, #305293 0 4px, transparent 4px 7px)" }} />
            <span className="text-xs text-gray-500">Projected</span>
          </div>
        </div>
      </div>

      <div className="h-64 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit=" €" />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              formatter={(value: unknown) => [`€${value}`, "Savings"]}
            />
            <ReferenceLine x={bridge.label} stroke="#E8E8EC" strokeWidth={2} label={{ value: "Today", position: "top", fill: "#879DBA", fontSize: 11 }} />
            <Line type="monotone" dataKey="actual" stroke="#3CB54A" strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false} />
            <Line type="monotone" dataKey="projected" stroke="#305293" strokeWidth={2.5} strokeDasharray="6 5" dot={{ r: 3 }} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
