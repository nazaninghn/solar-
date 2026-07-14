"use client";

import { LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, ResponsiveContainer, Tooltip, ReferenceLine } from "recharts";
import { TrendingUp, PiggyBank, CalendarRange, ArrowRightLeft } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";
import GaugeRadial from "../primitives/GaugeRadial";

const costBreakdown = [
  { name: "Grid Import", value: 34 }, { name: "Maintenance", value: 12 }, { name: "Financing", value: 18 }, { name: "Other", value: 8 },
];
const costColors = ["#305293", "#879DBA", "#4A70BE", "#E8E8EC"];

const costTrend = [
  { m: "Feb", v: 0.208 }, { m: "Mar", v: 0.197 }, { m: "Apr", v: 0.189 }, { m: "May", v: 0.183 }, { m: "Jun", v: 0.181 }, { m: "Jul", v: 0.184 },
];

const profitTimeline = [
  { m: "Jan", actual: 890, projected: null as number | null },
  { m: "Apr", actual: 1720, projected: null as number | null },
  { m: "Jul", actual: 2280, projected: 2280 },
  { m: "Oct", actual: null, projected: 1560 },
];

export default function FinancialSection() {
  return (
    <section id="financial" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Financial Components"
        description="ROI, cost, and forecast widgets that translate energy data into board-level financial language."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-ink text-white p-6 flex items-center gap-5">
          <GaugeRadial value={79} color="#D5F332" valueClassName="text-lg font-bold text-white" sublabel="7.9%" />
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp size={15} className="text-lime" />
              <h4 className="text-sm font-semibold">ROI</h4>
            </div>
            <p className="text-xs text-white/50 mt-1.5">Trailing 12-month average</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-primary-green/15 flex items-center justify-center shrink-0">
            <PiggyBank size={20} className="text-primary-green" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Monthly Savings</p>
            <p className="text-lg font-bold text-ink">€2,280</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-primary-green/15 flex items-center justify-center shrink-0">
            <CalendarRange size={20} className="text-primary-green" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Annual Savings</p>
            <p className="text-lg font-bold text-ink">€18,150</p>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-azure/15 flex items-center justify-center shrink-0">
            <ArrowRightLeft size={20} className="text-azure" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Revenue</p>
            <p className="text-lg font-bold text-ink">€760 <span className="text-xs text-gray-400 font-normal">/mo</span></p>
          </div>
        </div>

        <ChartCard title="Cost Breakdown" tag="Donut" height="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={costBreakdown} dataKey="value" nameKey="name" innerRadius={35} outerRadius={55} paddingAngle={2}>
                {costBreakdown.map((d, i) => <Cell key={d.name} fill={costColors[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Energy Cost Trend" tag="AreaChart" height="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={costTrend}>
              <defs>
                <linearGradient id="costTrend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#879DBA" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#879DBA" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Area type="monotone" dataKey="v" stroke="#879DBA" strokeWidth={2.5} fill="url(#costTrend)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Financial Forecast" tag="Confidence band" height="h-40" className="sm:col-span-2 xl:col-span-1">
          <div className="h-full flex flex-col justify-center gap-2">
            <p className="text-xs text-gray-400">Next quarter savings estimate</p>
            <p className="text-2xl font-bold text-ink">€5,890 <span className="text-sm font-normal text-gray-400">± €640</span></p>
            <div className="h-2 rounded-full bg-mist relative overflow-hidden mt-1">
              <div className="absolute inset-y-0 left-[30%] right-[15%] bg-lime/40 rounded-full" />
              <div className="absolute inset-y-0 left-[45%] w-1 bg-lime-dark" />
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Profit Timeline" tag="Actual vs Projected" height="h-40" className="sm:col-span-2 xl:col-span-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={profitTimeline}>
              <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <ReferenceLine x="Jul" stroke="#E8E8EC" strokeWidth={2} />
              <Line type="monotone" dataKey="actual" stroke="#3CB54A" strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false} />
              <Line type="monotone" dataKey="projected" stroke="#305293" strokeWidth={2.5} strokeDasharray="6 5" dot={{ r: 3 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </section>
  );
}
