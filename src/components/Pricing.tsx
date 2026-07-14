"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function Pricing() {
  const { t, locale } = useLanguage();
  const planMeta = [
    { price: "€990", highlighted: false },
    { price: "€2.490", highlighted: true },
    { price: locale === "tr" ? "Özel" : "Custom", highlighted: false },
  ];
  const plans = t.pricing.plans.map((plan, i) => ({ ...plan, ...planMeta[i] }));

  return (
    <section id="pricing" className="py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
            {t.pricing.eyebrow}
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
            {t.pricing.title}
          </h2>
          <p className="mt-4 text-gray-500">
            {t.pricing.subtitle}
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className={`relative rounded-3xl p-8 border transition-shadow ${
                plan.highlighted
                  ? "bg-ink border-ink shadow-xl"
                  : "bg-surface border-gray-100 hover:shadow-lg"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-lime text-ink text-[10px] font-bold uppercase tracking-wider rounded-full">
                  {t.pricing.mostPopular}
                </div>
              )}

              <h3 className={`text-lg font-bold ${plan.highlighted ? "text-white" : "text-ink"}`}>{plan.name}</h3>
              <div className="mt-3 flex items-baseline gap-1">
                <span className={`text-3xl font-extrabold ${plan.highlighted ? "text-white" : "text-ink"}`}>
                  {plan.price}
                </span>
                <span className={`text-sm ${plan.highlighted ? "text-white/40" : "text-gray-400"}`}>{plan.period}</span>
              </div>
              <p className={`mt-3 text-sm ${plan.highlighted ? "text-white/60" : "text-gray-500"}`}>{plan.description}</p>

              <button
                className={`mt-6 w-full py-3 px-4 rounded-full text-sm font-semibold transition-all ${
                  plan.highlighted
                    ? "bg-lime text-ink hover:bg-lime/90"
                    : "bg-ink/5 text-ink hover:bg-ink/10"
                }`}
              >
                {plan.cta}
              </button>

              <div className="mt-8 space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-2.5">
                    <Check size={16} className={`mt-0.5 shrink-0 ${plan.highlighted ? "text-lime" : "text-primary-green"}`} />
                    <span className={`text-sm ${plan.highlighted ? "text-white/70" : "text-gray-600"}`}>{feature}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
