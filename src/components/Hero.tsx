"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function Hero() {
  const { t } = useLanguage();

  return (
    <section className="relative min-h-screen overflow-hidden bg-ink">
      {/* Photo background */}
      <div className="absolute inset-0">
        <Image
          src="/hero-solar-panel.png"
          alt="Solar panel installed among green foliage"
          fill
          priority
          className="object-cover"
        />
        {/* Scrim for text legibility */}
        <div className="absolute inset-0 bg-gradient-to-r from-ink/85 via-ink/50 to-ink/20" />
        <div className="absolute inset-0 bg-gradient-to-t from-ink/70 via-transparent to-transparent" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 pt-40 pb-24 min-h-screen flex items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="max-w-2xl"
        >
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-[1.05] tracking-tight">
            {t.hero.headline1}{" "}
            <span className="text-lime">{t.hero.headline2}</span>
          </h1>

          <p className="mt-6 text-lg text-white/70 leading-relaxed max-w-md">
            {t.hero.subtitle}
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <a
              href="#cta"
              className="group inline-flex items-center gap-2 px-7 py-3.5 text-sm font-semibold text-ink bg-lime rounded-full hover:bg-lime/90 transition-all"
            >
              {t.hero.ctaPrimary}
              <svg
                className="w-4 h-4 group-hover:translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
            <a
              href="#pricing"
              className="inline-flex items-center px-7 py-3.5 text-sm font-semibold text-white border border-white/30 rounded-full hover:bg-white/10 transition-all"
            >
              {t.hero.ctaSecondary}
            </a>
          </div>

          {/* Trust Metrics */}
          <div className="mt-16 flex items-center gap-8">
            <div>
              <p className="text-2xl font-bold text-white">{t.hero.statCost}</p>
              <p className="text-xs text-white/50">{t.hero.statCostLabel}</p>
            </div>
            <div className="w-px h-8 bg-white/20" />
            <div>
              <p className="text-2xl font-bold text-white">{t.hero.statFacilities}</p>
              <p className="text-xs text-white/50">{t.hero.statFacilitiesLabel}</p>
            </div>
            <div className="w-px h-8 bg-white/20" />
            <div>
              <p className="text-2xl font-bold text-white">{t.hero.statSavings}</p>
              <p className="text-xs text-white/50">{t.hero.statSavingsLabel}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-warm-bg to-transparent" />
    </section>
  );
}
