"use client";

import { HeartPulse, Battery as BatteryIcon, Zap, Hourglass } from "lucide-react";
import KPICard from "../KPICard";
import { battery } from "./data";

export default function BatteryKPIs() {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <KPICard
        icon={HeartPulse}
        label="Battery Health"
        value={battery.health.toString()}
        unit="%"
        subtext="Excellent condition"
        trend="-1%"
        trendUp={false}
        sparkline={[99, 98.5, 98, 97.6, 97.1, 96.6, 96.2, 96]}
        sparklineColor="#3CB54A"
        iconBg="bg-primary-green/15"
        iconColor="text-primary-green"
      />
      <KPICard
        icon={BatteryIcon}
        label="Usable Capacity"
        value={battery.capacityUsable.toString()}
        unit="kWh"
        subtext={`of ${battery.capacityRated} kWh rated`}
        trend="-4%"
        trendUp={false}
        sparkline={[120, 119, 118.5, 117.8, 116.9, 116.1, 115.6, 115.2]}
        sparklineColor="#305293"
        iconBg="bg-royal/15"
        iconColor="text-royal"
      />
      <KPICard
        icon={Zap}
        label="Current SOC"
        value={battery.soc.toString()}
        unit="%"
        subtext={battery.isCharging ? `Charging · +${battery.chargeRateKw} kW` : `Discharging · ${battery.chargeRateKw} kW`}
        trend="+8%"
        trendUp={true}
        sparkline={chargeHistorySpark}
        sparklineColor="#ADC825"
        iconBg="bg-lime/15"
        iconColor="text-lime-dark"
      />
      <KPICard
        icon={Hourglass}
        label="Est. Lifespan Remaining"
        value={battery.lifespanYearsRemaining.toString()}
        unit="yrs"
        subtext={`${battery.cycles} / ${battery.ratedCycles} cycles used`}
        trend="On track"
        trendUp={true}
        sparkline={[9.1, 8.8, 8.5, 8.1, 7.8, 7.6, 7.5, 7.4]}
        sparklineColor="#879DBA"
        iconBg="bg-steel/20"
        iconColor="text-steel"
      />
    </div>
  );
}

const chargeHistorySpark = [42, 38, 34, 30, 41, 58, 74, 68];
