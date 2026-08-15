"use client";

import { motion } from "framer-motion";
import { BatteryCharging, ShoppingCart, ArrowRightLeft } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const toneStyles: Record<string, { badge: string; iconBg: string; iconColor: string }> = {
  positive: {
    badge: "bg-lime/20 text-lime-dark",
    iconBg: "bg-lime/15",
    iconColor: "text-lime-dark",
  },
  neutral: {
    badge: "bg-mist text-gray-500",
    iconBg: "bg-mist",
    iconColor: "text-gray-500",
  },
};

export default function RecommendationCard() {
  const { t } = useLanguage();

  const items = [
    {
      icon: BatteryCharging,
      question: t.dashboard.chargeBattery,
      answer: t.dashboard.yes,
      tone: "positive",
      reason: t.dashboard.chargeReason,
    },
    {
      icon: ShoppingCart,
      question: t.dashboard.buyElectricity,
      answer: t.dashboard.no,
      tone: "neutral",
      reason: t.dashboard.buyReason,
    },
    {
      icon: ArrowRightLeft,
      question: t.dashboard.sellElectricity,
      answer: t.dashboard.yes,
      tone: "positive",
      reason: t.dashboard.sellReason,
    },
  ];

  return (
    <div id="recommendations">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-ink tracking-tight">
          {t.dashboard.whatToDo}
        </h2>
        <p className="text-xs text-gray-400">{t.dashboard.updatedAgo}</p>
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        {items.map((item, i) => {
          const tone = toneStyles[item.tone];
          return (
            <motion.div
              key={item.question}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
              className="rounded-3xl bg-white border border-gray-100 p-6"
            >
              <div className="flex items-start justify-between">
                <div className={`w-11 h-11 rounded-2xl flex items-center justify-center ${tone.iconBg}`}>
                  <item.icon size={20} className={tone.iconColor} />
                </div>
                <span className={`text-xs font-bold uppercase tracking-wide px-3 py-1.5 rounded-full ${tone.badge}`}>
                  {item.answer}
                </span>
              </div>
              <p className="mt-4 text-sm font-semibold text-ink">{item.question}</p>
              <p className="mt-1.5 text-sm text-gray-500 leading-relaxed">{item.reason}</p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
