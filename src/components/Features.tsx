"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Battery,
  BarChart3,
  Cloud,
  FileText,
  Leaf,
  Activity,
} from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const icons = [Brain, Battery, BarChart3, Cloud, FileText, Leaf, Activity];

export default function Features() {
  const { t } = useLanguage();
  const features = t.features.items.map((item, i) => ({ ...item, icon: icons[i] }));

  return (
    <section id="features" className="py-24 lg:py-32 bg-surface">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
            {t.features.eyebrow}
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
            {t.features.title}
          </h2>
          <p className="mt-4 text-gray-500">
            {t.features.subtitle}
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className={`group relative bg-warm-bg rounded-3xl p-6 border border-gray-100 hover:border-ink/10 hover:shadow-lg hover:-translate-y-0.5 transition-all ${
                i === 6 ? "md:col-span-2 lg:col-span-1" : ""
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-ink flex items-center justify-center mb-4">
                <feature.icon size={20} className="text-lime" />
              </div>
              <h3 className="text-base font-semibold text-ink mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
