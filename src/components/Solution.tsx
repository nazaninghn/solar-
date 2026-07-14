"use client";

import { motion } from "framer-motion";
import { BarChart3, Battery, PiggyBank } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const icons = [BarChart3, Battery, PiggyBank];

export default function Solution() {
  const { t } = useLanguage();
  const solutions = t.solution.items.map((item, i) => ({ ...item, icon: icons[i] }));

  return (
    <section className="py-24 lg:py-32 bg-surface">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20">
          {/* Left: sticky heading + checklist */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="lg:sticky lg:top-32 self-start"
          >
            <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
              {t.solution.eyebrow}
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
              {t.solution.title}
            </h2>
            <p className="mt-4 text-gray-500 max-w-md">
              {t.solution.subtitle}
            </p>

            <div className="mt-10 border-t border-gray-200">
              {solutions.map((solution, i) => (
                <motion.div
                  key={solution.title}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-4 py-6 border-b border-gray-200"
                >
                  <div className="w-11 h-11 shrink-0 rounded-full bg-ink flex items-center justify-center">
                    <solution.icon size={20} className="text-lime" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-ink mb-1">
                      {solution.title}
                    </h3>
                    <p className="text-sm text-gray-500 leading-relaxed">
                      {solution.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right: sticky visual panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="lg:sticky lg:top-32 self-start"
          >
            <div className="relative overflow-hidden rounded-3xl aspect-square lg:aspect-auto lg:h-[520px]">
              <img
                src="/solution-bg.png"
                alt="SolarFlow energy solution"
                className="absolute inset-0 w-full h-full object-cover rounded-3xl"
              />
              {/* Overlay with icons */}
              <div className="absolute inset-0 bg-gradient-to-t from-ink/60 via-transparent to-ink/30 rounded-3xl" />
              <div className="relative z-10 flex items-center justify-center h-full">
                <div className="grid grid-cols-3 gap-4 p-10">
                  {[BarChart3, Battery, PiggyBank].map((Icon, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 15 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.15 }}
                      className="w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center"
                    >
                      <Icon size={26} className="text-lime" />
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
