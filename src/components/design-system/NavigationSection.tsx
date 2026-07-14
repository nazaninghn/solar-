"use client";

import { useState } from "react";
import { LayoutDashboard, BarChart3, Battery, Search, Bell, ChevronDown } from "lucide-react";
import SectionHeader from "./SectionHeader";

const navItems = [
  { label: "Dashboard", active: true, icon: LayoutDashboard },
  { label: "Analytics", active: false, icon: BarChart3 },
  { label: "Battery Storage", active: false, icon: Battery },
];

const tabs = ["Overview", "Analytics", "Settings"];

export default function NavigationSection() {
  const [tab, setTab] = useState(tabs[0]);

  return (
    <section id="navigation" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Navigation"
        description="Sidebar, top navigation bar, and tab switcher patterns used across the dashboard shell."
      />

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Sidebar preview */}
        <div className="rounded-3xl border border-gray-100 overflow-hidden">
          <div className="bg-ink text-white p-5 h-72 flex flex-col">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-green to-secondary-green" />
              <span className="text-sm font-bold">
                Solar<span className="text-lime">Flow</span>
              </span>
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => (
                <div
                  key={item.label}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium ${
                    item.active ? "bg-white/10 text-white" : "text-white/50"
                  }`}
                >
                  <item.icon size={15} className={item.active ? "text-lime" : ""} />
                  {item.label}
                </div>
              ))}
            </nav>
            <div className="mt-auto flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-white/5">
              <div className="w-7 h-7 rounded-full bg-lime/20 flex items-center justify-center text-[10px] font-bold text-lime">JD</div>
              <span className="text-xs font-medium">Jane Doe</span>
            </div>
          </div>
          <p className="px-6 py-3 text-[11px] font-mono text-gray-300 bg-white">Sidebar — dark, fixed 260px</p>
        </div>

        {/* Top nav preview */}
        <div className="rounded-3xl border border-gray-100 overflow-hidden">
          <div className="bg-white h-72 flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <div className="relative w-40">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <div className="pl-8 pr-3 py-2 rounded-full bg-mist/50 text-[11px] text-gray-400">Search…</div>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative w-8 h-8 rounded-full flex items-center justify-center hover:bg-mist/60">
                  <Bell size={15} className="text-ink" />
                  <span className="absolute top-1.5 right-2 w-1.5 h-1.5 rounded-full bg-danger" />
                </div>
                <div className="flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full hover:bg-mist/60">
                  <div className="w-6 h-6 rounded-full bg-ink flex items-center justify-center text-[9px] font-bold text-lime">JD</div>
                  <ChevronDown size={12} className="text-gray-400" />
                </div>
              </div>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-xs text-gray-300">Page content area</p>
            </div>
          </div>
          <p className="px-6 py-3 text-[11px] font-mono text-gray-300 bg-white border-t border-gray-100">Top Navigation — search, notifications, profile</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="mt-5 rounded-3xl border border-gray-100 bg-white p-6">
        <h4 className="text-sm font-semibold text-ink mb-4">Tabs</h4>
        <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1 w-fit">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                tab === t ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-4">Active tab: <span className="font-semibold text-ink">{tab}</span></p>
      </div>
    </section>
  );
}
