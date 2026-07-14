"use client";

import { motion } from "framer-motion";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";
import { Zap, Thermometer, RefreshCw, BatteryCharging } from "lucide-react";
import { battery } from "./data";

export default function BatteryGauge() {
  const gaugeData = [{ name: "SOC", value: battery.soc, fill: "#D5F332" }];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-ink text-white p-6 lg:p-8"
    >
      <div className="grid md:grid-cols-2 gap-6 items-center">
        <div className="relative flex items-center justify-center">
          <RadialBarChart
            width={220}
            height={220}
            cx="50%"
            cy="50%"
            innerRadius="72%"
            outerRadius="100%"
            barSize={16}
            data={gaugeData}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar background={{ fill: "rgba(255,255,255,0.08)" }} dataKey="value" cornerRadius={20} />
          </RadialBarChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-4xl font-bold tracking-tight">{battery.soc}%</p>
            <p className="text-xs text-white/50 mt-1 flex items-center gap-1">
              <BatteryCharging size={12} className="text-lime" />
              {battery.isCharging ? "Charging" : "Discharging"}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-white/50 uppercase tracking-widest">Battery Status</p>
            <p className="text-lg font-semibold mt-1">
              {battery.capacityUsable} kWh usable / {battery.capacityRated} kWh rated
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="rounded-2xl bg-white/10 px-3 py-3">
              <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
                <Zap size={12} />
                Rate
              </div>
              <p className="text-sm font-bold mt-1">{battery.chargeRateKw} kW</p>
            </div>
            <div className="rounded-2xl bg-white/10 px-3 py-3">
              <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
                <Thermometer size={12} />
                Temp
              </div>
              <p className="text-sm font-bold mt-1">{battery.temperatureC}°C</p>
            </div>
            <div className="rounded-2xl bg-white/10 px-3 py-3">
              <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
                <RefreshCw size={12} />
                Cycles
              </div>
              <p className="text-sm font-bold mt-1">{battery.cycles}</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
