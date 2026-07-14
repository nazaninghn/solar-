"use client";

import { motion } from "framer-motion";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function CTA() {
  const { t } = useLanguage();

  return (
    <section id="cta" className="py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Left: dark panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative overflow-hidden bg-ink rounded-3xl p-10 lg:p-12 flex flex-col justify-between min-h-[320px]"
          >
            <div className="absolute top-0 right-0 w-72 h-72 bg-primary-green/10 rounded-full blur-3xl" />
            <div className="relative z-10">
              <h2 className="text-2xl md:text-3xl font-bold text-white leading-tight tracking-tight">
                {t.cta.headline1}{" "}
                <span className="text-lime">{t.cta.headline2}</span>
              </h2>
              <p className="mt-4 text-white/60">
                {t.cta.subtitle1}
              </p>
            </div>
            <a
              href="#"
              className="relative z-10 mt-8 inline-flex items-center self-start px-7 py-3.5 text-sm font-semibold text-ink bg-lime rounded-full hover:bg-lime/90 transition-all"
            >
              {t.cta.bookDemo}
              <svg
                className="ml-2 w-4 h-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
          </motion.div>

          {/* Right: light panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="relative overflow-hidden bg-gradient-to-br from-primary-green/10 via-secondary-green/10 to-warm-bg border border-gray-100 rounded-3xl p-10 lg:p-12 flex flex-col justify-between min-h-[320px]"
          >
            <div className="relative z-10">
              <h2 className="text-2xl md:text-3xl font-bold text-ink leading-tight tracking-tight">
                {t.cta.headline3}
              </h2>
              <p className="mt-4 text-gray-600">
                {t.cta.subtitle2}
              </p>
            </div>
            <a
              href="#"
              className="relative z-10 mt-8 inline-flex items-center self-start px-7 py-3.5 text-sm font-semibold text-ink border border-ink/20 rounded-full hover:bg-ink/5 transition-all"
            >
              {t.cta.calculateSavings}
            </a>
          </motion.div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          {t.cta.footnote}
        </p>
      </div>
    </section>
  );
}
