"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CloudSun, Sun, Cloud, Wind, Droplets, MapPin } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface WeatherData {
  temp: number;
  cloud: number;
  wind: number;
  humidity: number;
  radiation: number;
  hourly: { time: string; temp: number; cloud: number }[];
}

export default function WeatherCard() {
  const { t } = useLanguage();
  const [weather, setWeather] = useState<WeatherData | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(
          "https://api.open-meteo.com/v1/forecast?latitude=41.01&longitude=28.98&hourly=temperature_2m,cloud_cover,wind_speed_10m,relative_humidity_2m,shortwave_radiation&forecast_days=1&timezone=auto"
        );
        if (res.ok) {
          const data = await res.json();
          const h = data.hourly;
          const nowHour = new Date().getHours();
          setWeather({
            temp: Math.round(h.temperature_2m[nowHour] || 0),
            cloud: h.cloud_cover[nowHour] || 0,
            wind: Math.round(h.wind_speed_10m[nowHour] || 0),
            humidity: h.relative_humidity_2m[nowHour] || 0,
            radiation: Math.round(h.shortwave_radiation[nowHour] || 0),
            hourly: Array.from({ length: 5 }, (_, i) => {
              const idx = Math.min(nowHour + i, 23);
              return {
                time: i === 0 ? t.dashboard.weather.now : `${idx}:00`,
                temp: Math.round(h.temperature_2m[idx] || 0),
                cloud: h.cloud_cover[idx] || 0,
              };
            }),
          });
        }
      } catch (e) {
        console.error("Weather fetch failed", e);
      }
    }
    load();
  }, [t]);

  const getIcon = (cloud: number) => (cloud < 30 ? Sun : cloud < 70 ? CloudSun : Cloud);
  const getCondition = (cloud: number) =>
    cloud < 20 ? t.dashboard.weather.clear : cloud < 50 ? t.dashboard.weather.partlyCloudy : cloud < 80 ? t.dashboard.weather.cloudy : t.dashboard.weather.overcast;

  const MainIcon = weather ? getIcon(weather.cloud) : Sun;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-gradient-to-br from-royal to-ink text-white p-6 lg:p-8 h-full flex flex-col"
    >
      <div className="flex items-center gap-1.5 text-white/60 text-xs">
        <MapPin size={13} />
        {t.dashboard.weather.location}
      </div>

      <div className="flex items-center justify-between mt-4">
        <div>
          <p className="text-5xl font-bold tracking-tight">{weather ? `${weather.temp}°` : "—"}</p>
          <p className="text-sm text-white/60 mt-1">{weather ? getCondition(weather.cloud) : t.dashboard.loading}</p>
        </div>
        <MainIcon size={56} className="text-lime" strokeWidth={1.5} />
      </div>

      <div className="grid grid-cols-2 gap-3 mt-6">
        <div className="rounded-2xl bg-white/10 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
            <Sun size={12} />
            {t.dashboard.weather.irradiance}
          </div>
          <p className="text-lg font-bold mt-1">{weather ? `${weather.radiation} W/m²` : "—"}</p>
          <div className="h-1.5 rounded-full bg-white/15 mt-2 overflow-hidden">
            <div className="h-full bg-lime rounded-full" style={{ width: `${Math.min((weather?.radiation || 0) / 10, 100)}%` }} />
          </div>
        </div>
        <div className="rounded-2xl bg-white/10 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-1.5 text-white/50 text-[11px]">
            <Wind size={12} />
            {t.dashboard.weather.wind}
          </div>
          <p className="text-lg font-bold mt-1">{weather ? `${weather.wind} km/h` : "—"}</p>
          <div className="flex items-center gap-1.5 text-white/50 text-[11px] mt-2">
            <Droplets size={12} />
            {weather ? `${weather.humidity}% ${t.dashboard.weather.humidity}` : "—"}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-5 border-t border-white/10 flex-1">
        <p className="text-xs text-white/50 mb-3">{t.dashboard.weather.hourly}</p>
        <div className="flex items-center justify-between">
          {(weather?.hourly || []).map((f) => {
            const Icon = getIcon(f.cloud);
            return (
              <div key={f.time} className="flex flex-col items-center gap-1.5">
                <span className="text-[11px] text-white/50">{f.time}</span>
                <Icon size={16} className="text-lime" />
                <span className="text-xs font-semibold">{f.temp}°</span>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
