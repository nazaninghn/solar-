"use client";

import { Keyboard, Eye, Contrast, Volume2, Loader2 } from "lucide-react";
import SectionHeader from "./SectionHeader";

const principles = [
  { icon: Contrast, title: "WCAG AA Contrast", body: "Ink on warm-bg exceeds 12:1. Lime-dark on white exceeds 4.6:1 for text-sized use." },
  { icon: Keyboard, title: "Full Keyboard Navigation", body: "Every interactive element is reachable via Tab, operable via Enter/Space, and dismissible via Escape." },
  { icon: Eye, title: "Visible Focus States", body: "A 2px ring in ink/20 or lime-dark/40 appears on every focusable element — never suppressed." },
  { icon: Volume2, title: "Screen Reader Friendly", body: "Icon-only buttons carry aria-label; status changes announce via aria-live regions." },
];

export default function AccessibilityMotionSection() {
  return (
    <section id="accessibility" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Guidelines"
        title="Accessibility & Motion"
        description="How the system meets WCAG AA, and the timing/easing rules that make interactions feel fast and predictable rather than decorative."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-5">
        {principles.map((p) => (
          <div key={p.title} className="rounded-3xl bg-white border border-gray-100 p-6">
            <div className="w-10 h-10 rounded-2xl bg-mist flex items-center justify-center mb-4">
              <p.icon size={18} className="text-ink" />
            </div>
            <h4 className="text-sm font-semibold text-ink">{p.title}</h4>
            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{p.body}</p>
          </div>
        ))}
      </div>

      <div className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8">
        <h4 className="text-sm font-semibold text-ink mb-5">Motion in Practice</h4>
        <div className="grid sm:grid-cols-3 gap-5">
          <div>
            <p className="text-xs text-gray-400 mb-3">Hover — card lift (120ms)</p>
            <div className="rounded-2xl border border-gray-100 p-4 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150 cursor-pointer">
              <p className="text-sm font-semibold text-ink">Hover me</p>
              <p className="text-xs text-gray-400 mt-1">Elevation + lift</p>
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-3">Focus — ring (instant)</p>
            <input placeholder="Tab to me" className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-shadow" />
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-3">Loading — spinner (continuous)</p>
            <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-ink text-white text-sm w-fit">
              <Loader2 size={14} className="animate-spin" />
              Processing…
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
