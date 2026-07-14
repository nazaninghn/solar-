"use client";

import { motion } from "framer-motion";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const companies = [
  "BASF",
  "Siemens",
  "ThyssenKrupp",
  "Bosch",
  "Continental",
  "Volkswagen",
  "HeidelbergCement",
  "Evonik",
];

export default function TrustedBy() {
  const { t } = useLanguage();

  return (
    <section className="py-16 border-b border-gray-100 bg-surface">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-xs font-semibold text-gray-400 uppercase tracking-widest mb-10"
        >
          {t.trustedBy.label}
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6"
        >
          {companies.map((company) => (
            <div
              key={company}
              className="flex items-center justify-center h-12 px-5 rounded-lg bg-gray-50 border border-gray-100"
            >
              <span className="text-base font-bold text-gray-300 tracking-tight">
                {company}
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
