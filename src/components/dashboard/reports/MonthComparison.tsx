"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { current, previous } from "./data";

const rows = [
  { key: "savings", label: "Savings", unit: "€", format: (v: number) => v.toLocaleString() },
  { key: "revenue", label: "Revenue", unit: "€", format: (v: number) => v.toLocaleString() },
  { key: "roi", label: "ROI", unit: "%", format: (v: number) => v.toFixed(1) },
  { key: "gridCost", label: "Grid Cost", unit: "€/kWh", format: (v: number) => v.toFixed(3) },
  { key: "carbonTons", label: "Carbon Reduction", unit: "t CO₂", format: (v: number) => v.toFixed(1) },
] as const;

export default function MonthComparison() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <h3 className="text-base font-semibold text-ink">Month-over-Month Comparison</h3>
      <p className="text-xs text-gray-400 mt-0.5">
        {current.month} {current.year} vs {previous.month} {previous.year}
      </p>

      <div className="mt-6 space-y-4">
        {rows.map((row, i) => {
          const curVal = current[row.key];
          const prevVal = previous[row.key];
          const delta = ((curVal - prevVal) / prevVal) * 100;
          const up = delta >= 0;
          const inverse = row.key === "gridCost";
          const positive = inverse ? !up : up;

          return (
            <motion.div
              key={row.key}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="flex items-center justify-between gap-4 pb-4 border-b border-gray-50 last:border-0 last:pb-0"
            >
              <div>
                <p className="text-sm font-medium text-ink">{row.label}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {row.format(prevVal)} {row.unit} → {row.format(curVal)} {row.unit}
                </p>
              </div>
              <div
                className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-full shrink-0 ${
                  positive ? "text-primary-green bg-primary-green/10" : "text-danger bg-danger/10"
                }`}
              >
                {up ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                {Math.abs(delta).toFixed(1)}%
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
