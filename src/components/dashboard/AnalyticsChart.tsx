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

const ranges = ["Day", "Week", "Month"] as const;
type Range = (typeof ranges)[number];

const datasets: Record<Range, { label: string; production: number; consumption: number }[]> = {
  Day: [
    { label: "06:00", production: 50, consumption: 320 },
    { label: "08:00", production: 280, consumption: 450 },
    { label: "10:00", production: 620, consumption: 520 },
    { label: "12:00", production: 847, consumption: 480 },
    { label: "14:00", production: 780, consumption: 510 },
    { label: "16:00", production: 520, consumption: 600 },
    { label: "18:00", production: 180, consumption: 550 },
    { label: "20:00", production: 20, consumption: 380 },
  ],
  Week: [
    { label: "Mon", production: 3.8, consumption: 3.2 },
    { label: "Tue", production: 4.1, consumption: 3.5 },
    { label: "Wed", production: 3.6, consumption: 3.4 },
    { label: "Thu", production: 4.4, consumption: 3.6 },
    { label: "Fri", production: 4.2, consumption: 3.8 },
    { label: "Sat", production: 3.9, consumption: 2.9 },
    { label: "Sun", production: 4.0, consumption: 2.7 },
  ],
  Month: [
    { label: "Wk 1", production: 26.4, consumption: 21.8 },
    { label: "Wk 2", production: 28.1, consumption: 22.9 },
    { label: "Wk 3", production: 25.7, consumption: 23.5 },
    { label: "Wk 4", production: 29.3, consumption: 24.1 },
  ],
};

export default function AnalyticsChart() {
  const [range, setRange] = useState<Range>("Day");
  const data = datasets[range];
  const unit = range === "Day" ? "kW" : "MWh";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-semibold text-ink">Production vs Consumption</h3>
          <p className="text-xs text-gray-400 mt-0.5">Interactive analytics · {range.toLowerCase()} view</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-lime-dark" />
            <span className="text-xs text-gray-500">Production</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-azure" />
            <span className="text-xs text-gray-500">Consumption</span>
          </div>

          <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1">
            {ranges.map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                  range === r ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="limeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="azureGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4A70BE" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#4A70BE" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              unit={` ${unit}`}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            <Area
              type="monotone"
              dataKey="production"
              stroke="#ADC825"
              strokeWidth={2.5}
              fill="url(#limeGrad)"
              name="Production"
            />
            <Area
              type="monotone"
              dataKey="consumption"
              stroke="#4A70BE"
              strokeWidth={2.5}
              fill="url(#azureGrad)"
              name="Consumption"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
