"use client";

import { motion } from "framer-motion";
import { monthly } from "./data";

export default function ReportsTable() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-3xl bg-white border border-gray-100 overflow-hidden"
    >
      <div className="px-6 lg:px-8 py-6">
        <h3 className="text-base font-semibold text-ink">12-Month Financial Detail</h3>
        <p className="text-xs text-gray-400 mt-0.5">Production, savings, revenue, and carbon impact by month</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[820px]">
          <thead>
            <tr className="border-y border-gray-100 bg-mist/40">
              <th className="text-left font-semibold text-gray-500 px-6 lg:px-8 py-3 text-xs uppercase tracking-wide">Month</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Solar</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Consumption</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Savings</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Revenue</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">ROI</th>
              <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Grid Cost</th>
              <th className="text-right font-semibold text-gray-500 px-6 lg:px-8 py-3 text-xs uppercase tracking-wide">Carbon</th>
            </tr>
          </thead>
          <tbody>
            {monthly.map((m, i) => (
              <tr key={`${m.month}-${m.year}`} className={`hover:bg-mist/30 transition-colors ${i !== monthly.length - 1 ? "border-b border-gray-50" : ""}`}>
                <td className="px-6 lg:px-8 py-3.5">
                  <p className="font-semibold text-ink">{m.month} {m.year}</p>
                </td>
                <td className="px-3 py-3.5 text-right text-gray-600">{m.solarKwh.toLocaleString()} kWh</td>
                <td className="px-3 py-3.5 text-right text-gray-600">{m.consumptionKwh.toLocaleString()} kWh</td>
                <td className="px-3 py-3.5 text-right font-semibold text-primary-green">€{m.savings.toLocaleString()}</td>
                <td className="px-3 py-3.5 text-right font-medium text-azure">€{m.revenue.toLocaleString()}</td>
                <td className="px-3 py-3.5 text-right font-medium text-lime-dark">{m.roi.toFixed(1)}%</td>
                <td className="px-3 py-3.5 text-right text-gray-600">€{m.gridCost.toFixed(3)}</td>
                <td className="px-6 lg:px-8 py-3.5 text-right font-medium text-secondary-green">{m.carbonTons.toFixed(1)} t</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
