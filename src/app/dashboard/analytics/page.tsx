"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend,
} from "recharts";
import { Sun, Zap, Battery, TrendingUp, TrendingDown, Activity } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface EnergyReading {
  timestamp: string;
  solar_generation_kwh: number;
  consumption_kwh: number;
  grid_import_kwh: number;
  grid_export_kwh: number;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<EnergyReading[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();

  useEffect(() => {
    async function load() {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(`${API}/api/v1/factories/1/energy/readings?limit=168`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (res.ok) {
          const json = await res.json();
          setData(Array.isArray(json) ? json : json.data || []);
        }
      } catch (e) {
        console.error("Failed to load analytics", e);
      }
      setLoading(false);
    }
    load();
  }, []);

  // Compute KPIs
  const totalSolar = data.reduce((s, d) => s + d.solar_generation_kwh, 0);
  const totalConsumption = data.reduce((s, d) => s + d.consumption_kwh, 0);
  const totalImport = data.reduce((s, d) => s + d.grid_import_kwh, 0);
  const totalExport = data.reduce((s, d) => s + d.grid_export_kwh, 0);
  const solarCoverage = totalConsumption > 0 ? (Math.min(totalSolar, totalConsumption) / totalConsumption * 100) : 0;
  const gridDependency = totalConsumption > 0 ? (totalImport / totalConsumption * 100) : 100;

  // Chart data (last 24 points)
  const chartData = data.slice(-24).map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" }),
    solar: Math.round(d.solar_generation_kwh),
    consumption: Math.round(d.consumption_kwh),
    import: Math.round(d.grid_import_kwh),
    export: Math.round(d.grid_export_kwh),
  }));

  // Daily totals for bar chart (group by day)
  const dailyMap: Record<string, { solar: number; consumption: number; import_: number }> = {};
  data.forEach((d) => {
    const day = new Date(d.timestamp).toLocaleDateString("en", { month: "short", day: "numeric" });
    if (!dailyMap[day]) dailyMap[day] = { solar: 0, consumption: 0, import_: 0 };
    dailyMap[day].solar += d.solar_generation_kwh;
    dailyMap[day].consumption += d.consumption_kwh;
    dailyMap[day].import_ += d.grid_import_kwh;
  });
  const dailyData = Object.entries(dailyMap).slice(-7).map(([day, v]) => ({
    day, solar: Math.round(v.solar), consumption: Math.round(v.consumption), import: Math.round(v.import_),
  }));

  const kpis = [
    { label: t.dashboard.analytics.solarGeneration, value: `${(totalSolar / 1000).toFixed(1)} MWh`, icon: Sun, color: "text-lime-dark", bg: "bg-lime/10" },
    { label: t.dashboard.analytics.totalConsumption, value: `${(totalConsumption / 1000).toFixed(1)} MWh`, icon: Zap, color: "text-royal", bg: "bg-royal/10" },
    { label: t.dashboard.analytics.solarCoverage, value: `${solarCoverage.toFixed(1)}%`, icon: TrendingUp, color: "text-primary-green", bg: "bg-primary-green/10" },
    { label: t.dashboard.analytics.gridDependency, value: `${gridDependency.toFixed(1)}%`, icon: TrendingDown, color: "text-energy-orange", bg: "bg-energy-orange/10" },
    { label: t.dashboard.analytics.gridExport, value: `${(totalExport / 1000).toFixed(1)} MWh`, icon: Battery, color: "text-azure", bg: "bg-azure/10" },
    { label: t.dashboard.analytics.dataPoints, value: `${data.length}`, icon: Activity, color: "text-gray-500", bg: "bg-gray-100" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{t.dashboard.analytics.title}</h1>
        <p className="text-sm text-gray-500 mt-1">{t.dashboard.analytics.subtitle}</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl p-4 border border-gray-100"
          >
            <div className={`w-9 h-9 rounded-xl ${kpi.bg} flex items-center justify-center mb-2`}>
              <kpi.icon size={18} className={kpi.color} />
            </div>
            <p className="text-xs text-gray-400">{kpi.label}</p>
            <p className="text-lg font-bold text-ink mt-0.5">{kpi.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Hourly Chart */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-1">{t.dashboard.analytics.hourlyChart}</h3>
        <p className="text-xs text-gray-400 mb-4">{t.dashboard.analytics.last24h}</p>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="solarG" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="consG" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#305293" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#305293" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} unit=" kWh" />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="solar" name="Solar" stroke="#ADC825" strokeWidth={2} fill="url(#solarG)" />
              <Area type="monotone" dataKey="consumption" name="Consumption" stroke="#305293" strokeWidth={2} fill="url(#consG)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Daily Bar Chart */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-1">{t.dashboard.analytics.dailySummary}</h3>
        <p className="text-xs text-gray-400 mb-4">{t.dashboard.analytics.last7days}</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dailyData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} unit=" kWh" />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="solar" name="Solar" fill="#ADC825" radius={[4, 4, 0, 0]} />
              <Bar dataKey="consumption" name="Consumption" fill="#305293" radius={[4, 4, 0, 0]} />
              <Bar dataKey="import" name="Grid Import" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
