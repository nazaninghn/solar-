"use client";

import { Sun, Zap, Battery, Euro, PiggyBank, Leaf } from "lucide-react";
import KPICard from "./KPICard";

const cards = [
  {
    icon: Sun,
    label: "Solar Production",
    value: "847",
    unit: "kW",
    subtext: "4.2 MWh generated today",
    trend: "+12%",
    trendUp: true,
    sparkline: [40, 55, 48, 62, 70, 65, 80, 76, 90, 84],
    sparklineColor: "#ADC825",
    iconBg: "bg-lime/15",
    iconColor: "text-lime-dark",
  },
  {
    icon: Zap,
    label: "Consumption",
    value: "612",
    unit: "kW",
    subtext: "3.8 MWh used today",
    trend: "-5%",
    trendUp: true,
    sparkline: [70, 68, 72, 60, 58, 63, 55, 59, 50, 52],
    sparklineColor: "#4A70BE",
    iconBg: "bg-azure/15",
    iconColor: "text-azure",
  },
  {
    icon: Battery,
    label: "Battery Charge",
    value: "68",
    unit: "%",
    subtext: "Charging · 2h 10m to full",
    trend: "+8%",
    trendUp: true,
    sparkline: [40, 44, 48, 50, 55, 58, 62, 64, 66, 68],
    sparklineColor: "#305293",
    iconBg: "bg-royal/15",
    iconColor: "text-royal",
  },
  {
    icon: Euro,
    label: "Grid Cost",
    value: "0.184",
    unit: "€/kWh",
    subtext: "Below daily average",
    trend: "-3%",
    trendUp: true,
    sparkline: [24, 22, 20, 21, 19, 18, 18.4, 17, 18, 18.4],
    sparklineColor: "#879DBA",
    iconBg: "bg-steel/20",
    iconColor: "text-steel",
  },
  {
    icon: PiggyBank,
    label: "Savings",
    value: "18,420",
    unit: "€",
    subtext: "This month · +12% vs last",
    trend: "+12%",
    trendUp: true,
    sparkline: [10, 12, 14, 13, 16, 15, 17, 18, 17.5, 18.4],
    sparklineColor: "#3CB54A",
    iconBg: "bg-primary-green/15",
    iconColor: "text-primary-green",
  },
  {
    icon: Leaf,
    label: "CO₂ Reduction",
    value: "2.4",
    unit: "tons",
    subtext: "This month · +15% vs last",
    trend: "+15%",
    trendUp: true,
    sparkline: [1.2, 1.4, 1.5, 1.6, 1.8, 1.9, 2.0, 2.1, 2.3, 2.4],
    sparklineColor: "#88C857",
    iconBg: "bg-secondary-green/15",
    iconColor: "text-secondary-green",
  },
];

export default function KPIGrid() {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
      {cards.map((card, i) => (
        <KPICard key={card.label} {...card} delay={i * 0.05} />
      ))}
    </div>
  );
}
