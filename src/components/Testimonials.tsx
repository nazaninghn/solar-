"use client";

import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const people = [
  { name: "Thomas Müller", company: "Deutsche Stahl AG", avatar: "TM" },
  { name: "Sarah Chen", company: "Pacific Manufacturing Ltd", avatar: "SC" },
  { name: "Henrik Johansson", company: "Nordic Pulp & Paper", avatar: "HJ" },
];

export default function Testimonials() {
  const { t } = useLanguage();
  const testimonials = t.testimonials.items.map((item, i) => ({ ...item, ...people[i] }));

  return (
    <section className="py-24 lg:py-32 bg-surface">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-2xl mx-auto mb-16"
        >
          <p className="text-xs font-semibold text-primary-green uppercase tracking-widest mb-3">
            {t.testimonials.eyebrow}
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-ink leading-tight tracking-tight">
            {t.testimonials.title}
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, i) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="bg-warm-bg rounded-3xl p-6 lg:p-8 border border-gray-100 hover:shadow-lg transition-shadow"
            >
              {/* Stars */}
              <div className="flex items-center gap-0.5 mb-4">
                {[...Array(5)].map((_, s) => (
                  <Star
                    key={s}
                    size={14}
                    className="text-lime fill-lime"
                  />
                ))}
              </div>

              <p className="text-sm text-gray-600 leading-relaxed mb-6">
                &ldquo;{testimonial.quote}&rdquo;
              </p>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-ink flex items-center justify-center">
                  <span className="text-xs font-bold text-lime">
                    {testimonial.avatar}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink">
                    {testimonial.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {testimonial.role} · {testimonial.company}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
