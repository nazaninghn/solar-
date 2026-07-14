"use client";

import { AreaChart, Area, XAxis, ReferenceLine, ResponsiveContainer, Tooltip } from "recharts";
import { ArrowDownToLine, ArrowUpFromLine, TrendingUp, Sun, Moon, ArrowRightLeft } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";

const priceData = [
  { h: "00", p: 0.14 }, { h: "04", p: 0.11 }, { h: "08", p: 0.19 }, { h: "12", p: 0.15 },
  { h: "16", p: 0.21 }, { h: "18", p: 0.31 }, { h: "20", p: 0.26 }, { h: "22", p: 0.18 },
];

export default function GridSection() {
  return (
    <section id="grid" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Grid & Pricing"
        description="Buy/sell price signals and trading widgets that drive the buy/charge/sell decision layer."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-danger/10 flex items-center justify-center shrink-0">
            <ArrowDownToLine size={20} className="text-danger" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Electricity Buy Price</p>
            <p className="text-lg font-bold text-ink">€0.184<span className="text-xs text-gray-400 font-normal">/kWh</span></p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-primary-green/10 flex items-center justify-center shrink-0">
            <ArrowUpFromLine size={20} className="text-primary-green" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Electricity Sell Price</p>
            <p className="text-lg font-bold text-ink">€0.312<span className="text-xs text-gray-400 font-normal">/kWh</span></p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 sm:col-span-2 xl:col-span-1">
          <p className="text-xs text-gray-400 mb-3">Peak / Off-Peak Hours</p>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-danger/10">
              <Sun size={12} className="text-danger" />
              <span className="text-xs font-semibold text-danger">Peak 17–20</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-royal/10">
              <Moon size={12} className="text-royal" />
              <span className="text-xs font-semibold text-royal">Off-peak 00–06</span>
            </div>
          </div>
        </div>

        <ChartCard title="Price Forecast" tag="AreaChart" height="h-56" className="sm:col-span-2 xl:col-span-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={priceData}>
              <defs>
                <linearGradient id="gridPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#305293" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#305293" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="h" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} formatter={(v: unknown) => [`€${Number(v).toFixed(2)}`, "Price"]} />
              <ReferenceLine x="18" stroke="#EF4444" strokeDasharray="4 3" label={{ value: "Peak", position: "top", fontSize: 10, fill: "#EF4444" }} />
              <Area type="monotone" dataKey="p" stroke="#305293" strokeWidth={2.5} fill="url(#gridPrice)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-ink text-white p-6">
          <div className="flex items-center gap-2 mb-3">
            <ArrowRightLeft size={16} className="text-lime" />
            <h4 className="text-sm font-semibold">Energy Trading Widget</h4>
          </div>
          <div className="flex items-center justify-between text-xs text-white/50 mb-1">
            <span>Sell surplus now</span>
            <TrendingUp size={13} className="text-lime" />
          </div>
          <p className="text-2xl font-bold tracking-tight">120 kWh</p>
          <p className="text-xs text-white/50 mt-1">≈ €22 at current sell price</p>
          <button className="mt-4 w-full py-2.5 rounded-full bg-lime text-ink text-xs font-semibold hover:bg-lime/90 transition-colors">
            Execute Trade
          </button>
        </div>
      </div>
    </section>
  );
}
