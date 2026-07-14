"use client";

import {
  Inbox,
  WifiOff,
  SearchX,
  ShieldAlert,
  ServerCrash,
  Rocket,
  Wrench,
  RefreshCw,
} from "lucide-react";
import SectionHeader from "./SectionHeader";

const states = [
  { icon: Inbox, tone: "bg-mist text-gray-400", title: "No data yet", body: "Data will appear here once collection begins." },
  { icon: WifiOff, tone: "bg-steel/15 text-steel", title: "No internet connection", body: "Check your network and we'll reconnect automatically.", action: "Retry" },
  { icon: SearchX, tone: "bg-mist text-gray-400", title: "No search results", body: "Try a different facility name or clear filters." },
  { icon: ShieldAlert, tone: "bg-energy-orange/10 text-energy-orange", title: "Permission denied", body: "You don't have access to this facility's financial data." },
  { icon: ServerCrash, tone: "bg-danger/10 text-danger", title: "Server error", body: "Something went wrong on our end. We've been notified.", action: "Retry" },
  { icon: Rocket, tone: "bg-lime/15 text-lime-dark", title: "Coming soon", body: "Multi-facility comparison is launching next quarter." },
  { icon: Wrench, tone: "bg-royal/10 text-royal", title: "Under maintenance", body: "Scheduled maintenance until 04:00 CET. Data may be delayed." },
];

export default function EmptyStatesSection() {
  return (
    <section id="empty-states" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Patterns"
        title="Empty States"
        description="Every reason a surface can have nothing to show — each with a consistent icon-chip, message, and optional recovery action."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {states.map((s) => (
          <div key={s.title} className="rounded-3xl bg-white border border-gray-100 p-6 flex flex-col items-center text-center">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 ${s.tone}`}>
              <s.icon size={22} />
            </div>
            <p className="text-sm font-semibold text-ink">{s.title}</p>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">{s.body}</p>
            {s.action && (
              <button className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-ink hover:bg-mist/60 transition-colors">
                <RefreshCw size={12} />
                {s.action}
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
