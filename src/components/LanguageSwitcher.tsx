"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Globe, Check } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const options: { code: "en" | "tr"; label: string; flag: string }[] = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "tr", label: "Türkçe", flag: "🇹🇷" },
];

export default function LanguageSwitcher({ dark = true }: { dark?: boolean }) {
  const { locale, setLocale } = useLanguage();
  const [open, setOpen] = useState(false);
  const current = options.find((o) => o.code === locale)!;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium transition-colors ${
          dark ? "text-white/80 hover:text-white hover:bg-white/10" : "text-ink hover:bg-mist/60"
        }`}
        aria-label="Change language"
      >
        <Globe size={15} />
        <span className="text-xs font-semibold uppercase">{current.code}</span>
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 w-40 rounded-2xl border border-gray-100 bg-white shadow-xl overflow-hidden py-1.5 z-20"
            >
              {options.map((o) => (
                <button
                  key={o.code}
                  onClick={() => {
                    setLocale(o.code);
                    setOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-ink hover:bg-mist/50 transition-colors"
                >
                  <span>{o.flag}</span>
                  <span className="flex-1 text-left">{o.label}</span>
                  {locale === o.code && <Check size={14} className="text-lime-dark" />}
                </button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
