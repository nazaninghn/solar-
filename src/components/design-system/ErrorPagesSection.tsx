"use client";

import { LockKeyhole, ShieldOff, MapPinOff, ServerCrash, Construction } from "lucide-react";
import SectionHeader from "./SectionHeader";

const errors = [
  { code: "401", icon: LockKeyhole, title: "Unauthorized", body: "Sign in to view this facility's dashboard.", action: "Sign In" },
  { code: "403", icon: ShieldOff, title: "Access Forbidden", body: "Your role doesn't include financial report access.", action: "Request Access" },
  { code: "404", icon: MapPinOff, title: "Page Not Found", body: "That facility or report doesn't exist.", action: "Back to Dashboard" },
  { code: "500", icon: ServerCrash, title: "Server Error", body: "Something broke on our end. We're on it.", action: "Retry" },
  { code: "503", icon: Construction, title: "Service Unavailable", body: "Scheduled maintenance — back by 04:00 CET.", action: "Check Status" },
];

export default function ErrorPagesSection() {
  return (
    <section id="error-pages" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Patterns"
        title="Error Pages"
        description="Full-page error states, framed as mini previews — consistent oversized code, icon chip, message, and single recovery action."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {errors.map((e) => (
          <div key={e.code} className="rounded-3xl border border-gray-100 overflow-hidden">
            <div className="bg-warm-bg px-6 py-10 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-2xl bg-white border border-gray-100 flex items-center justify-center mb-4">
                <e.icon size={22} className="text-ink" />
              </div>
              <p className="text-4xl font-bold text-ink tracking-tight">{e.code}</p>
              <p className="text-sm font-semibold text-ink mt-2">{e.title}</p>
              <p className="text-xs text-gray-400 mt-1.5 max-w-[220px] leading-relaxed">{e.body}</p>
              <button className="mt-5 px-5 py-2 rounded-full bg-ink text-white text-xs font-semibold hover:bg-black transition-colors">
                {e.action}
              </button>
            </div>
            <p className="px-6 py-3 text-[11px] font-mono text-gray-300 bg-white">/error/{e.code}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
