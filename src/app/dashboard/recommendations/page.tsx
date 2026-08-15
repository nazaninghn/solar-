"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Brain, Battery, Zap, TrendingUp, ArrowRightLeft, Clock, CheckCircle2, XCircle } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Recommendation {
  id: number;
  type: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  confidence: number;
  expected_savings: number;
  start_time: string | null;
  end_time: string | null;
}

const typeIcons: Record<string, any> = {
  CHARGE_BATTERY: Battery,
  DISCHARGE_BATTERY: Battery,
  BUY_GRID_POWER: Zap,
  SELL_SURPLUS: ArrowRightLeft,
  SHIFT_LOAD: TrendingUp,
};

const priorityColors: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-700",
  HIGH: "bg-energy-orange/10 text-energy-orange",
  MEDIUM: "bg-royal/10 text-royal",
  LOW: "bg-gray-100 text-gray-500",
};

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const token = localStorage.getItem("access_token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API}/api/v1/factories/1/recommendations`, { headers });
        if (res.ok) {
          const data = await res.json();
          setRecs(Array.isArray(data) ? data : []);
        }
      } catch (e) {
        console.error("Recommendations load failed", e);
      }
      setLoading(false);
    }
    load();
  }, []);

  // If no API recs, show demo recommendations
  const displayRecs: Recommendation[] = recs.length > 0 ? recs : [
    { id: 1, type: "CHARGE_BATTERY", title: "Charge battery before peak hours", description: "Solar forecast is low tomorrow. Charge battery to 85% during off-peak to save during peak pricing.", status: "pending", priority: "HIGH", confidence: 0.87, expected_savings: 420, start_time: null, end_time: null },
    { id: 2, type: "DISCHARGE_BATTERY", title: "Use battery during peak pricing", description: "Grid price is near peak (€0.31/kWh). Discharge battery to reduce grid cost.", status: "pending", priority: "HIGH", confidence: 0.91, expected_savings: 280, start_time: null, end_time: null },
    { id: 3, type: "SELL_SURPLUS", title: "Sell surplus solar energy", description: "Solar surplus of ~120 kWh expected. Battery is 78% (sufficient). Export at €0.19/kWh.", status: "accepted", priority: "MEDIUM", confidence: 0.82, expected_savings: 0, start_time: null, end_time: null },
    { id: 4, type: "BUY_GRID_POWER", title: "Buy grid power during off-peak", description: "Very low solar expected. Current grid price is off-peak. Buy now to reduce peak cost.", status: "pending", priority: "MEDIUM", confidence: 0.78, expected_savings: 150, start_time: null, end_time: null },
  ];

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">AI Recommendations</h1>
        <p className="text-sm text-gray-500 mt-1">Smart energy optimization suggestions based on forecast, pricing, and battery state</p>
      </div>

      {/* Summary */}
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-gray-100">
          <p className="text-xs text-gray-400">Active Recommendations</p>
          <p className="text-2xl font-bold text-ink mt-1">{displayRecs.filter(r => r.status === "pending").length}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100">
          <p className="text-xs text-gray-400">Potential Savings</p>
          <p className="text-2xl font-bold text-primary-green mt-1">€{displayRecs.reduce((s, r) => s + r.expected_savings, 0).toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100">
          <p className="text-xs text-gray-400">Avg Confidence</p>
          <p className="text-2xl font-bold text-ink mt-1">{Math.round(displayRecs.reduce((s, r) => s + r.confidence, 0) / displayRecs.length * 100)}%</p>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {displayRecs.map((rec, i) => {
          const Icon = typeIcons[rec.type] || Brain;
          return (
            <motion.div
              key={rec.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white rounded-2xl p-5 border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl bg-lime/10 flex items-center justify-center shrink-0">
                  <Icon size={20} className="text-lime-dark" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-ink">{rec.title}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${priorityColors[rec.priority] || priorityColors.MEDIUM}`}>
                      {rec.priority}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed">{rec.description}</p>
                  <div className="flex items-center gap-4 mt-3">
                    <span className="text-xs text-gray-400 flex items-center gap-1"><Brain size={12} /> {Math.round(rec.confidence * 100)}% confidence</span>
                    {rec.expected_savings > 0 && <span className="text-xs text-primary-green font-semibold">+€{rec.expected_savings}</span>}
                    <span className="text-xs text-gray-400 flex items-center gap-1"><Clock size={12} /> {rec.status}</span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button className="px-3 py-1.5 rounded-lg bg-primary-green text-white text-xs font-semibold hover:bg-primary-green/90 transition-colors flex items-center gap-1">
                    <CheckCircle2 size={12} /> Approve
                  </button>
                  <button className="px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-medium text-gray-500 hover:bg-gray-50 transition-colors flex items-center gap-1">
                    <XCircle size={12} /> Reject
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
