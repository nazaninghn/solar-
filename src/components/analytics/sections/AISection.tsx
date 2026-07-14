"use client";

import { LineChart, Line, XAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Sparkles, ShieldAlert, ThumbsUp, SlidersHorizontal, HeartPulse, PiggyBank, Target, AlertOctagon } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";
import ConfidenceMeter from "../primitives/ConfidenceMeter";
import GaugeRadial from "../primitives/GaugeRadial";

const forecastVsActual = [
  { t: "00", predicted: 12, actual: 14 },
  { t: "06", predicted: 120, actual: 110 },
  { t: "12", predicted: 780, actual: 802 },
  { t: "18", predicted: 210, actual: 198 },
  { t: "24", predicted: 15, actual: 18 },
];

const riskFactors = [
  { label: "Inverter 2 efficiency drift", severity: "medium" as const },
  { label: "Grid price spike Thursday", severity: "low" as const },
  { label: "Battery cell temp trending up", severity: "high" as const },
];

const severityColor = { low: "bg-primary-green", medium: "bg-energy-orange", high: "bg-danger" };

export default function AISection() {
  return (
    <section id="ai" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="AI Components"
        description="Confidence, risk, and scoring widgets that make model output legible to non-technical operators."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={16} className="text-lime-dark" />
            <h4 className="text-sm font-semibold text-ink">Prediction Confidence</h4>
          </div>
          <ConfidenceMeter label="Next 24h Solar Forecast" value={94} detail="±5% margin" />
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert size={16} className="text-energy-orange" />
            <h4 className="text-sm font-semibold text-ink">Risk Indicator</h4>
          </div>
          <div className="flex items-center gap-4">
            <GaugeSemiWrapper value={32} color="#FDB94C" />
            <div>
              <p className="text-xs text-gray-400">Overall facility risk</p>
              <p className="text-lg font-bold text-energy-orange">Low–Medium</p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-5">
          <GaugeRadial value={87} color="#ADC825" sublabel="Score" />
          <div>
            <div className="flex items-center gap-2">
              <ThumbsUp size={15} className="text-lime-dark" />
              <h4 className="text-sm font-semibold text-ink">Recommendation Score</h4>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              6 of 7 pending recommendations scored above 80% expected value.
            </p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-5">
          <GaugeRadial value={73} color="#4A70BE" sublabel="Score" />
          <div>
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={15} className="text-azure" />
              <h4 className="text-sm font-semibold text-ink">Energy Optimization Score</h4>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              Room to improve — battery dispatch timing lags optimal by ~40 min/day.
            </p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-5">
          <GaugeRadial value={96} color="#3CB54A" sublabel="Score" />
          <div>
            <div className="flex items-center gap-2">
              <HeartPulse size={15} className="text-primary-green" />
              <h4 className="text-sm font-semibold text-ink">Battery Health Score</h4>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
              96% state of health — degradation tracking ahead of the 8-year model.
            </p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Target size={16} className="text-royal" />
            <h4 className="text-sm font-semibold text-ink">AI Confidence Meter</h4>
          </div>
          <ConfidenceMeter label="Battery dispatch model" value={82} detail="v3.2, retrained 4d ago" />
        </div>

        <div className="rounded-3xl bg-ink text-white p-6">
          <div className="flex items-center gap-2">
            <PiggyBank size={16} className="text-lime" />
            <h4 className="text-sm font-semibold">Expected Savings Card</h4>
          </div>
          <p className="text-3xl font-bold mt-3 tracking-tight">€391</p>
          <p className="text-xs text-white/50 mt-1">If all pending recommendations are approved</p>
          <div className="mt-4">
            <ConfidenceMeterDark value={83} />
          </div>
        </div>

        <ChartCard title="Forecast Accuracy" tag="Predicted vs Actual" height="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecastVsActual}>
              <XAxis dataKey="t" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Line type="monotone" dataKey="predicted" stroke="#879DBA" strokeWidth={2} strokeDasharray="4 3" dot={false} />
              <Line type="monotone" dataKey="actual" stroke="#ADC825" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertOctagon size={16} className="text-danger" />
            <h4 className="text-sm font-semibold text-ink">Energy Risk Card</h4>
          </div>
          <div className="space-y-2.5">
            {riskFactors.map((r) => (
              <div key={r.label} className="flex items-center gap-2.5">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${severityColor[r.severity]}`} />
                <p className="text-xs text-gray-600">{r.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function GaugeSemiWrapper({ value, color }: { value: number; color: string }) {
  const radius = 34;
  const arcLength = Math.PI * radius;
  const offset = arcLength * (1 - value / 100);
  return (
    <svg width={84} height={48} viewBox="0 0 84 48">
      <path d="M 8 42 A 34 34 0 0 1 76 42" stroke="#E8E8EC" strokeWidth={8} strokeLinecap="round" fill="none" />
      <path d="M 8 42 A 34 34 0 0 1 76 42" stroke={color} strokeWidth={8} strokeLinecap="round" fill="none" strokeDasharray={arcLength} strokeDashoffset={offset} />
    </svg>
  );
}

function ConfidenceMeterDark({ value }: { value: number }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] text-white/50">Confidence</span>
        <span className="text-[11px] font-bold text-lime">{value}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full bg-lime" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
