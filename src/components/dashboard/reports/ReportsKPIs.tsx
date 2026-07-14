"use client";

import { PiggyBank, ArrowRightLeft, TrendingUp, Euro, Leaf } from "lucide-react";
import KPICard from "../KPICard";
import { monthly, totals } from "./data";

const savingsSpark = monthly.map((m) => m.savings);
const revenueSpark = monthly.map((m) => m.revenue);
const roiSpark = monthly.map((m) => m.roi);
const gridCostSpark = monthly.map((m) => m.gridCost);
const carbonSpark = monthly.map((m) => m.carbonTons);

export default function ReportsKPIs() {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-5">
      <KPICard
        icon={PiggyBank}
        label="Monthly Savings"
        value={monthly[monthly.length - 1].savings.toLocaleString()}
        unit="€"
        subtext="July · vs €1,980 in June"
        trend="+15%"
        trendUp={true}
        sparkline={savingsSpark}
        sparklineColor="#3CB54A"
        iconBg="bg-primary-green/15"
        iconColor="text-primary-green"
      />
      <KPICard
        icon={ArrowRightLeft}
        label="Revenue"
        value={monthly[monthly.length - 1].revenue.toLocaleString()}
        unit="€"
        subtext="Grid export, July"
        trend="+7%"
        trendUp={true}
        sparkline={revenueSpark}
        sparklineColor="#4A70BE"
        iconBg="bg-azure/15"
        iconColor="text-azure"
      />
      <KPICard
        icon={TrendingUp}
        label="ROI"
        value={totals.avgRoi.toFixed(1)}
        unit="%"
        subtext="Trailing 12-month average"
        trend="+0.4pp"
        trendUp={true}
        sparkline={roiSpark}
        sparklineColor="#ADC825"
        iconBg="bg-lime/15"
        iconColor="text-lime-dark"
      />
      <KPICard
        icon={Euro}
        label="Grid Electricity Cost"
        value={totals.avgGridCost.toFixed(3)}
        unit="€/kWh"
        subtext="Trailing 12-month average"
        trend="-2%"
        trendUp={true}
        sparkline={gridCostSpark}
        sparklineColor="#879DBA"
        iconBg="bg-steel/20"
        iconColor="text-steel"
      />
      <KPICard
        icon={Leaf}
        label="Carbon Reduction"
        value={totals.carbonYTD.toFixed(1)}
        unit="t CO₂"
        subtext="Trailing 12 months"
        trend="+11%"
        trendUp={true}
        sparkline={carbonSpark}
        sparklineColor="#88C857"
        iconBg="bg-secondary-green/15"
        iconColor="text-secondary-green"
      />
    </div>
  );
}
