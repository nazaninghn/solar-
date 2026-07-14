"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { forecast } from "./data";

const tabs = ["Energy", "Battery", "Price"] as const;
type Tab = (typeof tabs)[number];

const avgPrice = forecast.reduce((s, d) => s + d.gridPrice, 0) / forecast.length;

export default function ForecastChart() {
  const [tab, setTab] = useState<Tab>("Energy");

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-semibold text-ink">Interactive Forecast</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {tab === "Energy" && "Solar production vs. consumption · 7 days"}
            {tab === "Battery" && "Predicted end-of-day battery charge · 7 days"}
            {tab === "Price" && "Average day-ahead grid price · 7 days"}
          </p>
        </div>

        <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                tab === t ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {tab === "Energy" ? (
            <AreaChart data={forecast}>
              <defs>
                <linearGradient id="fSolar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="fConsumption" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4A70BE" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#4A70BE" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit=" kWh" />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              />
              <Area type="monotone" dataKey="solarKwh" name="Solar" stroke="#ADC825" strokeWidth={2.5} fill="url(#fSolar)" />
              <Area type="monotone" dataKey="consumptionKwh" name="Consumption" stroke="#4A70BE" strokeWidth={2.5} fill="url(#fConsumption)" />
            </AreaChart>
          ) : tab === "Battery" ? (
            <LineChart data={forecast}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                formatter={(value: unknown) => [`${Number(value)}%`, "Battery SOC"]}
              />
              <ReferenceLine y={20} stroke="#EF4444" strokeDasharray="4 4" label={{ value: "Min", position: "insideBottomLeft", fill: "#EF4444", fontSize: 10 }} />
              <ReferenceLine y={90} stroke="#3CB54A" strokeDasharray="4 4" label={{ value: "Target", position: "insideTopLeft", fill: "#3CB54A", fontSize: 10 }} />
              <Line type="monotone" dataKey="batterySoc" name="Battery %" stroke="#305293" strokeWidth={2.5} dot={{ r: 4, fill: "#305293" }} />
            </LineChart>
          ) : (
            <AreaChart data={forecast}>
              <defs>
                <linearGradient id="fPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#305293" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#305293" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="€" />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                formatter={(value: unknown) => [`€${Number(value).toFixed(2)}/kWh`, "Avg Price"]}
              />
              <ReferenceLine y={avgPrice} stroke="#879DBA" strokeDasharray="4 4" label={{ value: "Avg", position: "right", fill: "#879DBA", fontSize: 11 }} />
              <Area type="monotone" dataKey="gridPrice" name="Grid Price" stroke="#305293" strokeWidth={2.5} fill="url(#fPrice)" />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
