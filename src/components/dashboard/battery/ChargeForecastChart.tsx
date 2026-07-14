"use client";

import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { chargeForecast } from "./data";

const actionColor: Record<string, string> = {
  charge: "#ADC825",
  discharge: "#4A70BE",
  hold: "#879DBA",
};

function ActionDot(props: { cx?: number; cy?: number; payload?: { action: string } }) {
  const { cx, cy, payload } = props;
  if (cx === undefined || cy === undefined || !payload) return null;
  return <circle cx={cx} cy={cy} r={4} fill={actionColor[payload.action]} stroke="white" strokeWidth={1.5} />;
}

export default function ChargeForecastChart() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-ink">Charge Forecast</h3>
          <p className="text-xs text-gray-400 mt-0.5">Predicted SOC · next 24 hours</p>
        </div>
        <div className="flex items-center gap-3">
          {Object.entries(actionColor).map(([action, color]) => (
            <div key={action} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-500 capitalize">{action}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="h-64 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chargeForecast}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#94a3b8" }} unit="%" domain={[0, 100]} />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "1px solid #e2e8f0", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
              formatter={(value: unknown, _name, item) => {
                const payload = (item as { payload?: { action?: string } })?.payload;
                return [`${Number(value)}% · ${payload?.action ?? ""}`, "SOC"];
              }}
            />
            <Line type="monotone" dataKey="soc" stroke="#293234" strokeWidth={2} dot={<ActionDot />} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
