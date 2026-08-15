"use client";

import { useEffect, useState } from "react";
import { Sun, Zap, Battery, Euro, PiggyBank, Leaf } from "lucide-react";
import KPICard from "./KPICard";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function KPIGrid() {
  const { t } = useLanguage();
  const [kpis, setKpis] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const token = localStorage.getItem("access_token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API}/api/v1/factories/1/energy/readings?limit=24`, { headers });
        if (res.ok) {
          const data = await res.json();
          const readings = Array.isArray(data) ? data : data.data || [];
          
          const totalSolar = readings.reduce((s: number, r: any) => s + (r.solar_generation_kwh || 0), 0);
          const totalConsumption = readings.reduce((s: number, r: any) => s + (r.consumption_kwh || 0), 0);
          const totalImport = readings.reduce((s: number, r: any) => s + (r.grid_import_kwh || 0), 0);
          const totalExport = readings.reduce((s: number, r: any) => s + (r.grid_export_kwh || 0), 0);
          const avgSolar = readings.length > 0 ? totalSolar / readings.length : 0;
          const avgConsumption = readings.length > 0 ? totalConsumption / readings.length : 0;

          setKpis({
            solarKw: Math.round(avgSolar),
            solarMwh: (totalSolar / 1000).toFixed(1),
            consumptionKw: Math.round(avgConsumption),
            consumptionMwh: (totalConsumption / 1000).toFixed(1),
            gridCost: 0.184,
            savings: Math.round(totalSolar * 0.18),
            co2: (totalSolar * 0.0004).toFixed(1),
            sparkSolar: readings.slice(-10).map((r: any) => r.solar_generation_kwh || 0),
            sparkCons: readings.slice(-10).map((r: any) => r.consumption_kwh || 0),
          });
        }
      } catch (e) {
        console.error("KPI fetch failed", e);
      }
    }
    load();
  }, []);

  const cards = [
    {
      icon: Sun,
      label: t.dashboard.solarProduction,
      value: kpis ? String(kpis.solarKw) : "—",
      unit: "kW",
      subtext: kpis ? `${kpis.solarMwh} MWh ${t.dashboard.today}` : t.dashboard.loading,
      trend: "+12%",
      trendUp: true,
      sparkline: kpis?.sparkSolar || [0],
      sparklineColor: "#ADC825",
      iconBg: "bg-lime/15",
      iconColor: "text-lime-dark",
    },
    {
      icon: Zap,
      label: t.dashboard.consumption,
      value: kpis ? String(kpis.consumptionKw) : "—",
      unit: "kW",
      subtext: kpis ? `${kpis.consumptionMwh} MWh ${t.dashboard.today}` : t.dashboard.loading,
      trend: "-5%",
      trendUp: true,
      sparkline: kpis?.sparkCons || [0],
      sparklineColor: "#4A70BE",
      iconBg: "bg-azure/15",
      iconColor: "text-azure",
    },
    {
      icon: Battery,
      label: t.dashboard.batteryCharge,
      value: "72",
      unit: "%",
      subtext: t.dashboard.charging,
      trend: "+8%",
      trendUp: true,
      sparkline: [40, 44, 48, 55, 58, 62, 66, 68, 70, 72],
      sparklineColor: "#305293",
      iconBg: "bg-royal/15",
      iconColor: "text-royal",
    },
    {
      icon: Euro,
      label: t.dashboard.gridCost,
      value: kpis ? kpis.gridCost.toFixed(3) : "—",
      unit: "€/kWh",
      subtext: t.dashboard.belowAvg,
      trend: "-3%",
      trendUp: true,
      sparkline: [24, 22, 20, 21, 19, 18, 18.4, 17, 18, 18.4],
      sparklineColor: "#879DBA",
      iconBg: "bg-steel/20",
      iconColor: "text-steel",
    },
    {
      icon: PiggyBank,
      label: t.dashboard.savings,
      value: kpis ? kpis.savings.toLocaleString() : "—",
      unit: "€",
      subtext: `${t.dashboard.thisMonth} · ${t.dashboard.fromSolar}`,
      trend: "+12%",
      trendUp: true,
      sparkline: [10, 12, 14, 13, 16, 15, 17, 18, 17.5, 18.4],
      sparklineColor: "#3CB54A",
      iconBg: "bg-primary-green/15",
      iconColor: "text-primary-green",
    },
    {
      icon: Leaf,
      label: t.dashboard.co2Reduction,
      value: kpis ? kpis.co2 : "—",
      unit: "tons",
      subtext: t.dashboard.thisMonth,
      trend: "+15%",
      trendUp: true,
      sparkline: [1.2, 1.4, 1.5, 1.6, 1.8, 1.9, 2.0, 2.1, 2.3, 2.4],
      sparklineColor: "#88C857",
      iconBg: "bg-secondary-green/15",
      iconColor: "text-secondary-green",
    },
  ];

  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
      {cards.map((card, i) => (
        <KPICard key={card.label} {...card} delay={i * 0.05} />
      ))}
    </div>
  );
}
