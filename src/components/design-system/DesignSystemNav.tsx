"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const sections = [
  { id: "foundations", label: "Foundations" },
  { id: "buttons", label: "Buttons" },
  { id: "inputs", label: "Inputs" },
  { id: "advanced-inputs", label: "Advanced Inputs" },
  { id: "cards", label: "Cards" },
  { id: "tables", label: "Tables" },
  { id: "data-display", label: "Data Display" },
  { id: "charts", label: "Charts" },
  { id: "navigation", label: "Navigation" },
  { id: "advanced-navigation", label: "Advanced Navigation" },
  { id: "feedback", label: "Feedback" },
  { id: "overlays", label: "Overlays" },
  { id: "notifications", label: "Notifications" },
  { id: "empty-states", label: "Empty States" },
  { id: "error-pages", label: "Error Pages" },
  { id: "icons", label: "Icons" },
  { id: "accessibility", label: "Accessibility & Motion" },
  { id: "theming", label: "Theming & Guidelines" },
];

export default function DesignSystemNav() {
  const [active, setActive] = useState("foundations");

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
            <p className="text-[10px] text-gray-400 -mt-0.5">Design System</p>
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
          href="/"
          className="mt-6 flex items-center gap-2 px-3 py-2 text-xs font-semibold text-gray-400 hover:text-ink transition-colors"
        >
          <ArrowLeft size={13} />
          Back to Website
        </Link>
      </nav>
    </aside>
  );
}
