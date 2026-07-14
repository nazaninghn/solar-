"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, ChevronDown, Clock, RotateCcw } from "lucide-react";
import ConfidenceRing from "./ConfidenceRing";
import type { Recommendation, RecStatus } from "./data";

const categoryStyles: Record<string, string> = {
  Battery: "bg-lime/15 text-lime-dark",
  Grid: "bg-royal/15 text-royal",
  Load: "bg-azure/15 text-azure",
  Maintenance: "bg-energy-orange/15 text-energy-orange",
  Billing: "bg-steel/20 text-steel",
};

export default function AIRecommendationCard({
  item,
  status,
  onApprove,
  onReject,
  onReset,
  delay = 0,
}: {
  item: Recommendation;
  status: RecStatus;
  onApprove: () => void;
  onReject: () => void;
  onReset: () => void;
  delay?: number;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className={`rounded-3xl border p-6 transition-colors ${
        status === "approved"
          ? "bg-lime/5 border-lime-dark/30"
          : status === "rejected"
          ? "bg-mist/40 border-gray-200 opacity-70"
          : "bg-white border-gray-100"
      }`}
    >
      <div className="flex items-start gap-4">
        <div className="w-11 h-11 rounded-2xl bg-ink flex items-center justify-center shrink-0">
          <item.icon size={20} className="text-lime" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full ${categoryStyles[item.category]}`}>
              {item.category}
            </span>
            {status !== "pending" && (
              <span
                className={`text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full ${
                  status === "approved" ? "bg-primary-green/15 text-primary-green" : "bg-danger/10 text-danger"
                }`}
              >
                {status}
              </span>
            )}
          </div>
          <h3 className="text-base font-semibold text-ink mt-2">{item.title}</h3>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">{item.summary}</p>

          <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-gray-400">
            <span className="flex items-center gap-1.5">
              <Clock size={12} />
              {item.timeline}
            </span>
            {item.savings !== null && (
              <span className="font-semibold text-primary-green">
                Potential savings: €{item.savings.toFixed(item.savings % 1 === 0 ? 0 : 1)}
              </span>
            )}
          </div>
        </div>

        <ConfidenceRing value={item.confidence} />
      </div>

      <div className="flex items-center justify-between gap-3 mt-5 pt-5 border-t border-gray-100">
        <button
          onClick={() => setExpanded((e) => !e)}
          className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-ink transition-colors"
        >
          Recommendation details
          <ChevronDown size={14} className={`transition-transform ${expanded ? "rotate-180" : ""}`} />
        </button>

        {status === "pending" ? (
          <div className="flex items-center gap-2">
            <button
              onClick={onReject}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-gray-600 hover:bg-mist/60 transition-colors"
            >
              <X size={14} />
              Reject
            </button>
            <button
              onClick={onApprove}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-ink text-white text-xs font-semibold hover:bg-black transition-colors"
            >
              <Check size={14} className="text-lime" />
              Approve
            </button>
          </div>
        ) : (
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-gray-500 hover:bg-mist/60 transition-colors"
          >
            <RotateCcw size={13} />
            Undo
          </button>
        )}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <ul className="mt-4 pt-4 border-t border-gray-100 space-y-2">
              {item.details.map((d, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-gray-600 leading-relaxed">
                  <span className="w-1.5 h-1.5 rounded-full bg-lime-dark mt-1.5 shrink-0" />
                  {d}
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
