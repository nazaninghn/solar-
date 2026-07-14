"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  BarChart3,
  CloudSun,
  Sparkles,
  Battery,
  Receipt,
  FileText,
  Settings,
  ArrowLeft,
  X,
} from "lucide-react";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { label: "Forecast", href: "/dashboard/forecast", icon: CloudSun },
  { label: "AI Recommendations", href: "/dashboard/recommendations", icon: Sparkles },
  { label: "Battery Storage", href: "/dashboard/battery", icon: Battery },
  { label: "Billing & Savings", href: "/dashboard/billing", icon: Receipt },
  { label: "Reports", href: "/dashboard/reports", icon: FileText },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

function SidebarContent({ pathname }: { pathname: string }) {
  return (
    <div className="flex flex-col h-full bg-ink text-white">
      <Link href="/" className="flex items-center gap-2.5 px-6 py-6">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-green to-secondary-green flex items-center justify-center shrink-0">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
          </svg>
        </div>
        <span className="text-lg font-bold">
          Solar<span className="text-lime">Flow</span>
        </span>
      </Link>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {navItems.map((item) => {
          const active = item.href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                active
                  ? "bg-white/10 text-white"
                  : "text-white/50 hover:text-white hover:bg-white/5"
              }`}
            >
              <item.icon size={18} className={active ? "text-lime" : ""} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-4 pt-2 border-t border-white/10">
        <Link
          href="/"
          className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Website
        </Link>
        <div className="mt-2 flex items-center gap-3 px-3.5 py-3 rounded-xl bg-white/5">
          <div className="w-9 h-9 rounded-full bg-lime/20 flex items-center justify-center text-sm font-bold text-lime shrink-0">
            JD
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">Jane Doe</p>
            <p className="text-xs text-white/40 truncate">Acme Industrial GmbH</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-[260px] shrink-0 sticky top-0 h-screen">
        <SidebarContent pathname={pathname} />
      </aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed inset-y-0 left-0 w-[260px] z-50 lg:hidden"
            >
              <div className="relative h-full">
                <button
                  onClick={onClose}
                  className="absolute top-6 right-4 text-white/60 hover:text-white"
                  aria-label="Close menu"
                >
                  <X size={20} />
                </button>
                <SidebarContent pathname={pathname} />
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
