"use client";

import { Sun, Cloud, Wind, Thermometer, Droplets, Sunrise, Sunset, CloudSun, CloudRain } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import GaugeRadial from "../primitives/GaugeRadial";

const forecast7d = [
  { day: "Mon", icon: Sun, high: 27, low: 16 },
  { day: "Tue", icon: CloudSun, high: 25, low: 15 },
  { day: "Wed", icon: Sun, high: 29, low: 17 },
  { day: "Thu", icon: Sun, high: 30, low: 18 },
  { day: "Fri", icon: Cloud, high: 22, low: 14 },
  { day: "Sat", icon: CloudRain, high: 19, low: 13 },
  { day: "Sun", icon: CloudSun, high: 23, low: 15 },
];

const weatherTimeline = [
  { hour: "06", icon: Sun }, { hour: "09", icon: Sun }, { hour: "12", icon: CloudSun },
  { hour: "15", icon: Cloud }, { hour: "18", icon: CloudSun }, { hour: "21", icon: Sun },
];

export default function WeatherSection() {
  return (
    <section id="weather" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Weather Components"
        description="Weather signal cards that connect atmospheric conditions directly to production forecasting confidence."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <GaugeRadial value={89} color="#D5F332" sublabel="W/m²" size={72} stroke={7} />
          <div>
            <p className="text-xs text-gray-400">Solar Irradiance</p>
            <p className="text-lg font-bold text-ink">890</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-steel/15 flex items-center justify-center shrink-0">
            <Cloud size={20} className="text-steel" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Cloud Coverage</p>
            <p className="text-lg font-bold text-ink">18%</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-azure/15 flex items-center justify-center shrink-0">
            <Wind size={20} className="text-azure" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Wind Speed</p>
            <p className="text-lg font-bold text-ink">12 km/h</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-energy-orange/15 flex items-center justify-center shrink-0">
            <Thermometer size={20} className="text-energy-orange" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Temperature</p>
            <p className="text-lg font-bold text-ink">24°C</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-royal/15 flex items-center justify-center shrink-0">
            <Droplets size={20} className="text-royal" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Humidity</p>
            <p className="text-lg font-bold text-ink">34%</p>
          </div>
        </div>

        {/* Sunrise / Sunset arc */}
        <div className="rounded-3xl bg-ink text-white p-6 xl:col-span-2">
          <p className="text-xs text-white/50 uppercase tracking-widest mb-4">Sun Position</p>
          <div className="relative h-16">
            <svg viewBox="0 0 200 60" className="w-full h-full overflow-visible">
              <path d="M 10 55 A 90 90 0 0 1 190 55" stroke="rgba(255,255,255,0.15)" strokeWidth={2} fill="none" strokeDasharray="4 4" />
              <circle cx="132" cy="24" r="5" fill="#D5F332" />
            </svg>
          </div>
          <div className="flex items-center justify-between -mt-2">
            <div className="flex items-center gap-1.5">
              <Sunrise size={14} className="text-lime" />
              <span className="text-xs text-white/70">05:52</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sunset size={14} className="text-energy-orange" />
              <span className="text-xs text-white/70">21:14</span>
            </div>
          </div>
        </div>

        {/* Weather timeline */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6 xl:col-span-2">
          <p className="text-xs text-gray-400 mb-4">Weather Timeline</p>
          <div className="flex items-center justify-between">
            {weatherTimeline.map((w) => (
              <div key={w.hour} className="flex flex-col items-center gap-2">
                <w.icon size={18} className="text-royal" />
                <span className="text-[11px] text-gray-400">{w.hour}:00</span>
              </div>
            ))}
          </div>
        </div>

        {/* 7-day forecast */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6 sm:col-span-2 xl:col-span-4">
          <p className="text-xs text-gray-400 mb-4">7-Day Forecast</p>
          <div className="grid grid-cols-4 sm:grid-cols-7 gap-3">
            {forecast7d.map((d) => (
              <div key={d.day} className="flex flex-col items-center gap-1.5 rounded-2xl bg-warm-bg py-4">
                <span className="text-xs font-semibold text-ink">{d.day}</span>
                <d.icon size={20} className="text-royal" />
                <span className="text-xs font-semibold text-ink">{d.high}°</span>
                <span className="text-[11px] text-gray-400">{d.low}°</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
