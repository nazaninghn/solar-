"use client";

import { motion } from "framer-motion";
import { forecast, weatherIcon, weatherLabel } from "./data";

const badgeStyles: Record<string, string> = {
  Sell: "bg-lime/20 text-lime-dark",
  Charge: "bg-royal/15 text-royal",
  Buy: "bg-danger/10 text-danger",
  Hold: "bg-mist text-gray-500",
};

export default function ForecastTable() {
  return (
    <motion.div
      id="forecast-table"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 overflow-hidden"
    >
      <div className="px-6 lg:px-8 py-6">
        <h3 className="text-base font-semibold text-ink">7-Day Forecast Breakdown</h3>
        <p className="text-xs text-gray-400 mt-0.5">Detailed day-by-day prediction and recommended action</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[720px]">
          <thead>
            <tr className="border-y border-gray-100 bg-mist/40">
              <th className="text-left font-semibold text-gray-500 px-6 lg:px-8 py-3 text-xs uppercase tracking-wide">Day</th>
              <th className="text-left font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Weather</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Solar</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Consumption</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Battery</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Grid Price</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Savings</th>
              <th className="text-right font-semibold text-gray-500 px-6 lg:px-8 py-3 text-xs uppercase tracking-wide">Action</th>
            </tr>
          </thead>
          <tbody>
            {forecast.map((d, i) => {
              const Icon = weatherIcon[d.weather];
              return (
                <tr key={d.day} className={`hover:bg-mist/30 transition-colors ${i !== forecast.length - 1 ? "border-b border-gray-50" : ""}`}>
                  <td className="px-6 lg:px-8 py-3.5">
                    <p className="font-semibold text-ink">{i === 0 ? "Today" : d.day}</p>
                    <p className="text-xs text-gray-400">{d.date}</p>
                  </td>
                  <td className="px-3 py-3.5">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Icon size={16} className="text-royal shrink-0" />
                      <span className="text-xs">{weatherLabel[d.weather]}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3.5 text-right font-medium text-lime-dark">{d.solarKwh.toFixed(1)} kWh</td>
                  <td className="px-3 py-3.5 text-right font-medium text-azure">{d.consumptionKwh.toFixed(1)} kWh</td>
                  <td className="px-3 py-3.5 text-right font-medium text-royal">{d.batterySoc}%</td>
                  <td className="px-3 py-3.5 text-right font-medium text-gray-600">€{d.gridPrice.toFixed(2)}</td>
                  <td className="px-3 py-3.5 text-right font-semibold text-primary-green">€{d.savings.toFixed(1)}</td>
                  <td className="px-6 lg:px-8 py-3.5 text-right">
                    <span className={`inline-block text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded-full ${badgeStyles[d.recommendation]}`}>
                      {d.recommendation}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
