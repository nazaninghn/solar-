"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import SectionHeader from "./SectionHeader";
import {
  colorGroups,
  typeScale,
  spacingScale,
  breakpoints,
  radiusScale,
  deviceFrames,
  shadowScale,
  zIndexScale,
  motionScale,
  iconSizes,
} from "./tokens";

function Swatch({ token }: { token: (typeof colorGroups)[0]["tokens"][0] }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard?.writeText(token.hex);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <button
      onClick={copy}
      className="text-left rounded-2xl border border-gray-100 overflow-hidden hover:shadow-md transition-shadow group"
    >
      <div className={`h-20 ${token.className} relative flex items-center justify-center`}>
        <span className="absolute top-2 right-2 text-white/80 opacity-0 group-hover:opacity-100 transition-opacity">
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </span>
      </div>
      <div className="p-3 bg-white">
        <p className="text-xs font-semibold text-ink">{token.name}</p>
        <p className="text-[11px] text-gray-400 mt-0.5 font-mono">{token.hex}</p>
        <p className="text-[11px] text-gray-400 mt-1 leading-snug">{token.usage}</p>
      </div>
    </button>
  );
}

export default function FoundationsSection() {
  return (
    <section id="foundations" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Foundations"
        title="Color, Type, Spacing & Grid"
        description="The base tokens every SolarFlow surface — marketing, auth, and dashboard — is built from."
      />

      {/* Colors */}
      <div className="space-y-8">
        {colorGroups.map((group) => (
          <div key={group.title}>
            <h3 className="text-sm font-semibold text-ink">{group.title}</h3>
            <p className="text-xs text-gray-400 mt-0.5 mb-4">{group.description}</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {group.tokens.map((t) => (
                <Swatch key={t.varName} token={t} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Typography */}
      <div className="mt-14">
        <h3 className="text-sm font-semibold text-ink mb-4">Typography Scale</h3>
        <div className="rounded-3xl border border-gray-100 divide-y divide-gray-50 bg-white">
          {typeScale.map((t) => (
            <div key={t.label} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 px-6 py-5">
              <span className="w-20 shrink-0 text-xs font-semibold text-gray-400 uppercase tracking-wide">{t.label}</span>
              <p className={`flex-1 ${t.className} truncate`}>{t.sample}</p>
              <span className="shrink-0 text-[11px] font-mono text-gray-400">{t.specs}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Spacing */}
      <div className="mt-14 grid lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Spacing Scale</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 space-y-3">
            {spacingScale.map((s) => (
              <div key={s.token} className="flex items-center gap-4">
                <span className="w-20 shrink-0 text-xs font-mono text-gray-500">{s.token}</span>
                <div className="h-2.5 rounded-full bg-lime" style={{ width: s.px }} />
                <span className="text-xs text-gray-400">{s.px}px</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Radius Scale</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 grid grid-cols-2 gap-4">
            {radiusScale.map((r) => (
              <div key={r.token} className="flex flex-col items-center gap-2">
                <div className={`w-16 h-16 bg-ink ${r.token}`} />
                <span className="text-[11px] font-mono text-gray-500">{r.token}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grid / Breakpoints */}
      <div className="mt-14">
        <h3 className="text-sm font-semibold text-ink mb-4">Responsive Grid Breakpoints</h3>
        <div className="rounded-3xl border border-gray-100 bg-white p-6">
          {breakpoints.map((b) => (
            <div key={b.token} className="flex items-center gap-4 py-2.5 border-b border-gray-50 last:border-0">
              <span className="w-12 shrink-0 text-xs font-mono font-bold text-ink">{b.token}</span>
              <div className="flex-1 h-2 rounded-full bg-mist overflow-hidden">
                <div className="h-full bg-royal rounded-full" style={{ width: `${(b.px / 1536) * 100}%` }} />
              </div>
              <span className="w-16 shrink-0 text-right text-xs text-gray-400 font-mono">{b.px}px</span>
              <span className="w-32 shrink-0 text-right text-xs text-gray-400 hidden sm:block">{b.usage}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Device frames + 12-col grid */}
      <div className="mt-14">
        <h3 className="text-sm font-semibold text-ink mb-4">Grid System — Device Frames</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {deviceFrames.map((d) => (
            <div key={d.token} className="rounded-3xl border border-gray-100 bg-white p-5">
              <p className="text-sm font-semibold text-ink">{d.token}</p>
              <p className="text-xs text-gray-400 font-mono">{d.px}px</p>
              <div className="grid gap-0.5 mt-4" style={{ gridTemplateColumns: `repeat(${d.cols}, 1fr)` }}>
                {Array.from({ length: d.cols }).map((_, i) => (
                  <div key={i} className="h-6 rounded-sm bg-lime/30" />
                ))}
              </div>
              <p className="text-[11px] text-gray-400 mt-2">{d.cols}-column grid, 8px gutter</p>
            </div>
          ))}
        </div>
      </div>

      {/* Shadow / Elevation */}
      <div className="mt-14 grid lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Shadow / Elevation Tokens</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 space-y-4">
            {shadowScale.map((s) => (
              <div key={s.token} className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-white shrink-0" style={{ boxShadow: s.css }} />
                <div>
                  <p className="text-xs font-mono font-semibold text-ink">{s.token}</p>
                  <p className="text-[11px] text-gray-400 mt-0.5">{s.usage}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Z-Index Scale</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 space-y-2.5">
            {zIndexScale.map((z) => (
              <div key={z.token} className="flex items-center justify-between gap-3">
                <span className="text-xs font-mono text-gray-600">{z.token}</span>
                <span className="text-xs font-mono font-bold text-ink w-8 text-right">{z.value}</span>
                <span className="text-[11px] text-gray-400 flex-1 text-right truncate">{z.usage}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Motion + Icon sizes */}
      <div className="mt-14 grid lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Motion / Animation Tokens</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 space-y-2.5">
            {motionScale.map((m) => (
              <div key={m.token} className="flex items-center justify-between gap-3">
                <span className="text-xs font-mono text-gray-600">{m.token}</span>
                <span className="text-xs font-mono font-bold text-ink text-right">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Icon Sizes</h3>
          <div className="rounded-3xl border border-gray-100 bg-white p-6 flex items-end justify-around">
            {iconSizes.map((i) => (
              <div key={i.token} className="flex flex-col items-center gap-2">
                <div className="rounded-lg bg-mist flex items-center justify-center" style={{ width: i.px, height: i.px }} />
                <span className="text-[10px] font-mono text-gray-400">{i.px}px</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
