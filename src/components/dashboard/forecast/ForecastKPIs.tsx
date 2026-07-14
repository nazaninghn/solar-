"use client";

import { Sun, Zap, PiggyBank, Battery } from "lucide-react";
import KPICard from "../KPICard";
import { forecast, totals } from "./data";

export default function ForecastKPIs() {
  const solarSpark = forecast.map((d) => d.solarKwh);
  const consumptionSpark = forecast.map((d) => d.consumptionKwh);
  const savingsSpark = forecast.map((d) => d.savings);
  const batterySpark = forecast.map((d) => d.batterySoc);

  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <KPICard
        icon={Sun}
        label="7-Day Solar Forecast"
        value={totals.solarKwh.toFixed(0)}
        unit="kWh"
        subtext="Predicted total generation"
        trend="+9%"
        trendUp={true}
        sparkline={solarSpark}
        sparklineColor="#ADC825"
        iconBg="bg-lime/15"
        iconColor="text-lime-dark"
      />
      <KPICard
        icon={Zap}
        label="7-Day Consumption Forecast"
        value={totals.consumptionKwh.toFixed(0)}
        unit="kWh"
        subtext="Predicted total usage"
        trend="+2%"
        trendUp={false}
        sparkline={consumptionSpark}
        sparklineColor="#4A70BE"
        iconBg="bg-azure/15"
        iconColor="text-azure"
      />
      <KPICard
        icon={PiggyBank}
        label="Predicted Savings"
        value={totals.savings.toFixed(0)}
        unit="€"
        subtext="vs. no optimization"
        trend="+18%"
        trendUp={true}
        sparkline={savingsSpark}
        sparklineColor="#3CB54A"
        iconBg="bg-primary-green/15"
        iconColor="text-primary-green"
      />
      <KPICard
        icon={Battery}
        label="Avg. Battery Utilization"
        value={totals.avgBattery.toString()}
        unit="%"
        subtext="Across forecast window"
        trend="+6%"
        trendUp={true}
        sparkline={batterySpark}
        sparklineColor="#305293"
        iconBg="bg-royal/15"
        iconColor="text-royal"
      />
    </div>
  );
}
