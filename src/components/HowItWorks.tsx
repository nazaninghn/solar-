"use client";

import { motion } from "framer-motion";
import { Plug, Database, Brain, Lightbulb } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const icons = [Plug, Database, Brain, Lightbulb];
const stepNumbers = ["01", "02", "03", "04"];

export default function HowItWorks() {
  const { t } = useLanguage();
  const steps = t.howItWorks.items.map((item, i) => ({ ...item, icon: icons[i], step: stepNumbers[i] }));

  return (
    <section id="how-it-works" className="py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20">
          {/* Left: sticky heading */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="lg:sticky lg:top-32 self-start"
          >
            <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
              {t.howItWorks.eyebrow}
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
              {t.howItWorks.title}
            </h2>
            <p className="mt-4 text-gray-500 max-w-md">
              {t.howItWorks.subtitle}
            </p>
          </motion.div>

          {/* Right: vertical timeline card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 }}
            className="rounded-3xl bg-warm-bg border border-gray-100 p-8 lg:p-10"
          >
            <div className="relative">
              <div className="absolute left-[19px] top-2 bottom-2 w-px bg-gray-200" />
              <div className="space-y-10">
                {steps.map((step, i) => (
                  <motion.div
                    key={step.title}
                    initial={{ opacity: 0, x: 15 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.12 }}
                    className="relative flex items-start gap-5"
                  >
                    <div className="relative z-10 w-10 h-10 shrink-0 rounded-full bg-ink flex items-center justify-center">
                      <step.icon size={16} className="text-lime" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-primary-green mb-1">
                        {t.howItWorks.stepLabel} {step.step}
                      </div>
                      <h3 className="text-base font-semibold text-ink mb-1.5">
                        {step.title}
                      </h3>
                      <p className="text-sm text-gray-500 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
