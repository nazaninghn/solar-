"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Rocket, ArrowRight, X, Check } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useFactory } from "@/lib/factory/FactoryContext";
import { onboardingText } from "@/lib/i18n/onboarding";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const DISMISS_KEY = "solarflow-onboarding-dismissed";

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export default function OnboardingBanner() {
  const { locale } = useLanguage();
  const o = onboardingText[locale];
  const { activeId } = useFactory();

  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number }>({ done: 0, total: 3 });

  useEffect(() => {
    let cancelled = false;
    if (typeof window !== "undefined" && window.localStorage.getItem(DISMISS_KEY) === "1") {
      return;
    }
    async function check() {
      try {
        const [devicesRes, overviewRes, marketRes] = await Promise.all([
          fetch(`${API}/api/v1/factories/${activeId}/devices`, { headers: authHeaders() }),
          fetch(`${API}/api/v1/factories/${activeId}/failure-prediction/overview`, { headers: authHeaders() }),
          fetch(`${API}/api/v1/market/status`, { headers: authHeaders() }),
        ]);
        const devices = devicesRes.ok ? await devicesRes.json() : [];
        const overview = overviewRes.ok ? await overviewRes.json() : null;
        const market = marketRes.ok ? await marketRes.json() : null;

        const step1 = Array.isArray(devices) && devices.length > 0;
        const step2 = !!overview && (overview.devices ?? []).some((d: { assessment: unknown }) => d.assessment != null);
        const step3 = (market?.price_rows ?? 0) > 0;
        const done = [step1, step2, step3].filter(Boolean).length;

        if (cancelled) return;
        setProgress({ done, total: 3 });
        setVisible(done < 3);
      } catch (err) {
        console.error("Onboarding banner check failed", err);
      }
    }
    check();
    return () => {
      cancelled = true;
    };
  }, [activeId]);

  function dismiss() {
    setVisible(false);
    if (typeof window !== "undefined") window.localStorage.setItem(DISMISS_KEY, "1");
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="rounded-2xl border border-royal/20 bg-gradient-to-r from-royal/5 to-lime/5 p-5 flex flex-col sm:flex-row sm:items-center gap-4"
        >
          <div className="w-11 h-11 rounded-xl bg-ink flex items-center justify-center shrink-0">
            <Rocket size={20} className="text-lime" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-ink">{o.bannerTitle}</p>
            <p className="text-xs text-gray-500 mt-0.5">{o.bannerSubtitle}</p>
            <div className="flex items-center gap-1.5 mt-2">
              {Array.from({ length: progress.total }).map((_, i) => (
                <span key={i} className={`h-1.5 flex-1 max-w-16 rounded-full ${i < progress.done ? "bg-primary-green" : "bg-gray-200"}`} />
              ))}
              <span className="text-[11px] text-gray-400 ml-1 inline-flex items-center gap-1">
                <Check size={11} className="text-primary-green" />
                {progress.done}/{progress.total}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link href="/dashboard/onboarding" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black transition-colors">
              {o.bannerCta}
              <ArrowRight size={15} />
            </Link>
            <button onClick={dismiss} aria-label={o.dismiss} className="p-2 rounded-lg text-gray-400 hover:text-ink hover:bg-white/60 transition-colors">
              <X size={16} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
