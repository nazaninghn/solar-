"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Calendar, Settings, LogOut, UserRound, X } from "lucide-react";
import SectionHeader from "./SectionHeader";

const monthDays = Array.from({ length: 31 }, (_, i) => i + 1);
const leadingBlanks = 2; // July 1 2026 is a Wednesday-ish offset for illustration

export default function OverlaysSection() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState(13);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <section id="overlays" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Overlays"
        description="Dropdown menus, date pickers, and modal dialogs — all built with framer-motion for enter/exit transitions."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Dropdown */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Dropdown Menu</h4>
          <div className="relative w-fit">
            <button
              onClick={() => setDropdownOpen((o) => !o)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-full border border-gray-200 text-sm font-medium text-ink hover:bg-mist/60 transition-colors"
            >
              Account
              <ChevronDown size={14} className={`transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence>
              {dropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute left-0 mt-2 w-52 rounded-2xl border border-gray-100 bg-white shadow-xl overflow-hidden py-2 z-10"
                >
                  <a href="#" className="flex items-center gap-3 px-4 py-2.5 text-sm text-ink hover:bg-mist/40">
                    <UserRound size={15} className="text-gray-400" />
                    Profile
                  </a>
                  <a href="#" className="flex items-center gap-3 px-4 py-2.5 text-sm text-ink hover:bg-mist/40">
                    <Settings size={15} className="text-gray-400" />
                    Settings
                  </a>
                  <a href="#" className="flex items-center gap-3 px-4 py-2.5 text-sm text-danger hover:bg-mist/40">
                    <LogOut size={15} />
                    Sign Out
                  </a>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Date picker */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Date Picker</h4>
          <div className="relative w-fit">
            <button
              onClick={() => setDateOpen((o) => !o)}
              className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl border border-gray-200 text-sm text-ink hover:border-lime-dark transition-colors"
            >
              <Calendar size={15} className="text-gray-400" />
              July {selectedDay}, 2026
            </button>
            <AnimatePresence>
              {dateOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute left-0 mt-2 w-64 rounded-2xl border border-gray-100 bg-white shadow-xl p-4 z-10"
                >
                  <p className="text-xs font-semibold text-ink text-center mb-3">July 2026</p>
                  <div className="grid grid-cols-7 gap-1 text-center text-[10px] text-gray-400 mb-1">
                    {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
                      <span key={i}>{d}</span>
                    ))}
                  </div>
                  <div className="grid grid-cols-7 gap-1">
                    {Array.from({ length: leadingBlanks }).map((_, i) => (
                      <span key={`b-${i}`} />
                    ))}
                    {monthDays.map((d) => (
                      <button
                        key={d}
                        onClick={() => {
                          setSelectedDay(d);
                          setDateOpen(false);
                        }}
                        className={`w-7 h-7 rounded-full text-xs flex items-center justify-center transition-colors ${
                          d === selectedDay
                            ? "bg-ink text-white font-semibold"
                            : d === 13
                            ? "text-lime-dark font-semibold hover:bg-mist"
                            : "text-gray-600 hover:bg-mist"
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Modal trigger */}
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Modal Dialog</h4>
          <button
            onClick={() => setModalOpen(true)}
            className="px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors"
          >
            Open Modal
          </button>
        </div>
      </div>

      <AnimatePresence>
        {modalOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setModalOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 10 }}
              transition={{ duration: 0.18 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"
            >
              <div className="flex items-start justify-between">
                <div className="w-11 h-11 rounded-2xl bg-danger/10 flex items-center justify-center">
                  <X size={20} className="text-danger" />
                </div>
                <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-ink">
                  <X size={18} />
                </button>
              </div>
              <h3 className="text-lg font-semibold text-ink mt-4">Disconnect Facility B?</h3>
              <p className="text-sm text-gray-500 mt-1.5 leading-relaxed">
                This will stop data collection and pause AI recommendations for this facility until reconnected.
              </p>
              <div className="mt-6 flex items-center gap-3">
                <button
                  onClick={() => setModalOpen(false)}
                  className="flex-1 px-4 py-2.5 rounded-full border border-gray-200 text-sm font-semibold text-ink hover:bg-mist/60 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setModalOpen(false)}
                  className="flex-1 px-4 py-2.5 rounded-full bg-danger text-white text-sm font-semibold hover:bg-danger/90 transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </section>
  );
}
