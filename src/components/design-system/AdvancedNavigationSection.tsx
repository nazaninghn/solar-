"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronRight,
  ChevronLeft,
  Search,
  Command,
  LayoutDashboard,
  Battery,
  FileText,
  Copy,
  Trash2,
  Pin,
  Download,
} from "lucide-react";
import SectionHeader from "./SectionHeader";

const commandItems = [
  { icon: LayoutDashboard, label: "Go to Dashboard" },
  { icon: Battery, label: "Go to Battery Storage" },
  { icon: FileText, label: "Open Financial Reports" },
];

export default function AdvancedNavigationSection() {
  const [page, setPage] = useState(3);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [contextOpen, setContextOpen] = useState(false);

  return (
    <section id="advanced-navigation" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Advanced Navigation"
        description="Wayfinding and power-user navigation — breadcrumbs, pagination, command palette, and context menus."
      />

      <div className="grid sm:grid-cols-2 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Breadcrumb</h4>
          <div className="flex items-center gap-1.5 text-sm">
            <span className="text-gray-400">Dashboard</span>
            <ChevronRight size={14} className="text-gray-300" />
            <span className="text-gray-400">Reports</span>
            <ChevronRight size={14} className="text-gray-300" />
            <span className="text-ink font-medium">July 2026</span>
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Pagination</h4>
          <div className="flex items-center gap-1.5">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-mist/60">
              <ChevronLeft size={15} />
            </button>
            {[1, 2, 3, 4, 5].map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`w-8 h-8 rounded-full text-xs font-semibold transition-colors ${
                  page === p ? "bg-ink text-white" : "text-gray-500 hover:bg-mist/60"
                }`}
              >
                {p}
              </button>
            ))}
            <button onClick={() => setPage((p) => Math.min(5, p + 1))} className="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-mist/60">
              <ChevronRight size={15} />
            </button>
          </div>
        </div>

        <div className="rounded-3xl bg-ink text-white p-6">
          <h4 className="text-sm font-semibold mb-4">Command Palette</h4>
          <button
            onClick={() => setPaletteOpen(true)}
            className="flex items-center gap-2.5 w-full px-4 py-2.5 rounded-xl bg-white/10 text-white/60 text-sm hover:bg-white/15 transition-colors"
          >
            <Search size={14} />
            Search or jump to…
            <span className="ml-auto flex items-center gap-0.5 text-[11px] font-mono text-white/40">
              <Command size={11} />K
            </span>
          </button>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6 relative">
          <h4 className="text-sm font-semibold text-ink mb-4">Context Menu</h4>
          <button
            onClick={() => setContextOpen((o) => !o)}
            onBlur={() => setTimeout(() => setContextOpen(false), 150)}
            className="px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-ink hover:bg-mist/60 transition-colors"
          >
            Right-click Facility A row
          </button>

          <AnimatePresence>
            {contextOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.12 }}
                className="absolute left-6 top-20 w-48 rounded-2xl border border-gray-100 bg-white shadow-xl py-2 z-10"
              >
                <button className="flex items-center gap-3 w-full px-4 py-2 text-sm text-ink hover:bg-mist/40">
                  <Pin size={14} className="text-gray-400" /> Pin row
                </button>
                <button className="flex items-center gap-3 w-full px-4 py-2 text-sm text-ink hover:bg-mist/40">
                  <Copy size={14} className="text-gray-400" /> Duplicate
                </button>
                <button className="flex items-center gap-3 w-full px-4 py-2 text-sm text-ink hover:bg-mist/40">
                  <Download size={14} className="text-gray-400" /> Export
                </button>
                <button className="flex items-center gap-3 w-full px-4 py-2 text-sm text-danger hover:bg-mist/40">
                  <Trash2 size={14} /> Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {paletteOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setPaletteOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.97, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: -10 }}
              transition={{ duration: 0.15 }}
              className="fixed left-1/2 top-32 -translate-x-1/2 z-50 w-full max-w-lg rounded-2xl bg-white shadow-2xl overflow-hidden"
            >
              <div className="flex items-center gap-2.5 px-4 py-3.5 border-b border-gray-100">
                <Search size={15} className="text-gray-400" />
                <input autoFocus placeholder="Type a command…" className="flex-1 text-sm outline-none" />
              </div>
              <div className="py-2">
                {commandItems.map((c) => (
                  <button key={c.label} className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-ink hover:bg-mist/40">
                    <c.icon size={15} className="text-gray-400" />
                    {c.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </section>
  );
}
