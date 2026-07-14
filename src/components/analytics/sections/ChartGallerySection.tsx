"use client";

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Treemap,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";
import GaugeSemi from "../primitives/GaugeSemi";
import GaugeRadial from "../primitives/GaugeRadial";

const weekly = [
  { d: "Mon", solar: 40, load: 24 },
  { d: "Tue", solar: 55, load: 30 },
  { d: "Wed", solar: 48, load: 28 },
  { d: "Thu", solar: 70, load: 35 },
  { d: "Fri", solar: 62, load: 32 },
  { d: "Sat", solar: 45, load: 20 },
  { d: "Sun", solar: 58, load: 26 },
];

const stacked = weekly.map((w) => ({ d: w.d, self: w.load * 0.6, grid: w.load * 0.4 }));

const zones = [
  { name: "Zone A", value: 38 },
  { name: "Zone B", value: 27 },
  { name: "Zone C", value: 19 },
  { name: "Zone D", value: 16 },
];
const pieColors = ["#ADC825", "#4A70BE", "#305293", "#879DBA"];

const scatterData = Array.from({ length: 24 }, (_, i) => ({
  x: i,
  y: Math.round(30 + 55 * Math.sin(i / 3.5) + Math.random() * 12),
}));

const radarData = [
  { metric: "Uptime", value: 94 },
  { metric: "Efficiency", value: 82 },
  { metric: "Health", value: 96 },
  { metric: "Accuracy", value: 88 },
  { metric: "Safety", value: 99 },
];

const treemapData = [
  { name: "Line 1", size: 4200 },
  { name: "Line 2", size: 3100 },
  { name: "Line 3", size: 2400 },
  { name: "HVAC", size: 1800 },
  { name: "Lighting", size: 900 },
];

const waterfall = [
  { label: "Revenue", base: 0, value: 760 },
  { label: "Savings", base: 760, value: 2280 },
  { label: "Grid Cost", base: 0, value: -640 },
  { label: "Maint.", base: 0, value: -180 },
  { label: "Net", base: 0, value: 2220, isTotal: true },
];

const heatmapDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const heatmapHours = ["00", "04", "08", "12", "16", "20"];
const heatmapValue = (d: number, h: number) => {
  const base = Math.sin((h / 6) * Math.PI) * 60 + 40 - d * 3;
  return Math.max(4, Math.min(100, Math.round(base)));
};

const timelineEvents = [
  { label: "Charging", start: 0, end: 6, color: "bg-lime-dark" },
  { label: "Hold", start: 6, end: 9, color: "bg-steel" },
  { label: "Discharging", start: 9, end: 18, color: "bg-azure" },
  { label: "Charging", start: 18, end: 24, color: "bg-lime-dark" },
];

export default function ChartGallerySection() {
  return (
    <section id="charts" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Foundations"
        title="Chart Gallery"
        description="Every fundamental chart type in the system — the building blocks that domain widgets below are composed from."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <ChartCard title="Line Chart" tag="LineChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Line type="monotone" dataKey="solar" stroke="#ADC825" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="load" stroke="#4A70BE" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Area Chart" tag="AreaChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={weekly}>
              <defs>
                <linearGradient id="gArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ADC825" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ADC825" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Area type="monotone" dataKey="solar" stroke="#ADC825" strokeWidth={2.5} fill="url(#gArea)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Bar Chart" tag="BarChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Bar dataKey="solar" fill="#ADC825" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Horizontal Bar Chart" tag="BarChart layout=vertical" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={zones} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} width={50} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Bar dataKey="value" fill="#305293" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Stacked Bar Chart" tag="BarChart stackId" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stacked}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Bar dataKey="self" stackId="a" fill="#ADC825" radius={[0, 0, 0, 0]} />
              <Bar dataKey="grid" stackId="a" fill="#879DBA" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Grouped Bar Chart" tag="BarChart grouped" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weekly} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Bar dataKey="solar" fill="#ADC825" radius={[6, 6, 0, 0]} />
              <Bar dataKey="load" fill="#4A70BE" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Pie Chart" tag="PieChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={zones} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70}>
                {zones.map((z, i) => (
                  <Cell key={z.name} fill={pieColors[i]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Donut Chart" tag="PieChart innerRadius" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={zones} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2}>
                {zones.map((z, i) => (
                  <Cell key={z.name} fill={pieColors[i]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Scatter Plot" tag="ScatterChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="x" type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} unit="h" />
              <YAxis dataKey="y" type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Scatter data={scatterData} fill="#305293" />
            </ScatterChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Radar Chart" tag="RadarChart" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="#f1f5f9" />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
              <Radar dataKey="value" stroke="#ADC825" fill="#ADC825" fillOpacity={0.3} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Treemap" tag="Treemap" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap data={treemapData} dataKey="size" stroke="#fff" fill="#305293" />
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Waterfall Chart" tag="BarChart floating" height="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={waterfall}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Bar dataKey="base" stackId="w" fill="transparent" />
              <Bar dataKey="value" stackId="w" radius={[4, 4, 4, 4]}>
                {waterfall.map((w, i) => (
                  <Cell key={i} fill={w.isTotal ? "#293234" : w.value >= 0 ? "#ADC825" : "#EF4444"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Heatmap" tag="CSS grid" height="h-48">
          <div className="flex flex-col justify-center h-full gap-1">
            {heatmapDays.map((day, d) => (
              <div key={day} className="flex items-center gap-1">
                <span className="w-7 text-[9px] text-gray-400">{day}</span>
                <div className="flex gap-1 flex-1">
                  {heatmapHours.map((h, hi) => {
                    const v = heatmapValue(d, hi);
                    return (
                      <div
                        key={h}
                        className="flex-1 aspect-square rounded"
                        style={{ backgroundColor: `rgba(173, 200, 37, ${v / 100})` }}
                        title={`${day} ${h}:00 — ${v}%`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Timeline Chart" tag="Custom track" height="h-48">
          <div className="flex flex-col justify-center h-full gap-3">
            <div className="relative h-6 rounded-full bg-mist overflow-hidden flex">
              {timelineEvents.map((e, i) => (
                <div
                  key={i}
                  className={`h-full ${e.color}`}
                  style={{ width: `${((e.end - e.start) / 24) * 100}%` }}
                  title={`${e.label} ${e.start}:00–${e.end}:00`}
                />
              ))}
            </div>
            <div className="flex flex-wrap gap-3">
              {[...new Map(timelineEvents.map((e) => [e.label, e.color])).entries()].map(([label, color]) => (
                <div key={label} className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-[10px] text-gray-500">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Semi-circle Gauge" tag="Custom SVG arc" height="h-48">
          <div className="flex items-center justify-center h-full">
            <GaugeSemi value={72} label="72%" sublabel="Grid Independence" color="#305293" />
          </div>
        </ChartCard>

        <ChartCard title="Circular Progress / Radial" tag="RadialBar / SVG" height="h-48">
          <div className="flex items-center justify-center h-full gap-4">
            <GaugeRadial value={68} color="#D5F332" sublabel="SOC" />
            <GaugeRadial value={94} size={72} stroke={7} color="#3CB54A" sublabel="Uptime" />
          </div>
        </ChartCard>

        <ChartCard title="Sparkline / Mini Chart" tag="LineChart minimal" height="h-48">
          <div className="flex flex-col justify-center h-full gap-6">
            {[
              { label: "Production", color: "#ADC825" },
              { label: "Consumption", color: "#4A70BE" },
            ].map((s) => (
              <div key={s.label}>
                <p className="text-xs text-gray-400 mb-1">{s.label}</p>
                <div className="h-10">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={weekly}>
                      <Line type="monotone" dataKey={s.label === "Production" ? "solar" : "load"} stroke={s.color} strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </section>
  );
}
