"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Search, ArrowUpDown, Download, Info } from "lucide-react";
import SectionHeader from "./SectionHeader";

const accordionItems = [
  { q: "How is Battery Health calculated?", a: "Health score blends capacity retention, internal resistance drift, and thermal history over the last 90 days." },
  { q: "What counts as a charge cycle?", a: "One full 0–100% equivalent discharge, which may be composed of several partial cycles." },
];

const tableRows = [
  { facility: "Munich HQ", production: 5820, savings: 2280, status: "Healthy" },
  { facility: "Lyon Plant", production: 4120, savings: 1640, status: "Warning" },
  { facility: "Turin Depot", production: 3010, savings: 980, status: "Healthy" },
  { facility: "Rotterdam Hub", production: 2210, savings: 640, status: "Critical" },
];

const statusColor: Record<string, string> = {
  Healthy: "bg-primary-green/10 text-primary-green",
  Warning: "bg-energy-orange/10 text-energy-orange",
  Critical: "bg-danger/10 text-danger",
};

export default function DataDisplaySection() {
  const [openAccordion, setOpenAccordion] = useState<number | null>(0);
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [sortKey, setSortKey] = useState<"production" | "savings">("production");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [search, setSearch] = useState("");

  const rows = useMemo(() => {
    return tableRows
      .filter((r) => r.facility.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => (a[sortKey] - b[sortKey]) * sortDir);
  }, [search, sortKey, sortDir]);

  function toggleSort(key: "production" | "savings") {
    if (sortKey === key) setSortDir((d) => (d === 1 ? -1 : 1));
    else {
      setSortKey(key);
      setSortDir(-1);
    }
  }

  return (
    <section id="data-display" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Data Display"
        description="Accordion, tooltip, popover, avatar, timeline, and battery indicator, plus a fully sortable, filterable, searchable data table."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5 mb-5">
        {/* Accordion */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-3">Accordion</h4>
          <div className="divide-y divide-gray-50">
            {accordionItems.map((item, i) => (
              <div key={item.q}>
                <button
                  onClick={() => setOpenAccordion(openAccordion === i ? null : i)}
                  className="w-full flex items-center justify-between py-3 text-left"
                >
                  <span className="text-xs font-medium text-ink pr-3">{item.q}</span>
                  <ChevronDown size={14} className={`shrink-0 text-gray-400 transition-transform ${openAccordion === i ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence>
                  {openAccordion === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <p className="text-xs text-gray-500 pb-3 leading-relaxed">{item.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Tooltip + Popover */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex flex-col gap-6">
          <div>
            <h4 className="text-sm font-semibold text-ink mb-3">Tooltip</h4>
            <div className="relative w-fit">
              <button
                onMouseEnter={() => setTooltipOpen(true)}
                onMouseLeave={() => setTooltipOpen(false)}
                className="flex items-center gap-1.5 text-xs text-gray-500"
              >
                <Info size={13} />
                Hover for detail
              </button>
              {tooltipOpen && (
                <div className="absolute left-0 bottom-full mb-2 px-3 py-1.5 rounded-lg bg-ink text-white text-[11px] whitespace-nowrap">
                  95% forecast accuracy, 14-day rolling
                </div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-ink mb-3">Popover</h4>
            <div className="relative w-fit">
              <button
                onClick={() => setPopoverOpen((o) => !o)}
                className="px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-ink hover:bg-mist/60"
              >
                View breakdown
              </button>
              <AnimatePresence>
                {popoverOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="absolute left-0 mt-2 w-52 rounded-2xl border border-gray-100 bg-white shadow-xl p-4 z-10"
                  >
                    <p className="text-xs font-semibold text-ink mb-2">Savings Breakdown</p>
                    <div className="space-y-1.5 text-[11px] text-gray-500">
                      <div className="flex justify-between"><span>Self-consumption</span><span className="font-semibold text-ink">€1,420</span></div>
                      <div className="flex justify-between"><span>Grid export</span><span className="font-semibold text-ink">€620</span></div>
                      <div className="flex justify-between"><span>Battery arbitrage</span><span className="font-semibold text-ink">€240</span></div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Avatar + Timeline + Battery indicator */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6 flex flex-col gap-6">
          <div>
            <h4 className="text-sm font-semibold text-ink mb-3">Avatar Group</h4>
            <div className="flex -space-x-2.5">
              {["JD", "MK", "AL"].map((initials, i) => (
                <div
                  key={initials}
                  className="w-9 h-9 rounded-full bg-ink border-2 border-white flex items-center justify-center text-[10px] font-bold text-lime"
                  style={{ zIndex: 3 - i }}
                >
                  {initials}
                </div>
              ))}
              <div className="w-9 h-9 rounded-full bg-mist border-2 border-white flex items-center justify-center text-[10px] font-bold text-gray-500">+4</div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-ink mb-3">Battery Indicator</h4>
            <div className="flex items-center gap-2">
              <div className="relative w-10 h-5 rounded-md border-2 border-ink flex items-center px-0.5">
                <div className="h-full bg-lime-dark rounded-sm" style={{ width: "68%" }} />
                <div className="absolute -right-1.5 top-1/2 -translate-y-1/2 w-1 h-2 bg-ink rounded-r" />
              </div>
              <span className="text-xs font-semibold text-ink">68%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline full width */}
      <div className="rounded-3xl bg-white border border-gray-100 p-6 mb-5">
        <h4 className="text-sm font-semibold text-ink mb-4">Timeline</h4>
        <div className="relative pl-6">
          <div className="absolute left-[7px] top-1 bottom-1 w-px bg-gray-100" />
          {[
            { t: "14:02", label: "AI recommendation approved — charge battery" },
            { t: "13:40", label: "Grid price forecast updated" },
            { t: "12:15", label: "Solar production peaked at 847 kW" },
          ].map((e) => (
            <div key={e.t} className="relative pb-5 last:pb-0">
              <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full bg-lime border-2 border-white ring-1 ring-lime-dark/30" />
              <p className="text-xs text-gray-400">{e.t}</p>
              <p className="text-sm text-ink mt-0.5">{e.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Advanced Data Table */}
      <div className="rounded-3xl bg-white border border-gray-100 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-gray-100">
          <h4 className="text-sm font-semibold text-ink">Advanced Data Table</h4>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search facility…"
                className="pl-8 pr-3 py-1.5 rounded-full border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-lime-dark/30"
              />
            </div>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs font-semibold text-ink hover:bg-mist/60">
              <Download size={12} />
              Export CSV
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[500px]">
            <thead>
              <tr className="border-b border-gray-100 bg-mist/40">
                <th className="text-left font-semibold text-gray-500 px-6 py-3 text-xs uppercase tracking-wide sticky left-0 bg-mist/40">Facility</th>
                <th className="px-3 py-3 text-right">
                  <button onClick={() => toggleSort("production")} className="flex items-center gap-1 ml-auto text-xs font-semibold text-gray-500 uppercase tracking-wide hover:text-ink">
                    Production
                    <ArrowUpDown size={11} />
                  </button>
                </th>
                <th className="px-3 py-3 text-right">
                  <button onClick={() => toggleSort("savings")} className="flex items-center gap-1 ml-auto text-xs font-semibold text-gray-500 uppercase tracking-wide hover:text-ink">
                    Savings
                    <ArrowUpDown size={11} />
                  </button>
                </th>
                <th className="text-right font-semibold text-gray-500 px-6 py-3 text-xs uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.facility} className={`hover:bg-mist/30 transition-colors ${i !== rows.length - 1 ? "border-b border-gray-50" : ""}`}>
                  <td className="px-6 py-3.5 font-semibold text-ink sticky left-0 bg-white">{r.facility}</td>
                  <td className="px-3 py-3.5 text-right text-gray-600">{r.production.toLocaleString()} kWh</td>
                  <td className="px-3 py-3.5 text-right font-semibold text-primary-green">€{r.savings.toLocaleString()}</td>
                  <td className="px-6 py-3.5 text-right">
                    <span className={`inline-block text-xs font-bold px-3 py-1.5 rounded-full ${statusColor[r.status]}`}>{r.status}</span>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-sm text-gray-400">No facilities match &quot;{search}&quot;</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
