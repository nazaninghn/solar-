"use client";

import { motion } from "framer-motion";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { LucideIcon, ArrowUpRight, ArrowDownRight } from "lucide-react";

export interface KPICardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  unit?: string;
  subtext: string;
  trend: string;
  trendUp: boolean;
  sparkline: number[];
  sparklineColor: string;
  iconBg: string;
  iconColor: string;
  delay?: number;
}

export default function KPICard({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  trend,
  trendUp,
  sparkline,
  sparklineColor,
  iconBg,
  iconColor,
  delay = 0,
}: KPICardProps) {
  const data = sparkline.map((v, i) => ({ i, v }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${iconBg}`}>
          <Icon size={20} className={iconColor} />
        </div>
        <div
          className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            trendUp ? "text-primary-green bg-primary-green/10" : "text-danger bg-danger/10"
          }`}
        >
          {trendUp ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          {trend}
        </div>
      </div>

      <p className="mt-5 text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-ink tracking-tight">
        {value}
        {unit && <span className="text-lg font-semibold text-gray-400 ml-1">{unit}</span>}
      </p>
      <p className="mt-1 text-xs text-gray-400">{subtext}</p>

      <div className="h-10 mt-3 -mx-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <Line
              type="monotone"
              dataKey="v"
              stroke={sparklineColor}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
