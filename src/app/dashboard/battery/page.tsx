"use client";

import BatteryKPIs from "@/components/dashboard/battery/BatteryKPIs";
import BatteryGauge from "@/components/dashboard/battery/BatteryGauge";
import ChargeHistoryChart from "@/components/dashboard/battery/ChargeHistoryChart";
import ChargeForecastChart from "@/components/dashboard/battery/ChargeForecastChart";
import BatteryHealthCard from "@/components/dashboard/battery/BatteryHealthCard";
import ChargingStrategyCard from "@/components/dashboard/battery/ChargingStrategyCard";

export default function BatteryPage() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Battery Storage</h1>
        <p className="text-sm text-gray-500 mt-1">
          Health, capacity, charge behavior, and lifespan for your storage system.
        </p>
      </div>

      <BatteryKPIs />

      <BatteryGauge />

      <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
        <ChargeHistoryChart />
        <ChargeForecastChart />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
        <BatteryHealthCard />
        <ChargingStrategyCard />
      </div>
    </>
  );
}
