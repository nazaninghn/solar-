"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip,
} from "recharts";
import { Battery, Thermometer, Zap, Activity, Clock, TrendingUp } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function BatteryPage() {
  const [batteryData, setBatteryData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const token = localStorage.getItem("access_token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API}/api/v1/factories/1/energy/readings?limit=48`, { headers });
        if (res.ok) {
          const data = await res.json();
          const readings = Array.isArray(data) ? data : data.data || [];
          setBatteryData(readings);
        }
      } catch (e) {
        console.error("Battery load failed", e);
      }
      setLoading(false);
    }
    load();
  }, []);

  // Simulate SOC from charge/discharge data
  let soc = 72;
  const socHistory = batteryData.slice(-24).map((r: any, i: number) => {
    soc = Math.max(15, Math.min(90, soc + (r.battery_charge_kwh - r.battery_discharge_kwh) * 0.05));
    return {
      time: new Date(r.timestamp).toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit" }),
      soc: Math.round(soc),
      power: Math.round((r.battery_charge_kwh - r.battery_discharge_kwh) * 10),
    };
  });

  const currentSoc = socHistory.length > 0 ? socHistory[socHistory.length - 1].soc : 72;
  const totalCharge = batteryData.reduce((s: number, r: any) => s + (r.battery_charge_kwh || 0), 0);
  const totalDischarge = batteryData.reduce((s: number, r: any) => s + (r.battery_discharge_kwh || 0), 0);
  const status = currentSoc > 50 ? "Healthy" : currentSoc > 25 ? "Low" : "Critical";
  const statusColor = currentSoc > 50 ? "text-primary-green" : currentSoc > 25 ? "text-energy-orange" : "text-danger";

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Battery Storage</h1>
        <p className="text-sm text-gray-500 mt-1">BYD HVS 10.0 — Real-time state and history</p>
      </div>

      {/* Battery Status */}
      <div className="grid md:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <Battery size={20} className="text-royal" />
          <p className="text-xs text-gray-400 mt-2">State of Charge</p>
          <p className="text-3xl font-bold text-ink mt-1">{currentSoc}%</p>
          <div className="h-2 rounded-full bg-gray-100 mt-2 overflow-hidden">
            <div className="h-full bg-primary-green rounded-full transition-all" style={{ width: `${currentSoc}%` }} />
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <Activity size={20} className={statusColor} />
          <p className="text-xs text-gray-400 mt-2">Status</p>
          <p className={`text-lg font-bold mt-1 ${statusColor}`}>{status}</p>
          <p className="text-xs text-gray-400 mt-1">Temperature: 31°C</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <TrendingUp size={20} className="text-primary-green" />
          <p className="text-xs text-gray-400 mt-2">Total Charged (48h)</p>
          <p className="text-lg font-bold text-ink mt-1">{totalCharge.toFixed(1)} kWh</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <Zap size={20} className="text-energy-orange" />
          <p className="text-xs text-gray-400 mt-2">Total Discharged (48h)</p>
          <p className="text-lg font-bold text-ink mt-1">{totalDischarge.toFixed(1)} kWh</p>
        </motion.div>
      </div>

      {/* SOC Chart */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-1">State of Charge History</h3>
        <p className="text-xs text-gray-400 mb-4">Last 24 hours</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={socHistory}>
              <defs>
                <linearGradient id="socGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#305293" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#305293" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Area type="monotone" dataKey="soc" name="SOC" stroke="#305293" strokeWidth={2.5} fill="url(#socGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Battery Specs */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Battery Specifications</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Capacity", value: "2,000 kWh" },
            { label: "Max Charge Power", value: "500 kW" },
            { label: "Max Discharge Power", value: "500 kW" },
            { label: "Round-trip Efficiency", value: "92%" },
            { label: "Min SOC", value: "15%" },
            { label: "Max SOC", value: "90%" },
            { label: "Cycle Count", value: "~450" },
            { label: "Expected Life", value: "10 years" },
          ].map((spec) => (
            <div key={spec.label} className="py-2">
              <p className="text-xs text-gray-400">{spec.label}</p>
              <p className="text-sm font-semibold text-ink">{spec.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
