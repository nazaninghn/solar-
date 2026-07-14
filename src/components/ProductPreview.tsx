"use client";

import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { TrendingUp, Zap, DollarSign, Leaf } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const solarData = [
  { time: "06:00", production: 50, consumption: 320 },
  { time: "08:00", production: 280, consumption: 450 },
  { time: "10:00", production: 620, consumption: 520 },
  { time: "12:00", production: 847, consumption: 480 },
  { time: "14:00", production: 780, consumption: 510 },
  { time: "16:00", production: 520, consumption: 600 },
  { time: "18:00", production: 180, consumption: 550 },
  { time: "20:00", production: 20, consumption: 380 },
];

const kpiIcons = [TrendingUp, Zap, DollarSign, Leaf];
const kpiColors = ["text-primary-green", "text-energy-orange", "text-secondary-green", "text-primary-green"];

export default function ProductPreview() {
  const { t } = useLanguage();
  const kpis = t.productPreview.kpis.map((kpi, i) => ({ ...kpi, icon: kpiIcons[i], color: kpiColors[i] }));

  return (
    <section className="py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
            {t.productPreview.eyebrow}
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
            {t.productPreview.title}
          </h2>
          <p className="mt-4 text-gray-500">
            {t.productPreview.subtitle}
          </p>
        </motion.div>

        {/* KPI Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          {kpis.map((kpi) => (
            <div
              key={kpi.label}
              className="bg-surface rounded-3xl p-5 border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-2 mb-2">
                <kpi.icon size={16} className={kpi.color} />
                <span className="text-xs text-gray-500 font-medium">
                  {kpi.label}
                </span>
              </div>
              <p className="text-xl font-bold text-ink">{kpi.value}</p>
              <p className="text-xs text-primary-green font-medium mt-1">
                {kpi.change} {t.productPreview.thisMonth}
              </p>
            </div>
          ))}
        </motion.div>

        {/* Main Chart */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="bg-surface rounded-3xl p-6 lg:p-8 border border-gray-100 shadow-xl shadow-ink/5"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-ink">
                {t.productPreview.chartTitle}
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                {t.productPreview.chartSubtitle}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-green" />
                <span className="text-xs text-gray-500">{t.productPreview.legendProduction}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-energy-orange" />
                <span className="text-xs text-gray-500">{t.productPreview.legendConsumption}</span>
              </div>
            </div>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={solarData}>
                <defs>
                  <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3CB54A" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#3CB54A" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="orangeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FDB94C" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#FDB94C" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  unit=" kW"
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
                  stroke="#3CB54A"
                  strokeWidth={2.5}
                  fill="url(#greenGrad)"
                  name="Solar Production"
                />
                <Area
                  type="monotone"
                  dataKey="consumption"
                  stroke="#FDB94C"
                  strokeWidth={2.5}
                  fill="url(#orangeGrad)"
                  name="Consumption"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
