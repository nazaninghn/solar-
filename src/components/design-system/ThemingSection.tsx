"use client";

import { useState } from "react";
import { Sun, Moon, Layers, SlidersHorizontal, Smartphone, Tablet, Monitor } from "lucide-react";
import SectionHeader from "./SectionHeader";

function PreviewCluster({ dark }: { dark: boolean }) {
  return (
    <div className={`rounded-2xl p-5 transition-colors ${dark ? "bg-ink" : "bg-warm-bg border border-gray-100"}`}>
      <div className="flex items-center justify-between">
        <span className={`text-xs font-semibold uppercase tracking-wide ${dark ? "text-white/50" : "text-gray-400"}`}>
          {dark ? "Dark surface" : "Light surface"}
        </span>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${dark ? "bg-lime/20 text-lime" : "bg-primary-green/10 text-primary-green"}`}>
          Sell
        </span>
      </div>
      <p className={`text-2xl font-bold mt-3 tracking-tight ${dark ? "text-white" : "text-ink"}`}>€2,280</p>
      <p className={`text-xs mt-1 ${dark ? "text-white/50" : "text-gray-500"}`}>Monthly savings, July 2026</p>
      <div className="flex items-center gap-2 mt-4">
        <button className={`px-4 py-2 rounded-full text-xs font-semibold ${dark ? "bg-lime text-ink" : "bg-ink text-white"}`}>
          Primary
        </button>
        <button
          className={`px-4 py-2 rounded-full text-xs font-semibold border ${
            dark ? "border-white/20 text-white" : "border-gray-200 text-ink"
          }`}
        >
          Secondary
        </button>
      </div>
      <input
        placeholder="you@company.com"
        className={`w-full mt-4 px-4 py-2.5 rounded-xl text-xs border focus:outline-none ${
          dark ? "bg-white/5 border-white/10 text-white placeholder:text-white/30" : "bg-white border-gray-200 text-ink placeholder:text-gray-400"
        }`}
      />
    </div>
  );
}

export default function ThemingSection() {
  const [previewTheme, setPreviewTheme] = useState<"light" | "dark">("light");

  return (
    <section id="theming" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Guidelines"
        title="Theming & System Guidelines"
        description="How color, layout, and component variants adapt across light and dark surfaces and screen sizes."
      />

      {/* Light / Dark toggle */}
      <div className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-sm font-semibold text-ink">Light Theme / Dark Theme</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              SolarFlow is light-first; dark surfaces (ink) are used for emphasis — sidebars, hero banners, stat cards.
            </p>
          </div>
          <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1">
            <button
              onClick={() => setPreviewTheme("light")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                previewTheme === "light" ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              <Sun size={13} />
              Light
            </button>
            <button
              onClick={() => setPreviewTheme("dark")}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                previewTheme === "dark" ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
              }`}
            >
              <Moon size={13} />
              Dark
            </button>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <PreviewCluster dark={previewTheme === "dark"} />
          <PreviewCluster dark={!(previewTheme === "dark")} />
        </div>
      </div>

      {/* Responsive / Auto Layout / Variants */}
      <div className="grid lg:grid-cols-3 gap-5 mt-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="w-10 h-10 rounded-2xl bg-royal/15 flex items-center justify-center mb-4">
            <Smartphone size={18} className="text-royal" />
          </div>
          <h4 className="text-sm font-semibold text-ink">Responsive Components</h4>
          <p className="text-xs text-gray-500 mt-2 leading-relaxed">
            Every component is built mobile-first. KPI grids collapse from 3–5 columns down to 1, the sidebar becomes
            a slide-in drawer below <code className="font-mono bg-mist px-1 rounded">lg</code>, and tables scroll
            horizontally rather than truncate.
          </p>
          <div className="flex items-center gap-3 mt-4 text-gray-300">
            <Smartphone size={16} />
            <Tablet size={18} />
            <Monitor size={20} className="text-ink" />
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="w-10 h-10 rounded-2xl bg-lime/15 flex items-center justify-center mb-4">
            <Layers size={18} className="text-lime-dark" />
          </div>
          <h4 className="text-sm font-semibold text-ink">Auto Layout</h4>
          <p className="text-xs text-gray-500 mt-2 leading-relaxed">
            Layout is Flexbox/Grid-driven with <code className="font-mono bg-mist px-1 rounded">gap</code> utilities
            instead of manual margins — components reflow predictably when content length changes.
          </p>
          <div className="flex items-center gap-2 mt-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-6 flex-1 rounded-lg bg-mist" />
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <div className="w-10 h-10 rounded-2xl bg-azure/15 flex items-center justify-center mb-4">
            <SlidersHorizontal size={18} className="text-azure" />
          </div>
          <h4 className="text-sm font-semibold text-ink">Variants</h4>
          <p className="text-xs text-gray-500 mt-2 leading-relaxed">
            Components expose variant props (e.g. Badge <code className="font-mono bg-mist px-1 rounded">tone</code>,
            Button <code className="font-mono bg-mist px-1 rounded">variant</code>) that switch a class map —
            no duplicated components per style.
          </p>
          <div className="flex flex-wrap gap-1.5 mt-4">
            <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-lime/20 text-lime-dark">success</span>
            <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-royal/15 text-royal">info</span>
            <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-danger/10 text-danger">danger</span>
          </div>
        </div>
      </div>
    </section>
  );
}
