"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Bell,
  ChevronDown,
  Menu,
  Settings,
  LogOut,
  UserRound,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

const notifications = [
  {
    icon: TrendingUp,
    color: "text-lime-dark bg-lime/15",
    title: "Solar surplus detected",
    detail: "Production is 38% above consumption — good time to charge batteries.",
    time: "2m ago",
  },
  {
    icon: AlertTriangle,
    color: "text-energy-orange bg-energy-orange/15",
    title: "Price spike expected at 18:00",
    detail: "Grid price forecast to rise to €0.31/kWh during evening peak.",
    time: "1h ago",
  },
  {
    icon: CheckCircle2,
    color: "text-primary-green bg-primary-green/15",
    title: "Monthly report ready",
    detail: "Your June savings report has been generated.",
    time: "5h ago",
  },
];

export default function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-100">
      <div className="flex items-center justify-between gap-4 px-5 lg:px-8 py-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 -ml-2 text-ink"
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>

          <div className="relative w-full max-w-sm hidden sm:block">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search facilities, reports, alerts…"
              className="w-full pl-11 pr-4 py-2.5 rounded-full border border-gray-200 bg-mist/40 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/30 focus:border-lime-dark transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => {
                setNotifOpen((o) => !o);
                setProfileOpen(false);
              }}
              className="relative p-2.5 rounded-full hover:bg-mist/60 transition-colors"
              aria-label="Notifications"
            >
              <Bell size={18} className="text-ink" />
              <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-danger" />
            </button>

            <AnimatePresence>
              {notifOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-80 rounded-2xl border border-gray-100 bg-white shadow-xl overflow-hidden"
                >
                  <div className="px-5 py-4 border-b border-gray-100">
                    <p className="text-sm font-semibold text-ink">Notifications</p>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {notifications.map((n, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 px-5 py-3.5 border-b border-gray-50 last:border-0 hover:bg-mist/30 transition-colors"
                      >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${n.color}`}>
                          <n.icon size={15} />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-ink">{n.title}</p>
                          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{n.detail}</p>
                          <p className="text-[11px] text-gray-400 mt-1">{n.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Profile */}
          <div className="relative">
            <button
              onClick={() => {
                setProfileOpen((o) => !o);
                setNotifOpen(false);
              }}
              className="flex items-center gap-2 pl-1.5 pr-2.5 py-1.5 rounded-full hover:bg-mist/60 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-ink flex items-center justify-center text-xs font-bold text-lime">
                JD
              </div>
              <span className="hidden sm:block text-sm font-medium text-ink">Jane Doe</span>
              <ChevronDown size={14} className="text-gray-400 hidden sm:block" />
            </button>

            <AnimatePresence>
              {profileOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-56 rounded-2xl border border-gray-100 bg-white shadow-xl overflow-hidden py-2"
                >
                  <div className="px-4 py-2.5 border-b border-gray-100 mb-1">
                    <p className="text-sm font-semibold text-ink">Jane Doe</p>
                    <p className="text-xs text-gray-400">jane@acme-industrial.com</p>
                  </div>
                  <a href="#" className="flex items-center gap-3 px-4 py-2.5 text-sm text-ink hover:bg-mist/40 transition-colors">
                    <UserRound size={16} className="text-gray-400" />
                    My Profile
                  </a>
                  <a href="#" className="flex items-center gap-3 px-4 py-2.5 text-sm text-ink hover:bg-mist/40 transition-colors">
                    <Settings size={16} className="text-gray-400" />
                    Account Settings
                  </a>
                  <a href="/login" className="flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-mist/40 transition-colors">
                    <LogOut size={16} />
                    Sign Out
                  </a>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  );
}
