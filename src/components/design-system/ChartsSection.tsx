"use client";

import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import SectionHeader from "./SectionHeader";

const data = [
  { m: "Mon", a: 40, b: 24 },
  { m: "Tue", a: 55, b: 30 },
  { m: "Wed", a: 48, b: 28 },
  { m: "Thu", a: 70, b: 35 },
  { m: "Fri", a: 62, b: 32 },
  { m: "Sat", a: 45, b: 20 },
  { m: "Sun", a: 58, b: 26 },
];

function ChartCard({ title, tag, children }: { title: string; tag: string; children: React.ReactNode }) {
  return (
    <div className="rounded-3xl bg-white border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-ink">{title}</h4>
        <span className="text-[11px] font-mono text-gray-300">{tag}</span>
      </div>
      <div className="h-48">{children}</div>
    </div>
  );
}

export default function ChartsSection() {
  return (
    <section id="charts" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Charts"
        description="Built on Recharts with consistent gradient fills, 11px muted axis labels, and 2.5px stroke weight."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <ChartCard title="Area Chart" tag="AreaChart">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="dsArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Area type="monotone" dataKey="a" stroke="#ADC825" strokeWidth={2.5} fill="url(#dsArea)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Line Chart" tag="LineChart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Line type="monotone" dataKey="a" stroke="#305293" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="b" stroke="#4A70BE" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Bar Chart" tag="BarChart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="m" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Bar dataKey="a" fill="#879DBA" radius={[6, 6, 0, 0]} />
              <Bar dataKey="b" fill="#ADC825" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Radial Gauge" tag="RadialBarChart">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="100%"
              barSize={14}
              data={[{ value: 68, fill: "#D5F332" }]}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar background={{ fill: "#F7F6F1" }} dataKey="value" cornerRadius={20} />
            </RadialBarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Sparkline" tag="LineChart (minimal)">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <Line type="monotone" dataKey="a" stroke="#3CB54A" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-ink text-white p-6 flex flex-col justify-center">
          <p className="text-xs text-white/50 uppercase tracking-widest mb-2">Series Colors</p>
          {[
            { name: "Solar / Positive", hex: "#ADC825" },
            { name: "Consumption / Info", hex: "#4A70BE" },
            { name: "Grid / Battery", hex: "#305293" },
            { name: "Neutral / Baseline", hex: "#879DBA" },
          ].map((s) => (
            <div key={s.name} className="flex items-center gap-2.5 py-1.5">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: s.hex }} />
              <span className="text-xs text-white/70">{s.name}</span>
              <span className="ml-auto text-[11px] font-mono text-white/30">{s.hex}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
