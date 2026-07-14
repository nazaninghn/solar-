"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";
import { ArrowUpRight, ArrowDownRight, LucideIcon } from "lucide-react";
import GaugeRadial from "./GaugeRadial";
import { Skeleton, EmptyState } from "./States";

export interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  unit?: string;
  subtext?: string;
  trend?: string;
  trendUp?: boolean;
  variant?: "sparkline" | "gauge" | "none";
  sparkline?: number[];
  sparklineColor?: string;
  gaugeValue?: number;
  gaugeColor?: string;
  accent?: "lime" | "azure" | "royal" | "green" | "steel" | "orange";
  status?: "ready" | "loading" | "empty";
}

const accentMap = {
  lime: { bg: "bg-lime/15", text: "text-lime-dark" },
  azure: { bg: "bg-azure/15", text: "text-azure" },
  royal: { bg: "bg-royal/15", text: "text-royal" },
  green: { bg: "bg-primary-green/15", text: "text-primary-green" },
  steel: { bg: "bg-steel/20", text: "text-steel" },
  orange: { bg: "bg-energy-orange/15", text: "text-energy-orange" },
};

export default function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  trend,
  trendUp = true,
  variant = "sparkline",
  sparkline,
  sparklineColor = "#ADC825",
  gaugeValue,
  gaugeColor = "#D5F332",
  accent = "lime",
  status = "ready",
}: MetricCardProps) {
  const a = accentMap[accent];

  if (status === "loading") {
    return (
      <div className="rounded-3xl bg-white border border-gray-100 p-6">
        <div className="flex items-start justify-between">
          <Skeleton className="w-11 h-11 rounded-2xl" />
          <Skeleton className="w-14 h-6 rounded-full" />
        </div>
        <Skeleton className="h-3 w-24 mt-5" />
        <Skeleton className="h-7 w-20 mt-2" />
        <Skeleton className="h-3 w-32 mt-2" />
      </div>
    );
  }

  if (status === "empty") {
    return (
      <div className="rounded-3xl bg-white border border-gray-100 p-6">
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${a.bg}`}>
          <Icon size={20} className={a.text} />
        </div>
        <p className="mt-5 text-sm text-gray-500">{label}</p>
        <EmptyState label="No data" hint="Awaiting first reading." />
      </div>
    );
  }

  return (
    <div className="rounded-3xl bg-white border border-gray-100 p-6 hover:border-gray-200 hover:shadow-md transition-all">
      <div className="flex items-start justify-between">
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${a.bg}`}>
          <Icon size={20} className={a.text} />
        </div>
        {trend && (
          <div
            className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
              trendUp ? "text-primary-green bg-primary-green/10" : "text-danger bg-danger/10"
            }`}
          >
            {trendUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
            {trend}
          </div>
        )}
      </div>

      <p className="mt-5 text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-ink tracking-tight">
        {value}
        {unit && <span className="text-lg font-semibold text-gray-400 ml-1">{unit}</span>}
      </p>
      {subtext && <p className="mt-1 text-xs text-gray-400">{subtext}</p>}

      {variant === "sparkline" && sparkline && (
        <div className="h-10 mt-3 -mx-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkline.map((v, i) => ({ i, v }))}>
              <Line type="monotone" dataKey="v" stroke={sparklineColor} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {variant === "gauge" && gaugeValue !== undefined && (
        <div className="flex justify-center mt-2">
          <GaugeRadial value={gaugeValue} size={64} stroke={6} color={gaugeColor} valueClassName="text-sm font-bold text-ink" />
        </div>
      )}
    </div>
  );
}
