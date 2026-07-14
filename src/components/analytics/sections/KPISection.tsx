"use client";

import {
  Sun,
  Zap,
  Battery,
  Euro,
  PiggyBank,
  ArrowRightLeft,
  Leaf,
  Factory,
  Target,
  CloudSun,
  TrendingUp,
  Share2,
  Gauge,
  RefreshCw,
  HeartPulse,
} from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import MetricCard, { MetricCardProps } from "../primitives/MetricCard";

const kpis: MetricCardProps[] = [
  { icon: Sun, label: "Today's Solar Production", value: "847", unit: "kW", subtext: "4.2 MWh generated today", trend: "+12%", trendUp: true, sparkline: [40, 55, 48, 62, 70, 65, 80, 76, 90], sparklineColor: "#ADC825", accent: "lime" },
  { icon: Zap, label: "Today's Consumption", value: "612", unit: "kW", subtext: "3.8 MWh used today", trend: "-5%", trendUp: true, sparkline: [70, 68, 72, 60, 58, 63, 55, 59, 50], sparklineColor: "#4A70BE", accent: "azure" },
  { icon: Battery, label: "Battery Level", value: "68", unit: "%", variant: "gauge", gaugeValue: 68, gaugeColor: "#D5F332", subtext: "Charging · +12.4 kW", accent: "lime" },
  { icon: Euro, label: "Grid Cost", value: "0.184", unit: "€/kWh", subtext: "Below daily average", trend: "-3%", trendUp: true, sparkline: [24, 22, 20, 21, 19, 18, 18.4, 17, 18], sparklineColor: "#879DBA", accent: "steel" },
  { icon: PiggyBank, label: "Savings", value: "2,280", unit: "€", subtext: "This month", trend: "+15%", trendUp: true, sparkline: [10, 12, 14, 13, 16, 15, 17, 18, 22.8], sparklineColor: "#3CB54A", accent: "green" },
  { icon: ArrowRightLeft, label: "Revenue", value: "760", unit: "€", subtext: "Grid export, this month", trend: "+7%", trendUp: true, sparkline: [4, 5, 4.5, 6, 6.2, 6.8, 7.1, 7.4, 7.6], sparklineColor: "#4A70BE", accent: "azure" },
  { icon: Leaf, label: "Carbon Reduction", value: "3.3", unit: "t CO₂", subtext: "This month · +11%", trend: "+11%", trendUp: true, sparkline: [1.2, 1.5, 1.8, 2.0, 2.3, 2.6, 2.9, 3.1, 3.3], sparklineColor: "#88C857", accent: "green" },
  { icon: Factory, label: "Factory Efficiency", value: "91", unit: "%", variant: "gauge", gaugeValue: 91, gaugeColor: "#3CB54A", subtext: "OEE, trailing 7 days", accent: "green" },
  { icon: Target, label: "AI Prediction Accuracy", value: "95", unit: "%", variant: "gauge", gaugeValue: 95, gaugeColor: "#D5F332", subtext: "Day-ahead solar forecast", accent: "lime" },
  { icon: CloudSun, label: "Weather Confidence", value: "88", unit: "%", variant: "gauge", gaugeValue: 88, gaugeColor: "#4A70BE", subtext: "24h irradiance model", accent: "azure" },
  { icon: TrendingUp, label: "Peak Demand", value: "1,240", unit: "kW", subtext: "Today, 18:20", trend: "+4%", trendUp: false, sparkline: [800, 850, 900, 1100, 1240, 1180, 1050, 980, 900], sparklineColor: "#FDB94C", accent: "orange" },
  { icon: Share2, label: "Grid Dependency", value: "24", unit: "%", variant: "gauge", gaugeValue: 24, gaugeColor: "#879DBA", subtext: "Of total energy consumed", accent: "steel" },
  { icon: Gauge, label: "Self-Consumption Rate", value: "76", unit: "%", variant: "gauge", gaugeValue: 76, gaugeColor: "#ADC825", subtext: "Solar used directly on-site", accent: "lime" },
  { icon: RefreshCw, label: "Battery Cycles", value: "842", subtext: "of 6,000 rated cycles", trend: "14%", trendUp: true, sparkline: [700, 730, 760, 780, 800, 815, 828, 836, 842], sparklineColor: "#305293", accent: "royal" },
  { icon: HeartPulse, label: "Battery Health", value: "96", unit: "%", variant: "gauge", gaugeValue: 96, gaugeColor: "#3CB54A", subtext: "Excellent condition", accent: "green" },
];

export default function KPISection() {
  return (
    <section id="kpis" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="KPI Cards"
        description="One MetricCard primitive, three display variants (trend + sparkline, gauge, plain), driving all 15 headline metrics."
      />
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {kpis.map((kpi) => (
          <MetricCard key={kpi.label} {...kpi} />
        ))}
      </div>
    </section>
  );
}
