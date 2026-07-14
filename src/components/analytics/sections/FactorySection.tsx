"use client";

import { BarChart, Bar, XAxis, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { MapPin, Factory, Cpu, Activity, Layers, Zap } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";
import StatusBadge, { StatusVariant } from "../primitives/StatusBadge";
import GaugeSemi from "../primitives/GaugeSemi";

const lines = [
  { name: "Line 1", kwh: 42 }, { name: "Line 2", kwh: 31 }, { name: "Line 3", kwh: 24 }, { name: "Line 4", kwh: 18 },
];

const zones = [
  { name: "Zone A — Assembly", load: 78, status: "healthy" as StatusVariant },
  { name: "Zone B — Packaging", load: 54, status: "healthy" as StatusVariant },
  { name: "Zone C — Cold Storage", load: 91, status: "warning" as StatusVariant },
  { name: "Zone D — Warehouse", load: 22, status: "offline" as StatusVariant },
];

const equipment = [
  { name: "Inverter 1", status: "healthy" as StatusVariant },
  { name: "Inverter 2", status: "warning" as StatusVariant },
  { name: "Battery Rack A", status: "charging" as StatusVariant },
  { name: "Meter Gateway", status: "healthy" as StatusVariant },
  { name: "Backup Genset", status: "offline" as StatusVariant },
  { name: "HVAC Controller", status: "critical" as StatusVariant },
];

const machines = [
  { name: "CNC Mill 3", kwh: 62 }, { name: "Press Line B", kwh: 48 }, { name: "Conveyor Belt 2", kwh: 21 },
];

const loadDist = [
  { name: "Production", value: 52 }, { name: "HVAC", value: 21 }, { name: "Lighting", value: 12 }, { name: "IT/Office", value: 15 },
];
const loadColors = ["#305293", "#4A70BE", "#ADC825", "#879DBA"];

const facilities = [
  { name: "Munich HQ", x: 60, y: 40, status: "healthy" as StatusVariant },
  { name: "Lyon Plant", x: 30, y: 55, status: "healthy" as StatusVariant },
  { name: "Turin Depot", x: 45, y: 65, status: "warning" as StatusVariant },
];

export default function FactorySection() {
  return (
    <section id="factory" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Factory & Maps"
        description="Zone-level and equipment-level visibility, plus stylized location and distribution maps."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <ChartCard title="Production Line Consumption" tag="BarChart" height="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={lines}>
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <Bar dataKey="kwh" fill="#305293" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Layers size={16} className="text-royal" />
            <h4 className="text-sm font-semibold text-ink">Factory Zones</h4>
          </div>
          <div className="space-y-3">
            {zones.map((z) => (
              <div key={z.name} className="flex items-center justify-between gap-2">
                <span className="text-xs text-gray-600 truncate">{z.name}</span>
                <StatusBadge status={z.status} />
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={16} className="text-ink" />
            <h4 className="text-sm font-semibold text-ink">Equipment Status</h4>
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            {equipment.map((e) => (
              <div key={e.name} className="rounded-xl bg-warm-bg px-3 py-2.5">
                <p className="text-[11px] font-medium text-ink truncate">{e.name}</p>
                <div className="mt-1"><StatusBadge status={e.status} /></div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={16} className="text-azure" />
            <h4 className="text-sm font-semibold text-ink">Machine Energy Usage</h4>
          </div>
          <div className="space-y-3">
            {machines.map((m) => (
              <div key={m.name}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-600">{m.name}</span>
                  <span className="font-semibold text-ink">{m.kwh} kWh</span>
                </div>
                <div className="h-1.5 rounded-full bg-mist overflow-hidden">
                  <div className="h-full rounded-full bg-azure" style={{ width: `${m.kwh}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <ChartCard title="Load Distribution" tag="Donut" height="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={loadDist} dataKey="value" nameKey="name" innerRadius={35} outerRadius={55} paddingAngle={2}>
                {loadDist.map((d, i) => <Cell key={d.name} fill={loadColors[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex items-center justify-center">
          <GaugeSemi value={1240} max={1500} color="#FDB94C" label="1,240" sublabel="Peak Load Indicator · kW" />
        </div>

        {/* Maps */}
        <div className="rounded-3xl bg-ink text-white p-6 sm:col-span-2 xl:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <MapPin size={16} className="text-lime" />
            <h4 className="text-sm font-semibold">Factory Location</h4>
          </div>
          <div className="relative h-32 rounded-2xl bg-white/5 overflow-hidden">
            <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 200 130">
              {Array.from({ length: 8 }).map((_, r) =>
                Array.from({ length: 12 }).map((_, c) => (
                  <circle key={`${r}-${c}`} cx={c * 18 + 10} cy={r * 18 + 10} r={1} fill="#fff" />
                ))
              )}
            </svg>
            <MapPin size={22} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full text-lime" fill="#D5F332" />
          </div>
          <p className="text-xs text-white/50 mt-3">Facility A — Munich, DE</p>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Factory size={16} className="text-royal" />
            <h4 className="text-sm font-semibold text-ink">Solar Irradiance Map</h4>
          </div>
          <div className="h-32 rounded-2xl overflow-hidden grid grid-cols-8 grid-rows-5 gap-0.5">
            {Array.from({ length: 40 }).map((_, i) => {
              const v = Math.max(10, Math.round(90 - Math.abs(i % 8 - 4) * 12 - Math.abs(Math.floor(i / 8) - 2) * 8));
              return <div key={i} style={{ backgroundColor: `rgba(213,243,50,${v / 100})` }} />;
            })}
          </div>
          <p className="text-xs text-gray-400 mt-3">Regional irradiance intensity, W/m²</p>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={16} className="text-royal" />
            <h4 className="text-sm font-semibold text-ink">Energy Distribution Map</h4>
          </div>
          <svg viewBox="0 0 200 110" className="w-full h-32">
            <line x1="30" y1="55" x2="100" y2="25" stroke="#ADC825" strokeWidth={2} />
            <line x1="30" y1="55" x2="100" y2="85" stroke="#4A70BE" strokeWidth={2} />
            <line x1="100" y1="25" x2="170" y2="30" stroke="#305293" strokeWidth={2} />
            <line x1="100" y1="85" x2="170" y2="80" stroke="#305293" strokeWidth={2} />
            <circle cx="30" cy="55" r="10" fill="#293234" />
            <text x="30" y="59" textAnchor="middle" fontSize={9} fill="#fff">PV</text>
            <circle cx="100" cy="25" r="8" fill="#ADC825" />
            <text x="100" y="28" textAnchor="middle" fontSize={8} fill="#293234">Batt</text>
            <circle cx="100" cy="85" r="8" fill="#4A70BE" />
            <text x="100" y="88" textAnchor="middle" fontSize={8} fill="#fff">Load</text>
            <circle cx="170" cy="30" r="7" fill="#305293" />
            <circle cx="170" cy="80" r="7" fill="#305293" />
          </svg>
          <p className="text-xs text-gray-400 mt-1">Source-to-load distribution topology</p>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 sm:col-span-2 xl:col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} className="text-azure" />
            <h4 className="text-sm font-semibold text-ink">Multiple Facility Map</h4>
          </div>
          <div className="relative h-32 rounded-2xl bg-warm-bg overflow-hidden">
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path d="M10,20 Q50,-5 90,25 Q100,60 70,90 Q40,105 15,75 Q-5,45 10,20 Z" fill="#E8E8EC" />
              {facilities.map((f) => (
                <g key={f.name}>
                  <circle cx={f.x} cy={f.y} r={3} fill={f.status === "healthy" ? "#3CB54A" : "#FDB94C"} />
                  <circle cx={f.x} cy={f.y} r={6} fill={f.status === "healthy" ? "#3CB54A" : "#FDB94C"} opacity={0.25} />
                </g>
              ))}
            </svg>
          </div>
          <div className="flex flex-wrap gap-3 mt-3">
            {facilities.map((f) => (
              <div key={f.name} className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${f.status === "healthy" ? "bg-primary-green" : "bg-energy-orange"}`} />
                <span className="text-[10px] text-gray-500">{f.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
