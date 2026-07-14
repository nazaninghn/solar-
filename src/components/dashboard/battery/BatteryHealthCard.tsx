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
import { HeartPulse, RefreshCw, CalendarClock } from "lucide-react";
import { battery, degradation } from "./data";

export default function BatteryHealthCard() {
  const cyclesPct = Math.round((battery.cycles / battery.ratedCycles) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <h3 className="text-base font-semibold text-ink">Battery Health &amp; Lifespan</h3>
      <p className="text-xs text-gray-400 mt-0.5">Projected capacity retention over time</p>

      <div className="h-56 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={degradation}>
            <defs>
              <linearGradient id="degradeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3CB54A" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#3CB54A" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="%" domain={[75, 100]} />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              formatter={(value: unknown) => [`${Number(value).toFixed(1)}%`, "Capacity Retention"]}
            />
            <Area type="monotone" dataKey="capacityPct" stroke="#3CB54A" strokeWidth={2.5} fill="url(#degradeGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-6 pt-6 border-t border-gray-100">
        <div className="flex items-start gap-2.5">
          <div className="w-8 h-8 rounded-full bg-primary-green/10 flex items-center justify-center shrink-0">
            <HeartPulse size={15} className="text-primary-green" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Health Score</p>
            <p className="text-sm font-bold text-ink">{battery.health}%</p>
          </div>
        </div>
        <div className="flex items-start gap-2.5">
          <div className="w-8 h-8 rounded-full bg-royal/10 flex items-center justify-center shrink-0">
            <RefreshCw size={15} className="text-royal" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Cycles Used</p>
            <p className="text-sm font-bold text-ink">{cyclesPct}%</p>
          </div>
        </div>
        <div className="flex items-start gap-2.5">
          <div className="w-8 h-8 rounded-full bg-steel/15 flex items-center justify-center shrink-0">
            <CalendarClock size={15} className="text-steel" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Replace By</p>
            <p className="text-sm font-bold text-ink">{battery.replacementYear}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
