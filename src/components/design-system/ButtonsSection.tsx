"use client";

import { ArrowRight, Download, Loader2, Plus, Check, AlertTriangle } from "lucide-react";
import SectionHeader from "./SectionHeader";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6 py-5 border-b border-gray-50 last:border-0">
      <span className="w-28 shrink-0 text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</span>
      <div className="flex flex-wrap items-center gap-3">{children}</div>
    </div>
  );
}

export default function ButtonsSection() {
  return (
    <section id="buttons" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Buttons"
        description="Pill-shaped, fully rounded buttons in seven variants across three sizes, plus icon/FAB forms and every interaction state."
      />

      <div className="rounded-3xl border border-gray-100 bg-white px-6 lg:px-8">
        <Row label="Variants">
          <button className="px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors">Primary</button>
          <button className="px-5 py-2.5 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors">Accent</button>
          <button className="px-5 py-2.5 rounded-full bg-mist text-ink text-sm font-semibold hover:bg-mist/70 transition-colors">Secondary</button>
          <button className="px-5 py-2.5 rounded-full border border-gray-200 text-ink text-sm font-semibold hover:bg-mist/60 transition-colors">Outline</button>
          <button className="px-5 py-2.5 rounded-full text-ink text-sm font-semibold hover:bg-mist/60 transition-colors">Ghost</button>
          <button className="px-5 py-2.5 rounded-full bg-danger text-white text-sm font-semibold hover:bg-danger/90 transition-colors">Destructive</button>
          <button className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-success text-white text-sm font-semibold hover:bg-success/90 transition-colors">
            <Check size={14} />
            Success
          </button>
          <button className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-warning text-white text-sm font-semibold hover:bg-warning/90 transition-colors">
            <AlertTriangle size={14} />
            Warning
          </button>
        </Row>

        <Row label="Icon / FAB">
          <button className="w-10 h-10 rounded-full bg-ink text-white flex items-center justify-center hover:bg-black transition-colors" aria-label="Add">
            <Plus size={16} />
          </button>
          <button className="w-14 h-14 rounded-full bg-lime text-ink flex items-center justify-center shadow-lg shadow-lime/30 hover:bg-lime/90 hover:shadow-xl transition-all" aria-label="Floating action">
            <Plus size={22} />
          </button>
        </Row>

        <Row label="Sizes">
          <button className="px-3.5 py-1.5 rounded-full bg-ink text-white text-xs font-semibold">Small</button>
          <button className="px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold">Medium</button>
          <button className="px-7 py-3.5 rounded-full bg-ink text-white text-base font-semibold">Large</button>
        </Row>

        <Row label="With Icon">
          <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors">
            Continue
            <ArrowRight size={15} className="group-hover:translate-x-0.5" />
          </button>
          <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors">
            <Download size={15} />
            Download
          </button>
        </Row>

        <Row label="States">
          <button className="px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold">Default</button>
          <button className="px-5 py-2.5 rounded-full bg-black text-white text-sm font-semibold ring-2 ring-ink/20">Focus</button>
          <button className="px-5 py-2.5 rounded-full bg-black text-white text-sm font-semibold scale-95">Pressed</button>
          <button disabled className="px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold opacity-40 cursor-not-allowed">Disabled</button>
          <button disabled className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold opacity-80">
            <Loader2 size={14} className="animate-spin" />
            Loading
          </button>
        </Row>
      </div>
    </section>
  );
}
