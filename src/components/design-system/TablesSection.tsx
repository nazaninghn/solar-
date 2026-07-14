"use client";

import SectionHeader from "./SectionHeader";

const rows = [
  { month: "May 2026", solar: "5,180 kWh", savings: "€1,980", roi: "7.1%", status: "Sell" },
  { month: "Jun 2026", solar: "5,610 kWh", savings: "€2,140", roi: "7.6%", status: "Sell" },
  { month: "Jul 2026", solar: "5,820 kWh", savings: "€2,280", roi: "7.9%", status: "Charge" },
];

const badgeStyles: Record<string, string> = {
  Sell: "bg-lime/20 text-lime-dark",
  Charge: "bg-royal/15 text-royal",
};

export default function TablesSection() {
  return (
    <section id="tables" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Tables"
        description="Data tables use a mist header row, hairline row dividers, and right-aligned numeric columns."
      />

      <div className="rounded-3xl bg-white border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="border-b border-gray-100 bg-mist/40">
                <th className="text-left font-semibold text-gray-500 px-6 py-3 text-xs uppercase tracking-wide">Month</th>
                <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Solar</th>
                <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">Savings</th>
                <th className="text-right font-semibold text-gray-500 px-3 py-3 text-xs uppercase tracking-wide">ROI</th>
                <th className="text-right font-semibold text-gray-500 px-6 py-3 text-xs uppercase tracking-wide">Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.month} className={`hover:bg-mist/30 transition-colors ${i !== rows.length - 1 ? "border-b border-gray-50" : ""}`}>
                  <td className="px-6 py-3.5 font-semibold text-ink">{r.month}</td>
                  <td className="px-3 py-3.5 text-right text-gray-600">{r.solar}</td>
                  <td className="px-3 py-3.5 text-right font-semibold text-primary-green">{r.savings}</td>
                  <td className="px-3 py-3.5 text-right font-medium text-lime-dark">{r.roi}</td>
                  <td className="px-6 py-3.5 text-right">
                    <span className={`inline-block text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded-full ${badgeStyles[r.status]}`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
