"use client";

import { motion } from "framer-motion";
import {
  TrendingDown,
  CloudOff,
  Battery,
  Zap,
  EyeOff,
} from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const icons = [TrendingDown, CloudOff, Battery, Zap, EyeOff];

export default function Problem() {
  const { t } = useLanguage();
  const problems = t.problem.items.map((item, i) => ({ ...item, icon: icons[i] }));

  return (
    <section className="py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <p className="text-xs font-semibold text-danger uppercase tracking-widest mb-3">
            {t.problem.eyebrow}
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
            {t.problem.title}
          </h2>
        </motion.div>

        {/* Marquee banner */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mb-16 overflow-hidden rounded-2xl bg-ink"
        >
          <div className="flex whitespace-nowrap py-5 animate-marquee">
            {[...Array(2)].map((_, group) => (
              <div key={group} className="flex items-center shrink-0">
                {[...Array(4)].map((_, i) => (
                  <span key={i} className="flex items-center gap-6 mx-6">
                    <span className="text-sm md:text-base font-semibold uppercase tracking-widest text-white">
                      {t.problem.marqueeLeft}
                    </span>
                    <span className="text-lime text-lg">›  ›  ›  ›</span>
                    <span className="text-sm md:text-base font-semibold uppercase tracking-widest text-white/40">
                      {t.problem.marqueeRight}
                    </span>
                  </span>
                ))}
              </div>
            ))}
          </div>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {problems.map((problem, i) => (
            <motion.div
              key={problem.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`bg-surface rounded-3xl p-6 border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all ${
                i >= 3 ? "lg:col-span-1" : ""
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-ink/5 flex items-center justify-center mb-4">
                <problem.icon size={20} className="text-ink" />
              </div>
              <h3 className="text-base font-semibold text-ink mb-2">
                {problem.title}
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {problem.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
