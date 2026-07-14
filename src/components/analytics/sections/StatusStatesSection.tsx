"use client";

import { useState } from "react";
import { Sun, Moon } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import StatusBadge, { StatusVariant } from "../primitives/StatusBadge";
import ChartCard from "../primitives/ChartCard";
import MetricCard from "../primitives/MetricCard";
import { LineChart, Line, ResponsiveContainer } from "recharts";

const statuses: StatusVariant[] = [
  "healthy",
  "warning",
  "critical",
  "offline",
  "charging",
  "discharging",
  "optimizing",
  "forecasting",
];

const spark = [40, 55, 48, 62, 70, 65, 80, 76, 90];

export default function StatusStatesSection() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  return (
    <section id="status" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Guidelines"
        title="Status Indicators & Component States"
        description="Every status a system entity can be in, and how every component surfaces loading, empty, error, hover, and theme states."
      />

      {/* Status badges */}
      <div className="rounded-3xl bg-white border border-gray-100 p-6 mb-5">
        <h4 className="text-sm font-semibold text-ink mb-4">Status Variants</h4>
        <div className="flex flex-wrap gap-3">
          {statuses.map((s) => (
            <StatusBadge key={s} status={s} />
          ))}
        </div>
      </div>

      {/* Component states: ChartCard */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-5">
        <ChartCard title="Ready" tag="status=ready" height="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={spark.map((v, i) => ({ i, v }))}>
              <Line type="monotone" dataKey="v" stroke="#ADC825" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Loading" tag="status=loading" status="loading" height="h-32">{null}</ChartCard>
        <ChartCard title="Empty" tag="status=empty" status="empty" height="h-32">{null}</ChartCard>
        <ChartCard title="Error" tag="status=error" status="error" height="h-32">{null}</ChartCard>
      </div>

      {/* MetricCard states */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5 mb-5">
        <MetricCard icon={Sun} label="Ready state" value="847" unit="kW" subtext="Hover for elevation" trend="+12%" trendUp sparkline={spark} accent="lime" />
        <MetricCard icon={Sun} label="Loading state" value="" status="loading" />
        <MetricCard icon={Sun} label="Empty state" value="" status="empty" />
      </div>

      {/* Light / Dark toggle */}
      <div className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h4 className="text-sm font-semibold text-ink">Light / Dark Surface</h4>
            <p className="text-xs text-gray-400 mt-0.5">Analytics widgets are dark-mode ready — ink is a first-class surface, not an inversion hack.</p>
          </div>
          <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1">
            <button
              onClick={() => setTheme("light")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                theme === "light" ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              <Sun size={13} />
              Light
            </button>
            <button
              onClick={() => setTheme("dark")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                theme === "dark" ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              <Moon size={13} />
              Dark
            </button>
          </div>
        </div>

        <div className={`rounded-2xl p-6 transition-colors ${theme === "dark" ? "bg-ink" : "bg-warm-bg border border-gray-100"}`}>
          <div className="grid sm:grid-cols-3 gap-4">
            <div className={`rounded-2xl p-4 ${theme === "dark" ? "bg-white/5" : "bg-white border border-gray-100"}`}>
              <p className={`text-[11px] uppercase tracking-wide ${theme === "dark" ? "text-white/40" : "text-gray-400"}`}>Solar Production</p>
              <p className={`text-xl font-bold mt-1 ${theme === "dark" ? "text-white" : "text-ink"}`}>847 kW</p>
              <StatusBadge status="charging" />
            </div>
            <div className={`rounded-2xl p-4 ${theme === "dark" ? "bg-white/5" : "bg-white border border-gray-100"}`}>
              <p className={`text-[11px] uppercase tracking-wide ${theme === "dark" ? "text-white/40" : "text-gray-400"}`}>Grid Cost</p>
              <p className={`text-xl font-bold mt-1 ${theme === "dark" ? "text-white" : "text-ink"}`}>€0.184</p>
              <StatusBadge status="forecasting" />
            </div>
            <div className={`rounded-2xl p-4 ${theme === "dark" ? "bg-white/5" : "bg-white border border-gray-100"}`}>
              <p className={`text-[11px] uppercase tracking-wide ${theme === "dark" ? "text-white/40" : "text-gray-400"}`}>Battery</p>
              <p className={`text-xl font-bold mt-1 ${theme === "dark" ? "text-white" : "text-ink"}`}>68%</p>
              <StatusBadge status="healthy" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
