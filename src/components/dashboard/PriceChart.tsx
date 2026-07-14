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
  ReferenceLine,
} from "recharts";

const priceData = [
  { hour: "00", price: 0.14 },
  { hour: "02", price: 0.12 },
  { hour: "04", price: 0.11 },
  { hour: "06", price: 0.15 },
  { hour: "08", price: 0.19 },
  { hour: "10", price: 0.17 },
  { hour: "12", price: 0.15 },
  { hour: "14", price: 0.16 },
  { hour: "16", price: 0.21 },
  { hour: "18", price: 0.31 },
  { hour: "20", price: 0.26 },
  { hour: "22", price: 0.18 },
];

const avg = priceData.reduce((s, d) => s + d.price, 0) / priceData.length;

export default function PriceChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h3 className="text-base font-semibold text-ink">Electricity Price Today</h3>
          <p className="text-xs text-gray-400 mt-0.5">€/kWh · day-ahead market</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-danger/10">
          <span className="w-2 h-2 rounded-full bg-danger" />
          <span className="text-xs font-semibold text-danger">Best sell window: 18:00–19:00</span>
        </div>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={priceData}>
            <defs>
              <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#305293" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#305293" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="hour"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              unit="€"
            />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
              formatter={(value: unknown) => [`€${Number(value).toFixed(2)}/kWh`, "Price"]}
            />
            <ReferenceLine
              y={avg}
              stroke="#879DBA"
              strokeDasharray="4 4"
              label={{ value: "Avg", position: "right", fill: "#879DBA", fontSize: 11 }}
            />
            <ReferenceLine
              x="12"
              stroke="#293234"
              strokeDasharray="3 3"
              label={{ value: "Now", position: "top", fill: "#293234", fontSize: 11 }}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#305293"
              strokeWidth={2.5}
              fill="url(#priceGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
