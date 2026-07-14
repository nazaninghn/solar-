"use client";

import { motion } from "framer-motion";
import { Sun, Zap } from "lucide-react";
import { forecast, weatherIcon, weatherLabel } from "./data";

export default function SevenDayStrip() {
  return (
    <div>
      <h2 className="text-lg font-bold text-ink tracking-tight mb-4">7-Day Forecast</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {forecast.map((d, i) => {
          const Icon = weatherIcon[d.weather];
          const isToday = i === 0;
          return (
            <motion.div
              key={d.day}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.35 }}
              className={`rounded-3xl border p-4 flex flex-col items-center text-center ${
                isToday
                  ? "bg-ink border-ink text-white"
                  : "bg-white border-gray-100 text-ink"
              }`}
            >
              <p className={`text-xs font-semibold ${isToday ? "text-lime" : "text-gray-400"}`}>
                {isToday ? "Today" : d.day}
              </p>
              <p className={`text-[11px] mt-0.5 ${isToday ? "text-white/50" : "text-gray-400"}`}>
                {d.date}
              </p>

              <Icon size={28} className={`mt-3 ${isToday ? "text-lime" : "text-royal"}`} strokeWidth={1.5} />
              <p className={`text-[11px] mt-1.5 ${isToday ? "text-white/60" : "text-gray-400"}`}>
                {weatherLabel[d.weather]}
              </p>

              <div className={`flex items-center gap-1.5 text-sm font-semibold mt-2 ${isToday ? "text-white" : "text-ink"}`}>
                {d.tempHigh}° <span className={isToday ? "text-white/40" : "text-gray-400"}>/ {d.tempLow}°</span>
              </div>

              <div className="w-full mt-3 pt-3 border-t border-dashed border-current/10 space-y-1.5">
                <div className="flex items-center justify-between gap-2 text-[11px]">
                  <span className={`flex items-center gap-1 ${isToday ? "text-white/50" : "text-gray-400"}`}>
                    <Sun size={11} /> Solar
                  </span>
                  <span className={`font-semibold ${isToday ? "text-lime" : "text-lime-dark"}`}>
                    {d.solarKwh.toFixed(0)} kWh
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2 text-[11px]">
                  <span className={`flex items-center gap-1 ${isToday ? "text-white/50" : "text-gray-400"}`}>
                    <Zap size={11} /> Use
                  </span>
                  <span className={`font-semibold ${isToday ? "text-white" : "text-azure"}`}>
                    {d.consumptionKwh.toFixed(0)} kWh
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
