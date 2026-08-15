"use client";

import { motion } from "framer-motion";
import { FileText, Download, Calendar, TrendingUp, Zap, PiggyBank } from "lucide-react";

const reports = [
  { id: 1, name: "Monthly Energy Report — July 2026", type: "Energy", date: "Aug 1, 2026", size: "2.4 MB", status: "Ready" },
  { id: 2, name: "Financial Summary — July 2026", type: "Financial", date: "Aug 1, 2026", size: "1.8 MB", status: "Ready" },
  { id: 3, name: "Weekly Performance — W31", type: "Performance", date: "Aug 5, 2026", size: "1.2 MB", status: "Ready" },
  { id: 4, name: "Battery Health Report — Q2 2026", type: "Battery", date: "Jul 1, 2026", size: "890 KB", status: "Ready" },
  { id: 5, name: "Solar Forecast Accuracy — July 2026", type: "Forecast", date: "Aug 1, 2026", size: "650 KB", status: "Ready" },
  { id: 6, name: "Monthly Energy Report — August 2026", type: "Energy", date: "Generating...", size: "—", status: "Processing" },
];

const quickStats = [
  { icon: Zap, label: "Reports Generated", value: "24", sub: "This year" },
  { icon: TrendingUp, label: "Data Coverage", value: "98.7%", sub: "Average" },
  { icon: PiggyBank, label: "Total Documented Savings", value: "€52,400", sub: "Year to date" },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Reports</h1>
          <p className="text-sm text-gray-500 mt-1">Energy, financial, and performance reports</p>
        </div>
        <button className="px-4 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors flex items-center gap-2">
          <FileText size={16} />
          Generate Report
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid sm:grid-cols-3 gap-4">
        {quickStats.map((stat) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-4 border border-gray-100">
            <stat.icon size={18} className="text-royal" />
            <p className="text-xs text-gray-400 mt-2">{stat.label}</p>
            <p className="text-xl font-bold text-ink mt-0.5">{stat.value}</p>
            <p className="text-[10px] text-gray-400">{stat.sub}</p>
          </motion.div>
        ))}
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-ink">Recent Reports</h3>
          <div className="flex items-center gap-2">
            <select className="text-xs border border-gray-200 rounded-lg px-3 py-1.5">
              <option>All Types</option>
              <option>Energy</option>
              <option>Financial</option>
              <option>Performance</option>
              <option>Battery</option>
            </select>
          </div>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-50 text-left">
              <th className="px-5 py-3 text-xs text-gray-400 font-medium">Report</th>
              <th className="px-5 py-3 text-xs text-gray-400 font-medium">Type</th>
              <th className="px-5 py-3 text-xs text-gray-400 font-medium">Date</th>
              <th className="px-5 py-3 text-xs text-gray-400 font-medium">Size</th>
              <th className="px-5 py-3 text-xs text-gray-400 font-medium">Status</th>
              <th className="px-5 py-3 text-xs text-gray-400 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report, i) => (
              <motion.tr
                key={report.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="border-b border-gray-50 hover:bg-gray-50/50"
              >
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-royal/10 flex items-center justify-center shrink-0">
                      <FileText size={14} className="text-royal" />
                    </div>
                    <span className="font-medium text-ink text-sm">{report.name}</span>
                  </div>
                </td>
                <td className="px-5 py-3 text-gray-500">{report.type}</td>
                <td className="px-5 py-3 text-gray-500 flex items-center gap-1"><Calendar size={12} /> {report.date}</td>
                <td className="px-5 py-3 text-gray-500">{report.size}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                    report.status === "Ready" ? "bg-primary-green/10 text-primary-green" : "bg-energy-orange/10 text-energy-orange"
                  }`}>{report.status}</span>
                </td>
                <td className="px-5 py-3">
                  {report.status === "Ready" && (
                    <button className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
                      <Download size={16} className="text-gray-400" />
                    </button>
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
