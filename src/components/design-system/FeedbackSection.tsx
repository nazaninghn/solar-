"use client";

import { CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";
import SectionHeader from "./SectionHeader";

const alerts = [
  { icon: CheckCircle2, tone: "success", title: "Report generated", body: "Your June financial report is ready to download." },
  { icon: Info, tone: "info", title: "Scheduled maintenance", body: "Inverter inspection recommended within 2 weeks." },
  { icon: AlertTriangle, tone: "warning", title: "Price spike expected", body: "Grid price forecast to reach €0.31/kWh at 18:00." },
  { icon: XCircle, tone: "danger", title: "Connection lost", body: "Facility B meter has not reported in 34 minutes." },
];

const alertStyles: Record<string, string> = {
  success: "bg-primary-green/10 border-primary-green/20 text-primary-green",
  info: "bg-royal/10 border-royal/20 text-royal",
  warning: "bg-energy-orange/10 border-energy-orange/20 text-energy-orange",
  danger: "bg-danger/10 border-danger/20 text-danger",
};

const badges = [
  { label: "Sell", className: "bg-lime/20 text-lime-dark" },
  { label: "Charge", className: "bg-royal/15 text-royal" },
  { label: "Buy", className: "bg-danger/10 text-danger" },
  { label: "Hold", className: "bg-mist text-gray-500" },
  { label: "Approved", className: "bg-primary-green/15 text-primary-green" },
  { label: "Rejected", className: "bg-danger/10 text-danger" },
];

const chips = [
  { label: "Online", dot: "bg-primary-green" },
  { label: "Charging", dot: "bg-lime-dark" },
  { label: "Offline", dot: "bg-gray-300" },
  { label: "Warning", dot: "bg-energy-orange" },
];

const progressBars = [
  { label: "Battery SOC", value: 68, color: "bg-lime-dark" },
  { label: "Cycles Used", value: 14, color: "bg-royal" },
  { label: "Storage Quota", value: 92, color: "bg-danger" },
];

export default function FeedbackSection() {
  return (
    <section id="feedback" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Feedback"
        description="Alerts, badges, status chips, and progress indicators for communicating system state."
      />

      <div className="space-y-10">
        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Alerts</h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {alerts.map((a) => (
              <div key={a.title} className={`flex items-start gap-3 rounded-2xl border px-4 py-3.5 ${alertStyles[a.tone]}`}>
                <a.icon size={18} className="shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-ink">{a.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{a.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-ink mb-4">Badges</h3>
            <div className="flex flex-wrap gap-2">
              {badges.map((b) => (
                <span key={b.label} className={`text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded-full ${b.className}`}>
                  {b.label}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-ink mb-4">Status Chips</h3>
            <div className="flex flex-wrap gap-3">
              {chips.map((c) => (
                <span key={c.label} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-mist/60 text-xs font-medium text-ink">
                  <span className={`w-2 h-2 rounded-full ${c.dot}`} />
                  {c.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-ink mb-4">Progress Bars</h3>
          <div className="rounded-3xl bg-white border border-gray-100 p-6 space-y-5 max-w-md">
            {progressBars.map((p) => (
              <div key={p.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-ink">{p.label}</span>
                  <span className="text-xs text-gray-400">{p.value}%</span>
                </div>
                <div className="h-2 rounded-full bg-mist overflow-hidden">
                  <div className={`h-full rounded-full ${p.color}`} style={{ width: `${p.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
