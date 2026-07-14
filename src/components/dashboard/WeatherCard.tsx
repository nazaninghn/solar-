"use client";

import { motion } from "framer-motion";
import { CloudSun, Sun, Cloud, Wind, Droplets, MapPin } from "lucide-react";

const forecast = [
  { time: "Now", icon: Sun, temp: "24°" },
  { time: "13:00", icon: Sun, temp: "26°" },
  { time: "14:00", icon: CloudSun, temp: "25°" },
  { time: "15:00", icon: CloudSun, temp: "23°" },
  { time: "16:00", icon: Cloud, temp: "21°" },
];

export default function WeatherCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-gradient-to-br from-royal to-ink text-white p-6 lg:p-8 h-full flex flex-col"
    >
      <div className="flex items-center gap-1.5 text-white/60 text-xs">
        <MapPin size={13} />
        Facility A · Munich
      </div>

      <div className="flex items-center justify-between mt-4">
        <div>
          <p className="text-5xl font-bold tracking-tight">24°</p>
          <p className="text-sm text-white/60 mt-1">Sunny, clear skies</p>
        </div>
        <Sun size={56} className="text-lime" strokeWidth={1.5} />
      </div>

      <div className="grid grid-cols-2 gap-3 mt-6">
        <div className="rounded-2xl bg-white/10 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
            <Sun size={12} />
            Irradiance
          </div>
          <p className="text-lg font-bold mt-1">890 W/m²</p>
          <div className="h-1.5 rounded-full bg-white/15 mt-2 overflow-hidden">
            <div className="h-full bg-lime rounded-full" style={{ width: "82%" }} />
          </div>
        </div>
        <div className="rounded-2xl bg-white/10 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
            <Wind size={12} />
            Wind
          </div>
          <p className="text-lg font-bold mt-1">12 km/h</p>
          <div className="flex items-center gap-1.5 text-white/50 text-[11px] mt-2">
            <Droplets size={12} />
            34% humidity
          </div>
        </div>
      </div>

      <div className="mt-6 pt-5 border-t border-white/10 flex-1">
        <p className="text-xs text-white/50 mb-3">Hourly forecast</p>
        <div className="flex items-center justify-between">
          {forecast.map((f) => (
            <div key={f.time} className="flex flex-col items-center gap-1.5">
              <span className="text-[11px] text-white/50">{f.time}</span>
              <f.icon size={16} className="text-lime" />
              <span className="text-xs font-semibold">{f.temp}</span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
