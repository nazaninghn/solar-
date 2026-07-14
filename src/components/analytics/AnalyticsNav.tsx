"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const sections = [
  { id: "charts", label: "Chart Gallery" },
  { id: "energy-flow", label: "Energy Flow" },
  { id: "kpis", label: "KPI Cards" },
  { id: "ai", label: "AI Components" },
  { id: "weather", label: "Weather" },
  { id: "battery", label: "Battery" },
  { id: "grid", label: "Grid & Pricing" },
  { id: "factory", label: "Factory & Maps" },
  { id: "financial", label: "Financial" },
  { id: "status", label: "Status & States" },
];

export default function AnalyticsNav() {
  const [active, setActive] = useState("charts");

  return (
    <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen overflow-y-auto border-r border-gray-100 bg-white">
      <div className="px-6 py-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-green to-secondary-green flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
            </svg>
          </div>
          <div>
            <span className="text-base font-bold text-ink">
              Solar<span className="text-lime-dark">Flow</span>
            </span>
            <p className="text-[10px] text-gray-400 -mt-0.5">Analytics System</p>
          </div>
        </Link>
      </div>

      <nav className="px-4 pb-10">
        {sections.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            onClick={() => setActive(s.id)}
            className={`block px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
              active === s.id ? "bg-ink text-white" : "text-gray-500 hover:text-ink hover:bg-mist/60"
            }`}
          >
            {s.label}
          </a>
        ))}

        <Link
          href="/design-system"
          className="mt-4 flex items-center gap-2 px-3 py-2 text-xs font-semibold text-gray-400 hover:text-ink transition-colors"
        >
          UI Design System →
        </Link>
        <Link
          href="/"
          className="mt-1 flex items-center gap-2 px-3 py-2 text-xs font-semibold text-gray-400 hover:text-ink transition-colors"
        >
          <ArrowLeft size={13} />
          Back to Website
        </Link>
      </nav>
    </aside>
  );
}
