"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import LanguageSwitcher from "./LanguageSwitcher";

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = useLanguage();

  const links = [
    { label: t.nav.home, href: "#" },
    { label: t.nav.about, href: "#how-it-works" },
    { label: t.nav.services, href: "#features" },
    { label: t.nav.pricing, href: "#pricing" },
    { label: t.nav.contact, href: "#cta" },
  ];

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="absolute top-0 left-0 right-0 z-50"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-green to-secondary-green flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white">
              Solar<span className="text-lime">Flow</span>
            </span>
          </a>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-8">
            {links.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-white/80 hover:text-white transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <LanguageSwitcher dark />
            <a
              href="/login"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white/80 hover:text-white transition-colors"
            >
              {t.nav.logIn}
            </a>
            <a
              href="/register"
              className="inline-flex items-center px-5 py-2.5 text-sm font-semibold text-primary-navy bg-primary-green rounded-full hover:bg-secondary-green transition-colors shadow-lg shadow-primary-green/25"
            >
              {t.nav.createAccount}
            </a>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-1">
            <LanguageSwitcher dark />
            <button
              className="p-2 text-white"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden bg-ink/95 backdrop-blur-xl border-b border-white/10 px-6 py-4"
        >
          <div className="flex flex-col gap-3">
            {links.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-white/80 hover:text-white transition-colors py-2"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <div className="mt-3 pt-3 border-t border-white/10 flex flex-col gap-2">
              <a
                href="/login"
                className="px-4 py-2.5 text-sm font-medium text-white/80 hover:text-white text-center rounded-full border border-white/20"
                onClick={() => setMobileOpen(false)}
              >
                {t.nav.logIn}
              </a>
              <a
                href="/register"
                className="px-4 py-2.5 text-sm font-semibold text-primary-navy bg-primary-green rounded-full text-center"
                onClick={() => setMobileOpen(false)}
              >
                {t.nav.createAccount}
              </a>
            </div>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}
