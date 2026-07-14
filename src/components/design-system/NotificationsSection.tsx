"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, X, PanelRightOpen, AlertTriangle } from "lucide-react";
import SectionHeader from "./SectionHeader";

export default function NotificationsSection() {
  const [toastOpen, setToastOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  function fireToast() {
    setToastOpen(true);
    setTimeout(() => setToastOpen(false), 3000);
  }

  return (
    <section id="notifications" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Notifications & Overlays"
        description="Toast, drawer, and confirmation dialog — transient and blocking feedback patterns."
      />

      <div className="grid sm:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Toast / Snackbar</h4>
          <button onClick={fireToast} className="px-4 py-2.5 rounded-full bg-ink text-white text-xs font-semibold hover:bg-black transition-colors">
            Trigger Toast
          </button>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Drawer</h4>
          <button
            onClick={() => setDrawerOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-full border border-gray-200 text-xs font-semibold text-ink hover:bg-mist/60 transition-colors"
          >
            <PanelRightOpen size={13} />
            Open Drawer
          </button>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <h4 className="text-sm font-semibold text-ink mb-4">Confirmation Dialog</h4>
          <button
            onClick={() => setConfirmOpen(true)}
            className="px-4 py-2.5 rounded-full bg-danger/10 text-danger text-xs font-semibold hover:bg-danger/20 transition-colors"
          >
            Delete Report
          </button>
        </div>
      </div>

      {/* Toast */}
      <AnimatePresence>
        {toastOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, x: "-50%" }}
            animate={{ opacity: 1, y: 0, x: "-50%" }}
            exit={{ opacity: 0, y: 20, x: "-50%" }}
            className="fixed bottom-8 left-1/2 z-[60] flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-ink text-white shadow-2xl"
          >
            <CheckCircle2 size={16} className="text-lime shrink-0" />
            <p className="text-sm">Report exported successfully.</p>
            <button onClick={() => setToastOpen(false)} className="text-white/40 hover:text-white">
              <X size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setDrawerOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed inset-y-0 right-0 w-full max-w-sm bg-white z-50 shadow-2xl p-6"
            >
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-semibold text-ink">Facility Settings</h3>
                <button onClick={() => setDrawerOpen(false)} className="text-gray-400 hover:text-ink">
                  <X size={18} />
                </button>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed">
                Drawers slide in from the edge for focused, non-blocking tasks — editing a facility, viewing a
                detail record, or configuring a widget without leaving the current page context.
              </p>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Confirmation dialog */}
      <AnimatePresence>
        {confirmOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setConfirmOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl text-center"
            >
              <div className="w-12 h-12 rounded-2xl bg-danger/10 flex items-center justify-center mx-auto">
                <AlertTriangle size={22} className="text-danger" />
              </div>
              <h3 className="text-base font-semibold text-ink mt-4">Delete this report?</h3>
              <p className="text-sm text-gray-500 mt-1.5">This action cannot be undone.</p>
              <div className="mt-5 flex items-center gap-3">
                <button onClick={() => setConfirmOpen(false)} className="flex-1 px-4 py-2.5 rounded-full border border-gray-200 text-sm font-semibold text-ink hover:bg-mist/60">
                  Cancel
                </button>
                <button onClick={() => setConfirmOpen(false)} className="flex-1 px-4 py-2.5 rounded-full bg-danger text-white text-sm font-semibold hover:bg-danger/90">
                  Delete
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </section>
  );
}
