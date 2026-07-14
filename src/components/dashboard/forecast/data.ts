import { Sun, CloudSun, Cloud, CloudRain, LucideIcon } from "lucide-react";

export type WeatherKind = "sunny" | "partly-cloudy" | "cloudy" | "rain";

export const weatherIcon: Record<WeatherKind, LucideIcon> = {
  sunny: Sun,
  "partly-cloudy": CloudSun,
  cloudy: Cloud,
  rain: CloudRain,
};

export const weatherLabel: Record<WeatherKind, string> = {
  sunny: "Sunny",
  "partly-cloudy": "Partly Cloudy",
  cloudy: "Cloudy",
  rain: "Light Rain",
};

export interface ForecastDay {
  day: string;
  date: string;
  weather: WeatherKind;
  tempHigh: number;
  tempLow: number;
  solarKwh: number;
  consumptionKwh: number;
  batterySoc: number;
  gridPrice: number;
  costWithoutOptimization: number;
  costWithOptimization: number;
  savings: number;
  recommendation: "Sell" | "Charge" | "Hold" | "Buy";
}

export const forecast: ForecastDay[] = [
  {
    day: "Mon",
    date: "Jul 14",
    weather: "sunny",
    tempHigh: 27,
    tempLow: 16,
    solarKwh: 44.2,
    consumptionKwh: 31.6,
    batterySoc: 84,
    gridPrice: 0.18,
    costWithoutOptimization: 38.4,
    costWithOptimization: 21.1,
    savings: 17.3,
    recommendation: "Sell",
  },
  {
    day: "Tue",
    date: "Jul 15",
    weather: "partly-cloudy",
    tempHigh: 25,
    tempLow: 15,
    solarKwh: 36.8,
    consumptionKwh: 32.1,
    batterySoc: 71,
    gridPrice: 0.2,
    costWithoutOptimization: 39.1,
    costWithOptimization: 24.6,
    savings: 14.5,
    recommendation: "Charge",
  },
  {
    day: "Wed",
    date: "Jul 16",
    weather: "sunny",
    tempHigh: 29,
    tempLow: 17,
    solarKwh: 47.5,
    consumptionKwh: 30.9,
    batterySoc: 92,
    gridPrice: 0.22,
    costWithoutOptimization: 40.8,
    costWithOptimization: 19.7,
    savings: 21.1,
    recommendation: "Sell",
  },
  {
    day: "Thu",
    date: "Jul 17",
    weather: "sunny",
    tempHigh: 30,
    tempLow: 18,
    solarKwh: 48.9,
    consumptionKwh: 33.4,
    batterySoc: 95,
    gridPrice: 0.31,
    costWithoutOptimization: 45.2,
    costWithOptimization: 18.4,
    savings: 26.8,
    recommendation: "Sell",
  },
  {
    day: "Fri",
    date: "Jul 18",
    weather: "cloudy",
    tempHigh: 22,
    tempLow: 14,
    solarKwh: 24.3,
    consumptionKwh: 34.2,
    batterySoc: 58,
    gridPrice: 0.19,
    costWithoutOptimization: 37.6,
    costWithOptimization: 27.9,
    savings: 9.7,
    recommendation: "Buy",
  },
  {
    day: "Sat",
    date: "Jul 19",
    weather: "rain",
    tempHigh: 19,
    tempLow: 13,
    solarKwh: 14.1,
    consumptionKwh: 27.8,
    batterySoc: 41,
    gridPrice: 0.16,
    costWithoutOptimization: 30.5,
    costWithOptimization: 24.3,
    savings: 6.2,
    recommendation: "Buy",
  },
  {
    day: "Sun",
    date: "Jul 20",
    weather: "partly-cloudy",
    tempHigh: 23,
    tempLow: 15,
    solarKwh: 33.6,
    consumptionKwh: 26.4,
    batterySoc: 68,
    gridPrice: 0.17,
    costWithoutOptimization: 32.1,
    costWithOptimization: 22.8,
    savings: 9.3,
    recommendation: "Hold",
  },
];

export const totals = {
  solarKwh: forecast.reduce((s, d) => s + d.solarKwh, 0),
  consumptionKwh: forecast.reduce((s, d) => s + d.consumptionKwh, 0),
  savings: forecast.reduce((s, d) => s + d.savings, 0),
  costWithout: forecast.reduce((s, d) => s + d.costWithoutOptimization, 0),
  costWith: forecast.reduce((s, d) => s + d.costWithOptimization, 0),
  avgBattery: Math.round(forecast.reduce((s, d) => s + d.batterySoc, 0) / forecast.length),
};
