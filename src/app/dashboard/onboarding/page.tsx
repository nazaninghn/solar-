"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Plug, ShieldAlert, TrendingUp, Check, ArrowRight, ArrowLeft, RefreshCw } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useFactory } from "@/lib/factory/FactoryContext";
import { onboardingText } from "@/lib/i18n/onboarding";
import DevicesPanel from "@/components/dashboard/DevicesPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const fpBase = (factoryId: number) => `${API}/api/v1/factories/${factoryId}/failure-prediction`;

function authHeaders(json = false): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

type Setup = {
  deviceCount: number;
  assessedCount: number;
  topRisk: { level: string; score: number } | null;
  priceRows: number;
};

async function loadSetup(factoryId: number): Promise<Setup> {
  const [devicesRes, overviewRes, marketRes] = await Promise.all([
    fetch(`${API}/api/v1/factories/${factoryId}/devices`, { headers: authHeaders() }),
    fetch(`${fpBase(factoryId)}/overview`, { headers: authHeaders() }),
    fetch(`${API}/api/v1/market/status`, { headers: authHeaders() }),
  ]);

  const devices = devicesRes.ok ? await devicesRes.json() : [];
  const overview = overviewRes.ok ? await overviewRes.json() : null;
  const market = marketRes.ok ? await marketRes.json() : null;

  let assessedCount = 0;
  let topRisk: { level: string; score: number } | null = null;
  if (overview) {
    const assessed = (overview.devices ?? []).filter(
      (d: { assessment: unknown }) => d.assessment != null,
    );
    assessedCount = assessed.length;
    for (const d of assessed) {
      const a = d.assessment as { risk_level: string; risk_score: number };
      if (!topRisk || a.risk_score > topRisk.score) {
        topRisk = { level: a.risk_level, score: a.risk_score };
      }
    }
  }

  return {
    deviceCount: Array.isArray(devices) ? devices.length : 0,
    assessedCount,
    topRisk,
    priceRows: market?.price_rows ?? 0,
  };
}

const RISK_COLOR: Record<string, string> = {
  LOW: "text-primary-green",
  MEDIUM: "text-warning",
  HIGH: "text-energy-orange",
  CRITICAL: "text-danger",
};

export default function OnboardingPage() {
  const { locale } = useLanguage();
  const o = onboardingText[locale];
  const { activeId } = useFactory();

  const [setup, setSetup] = useState<Setup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [step, setStep] = useState(1);
  const [running, setRunning] = useState(false);

  const [reloadKey, setReloadKey] = useState(0);
  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      try {
        const data = await loadSetup(activeId);
        if (cancelled) return;
        setSetup(data);
        setError(false);
      } catch (err) {
        console.error("Onboarding status load failed", err);
        if (!cancelled) setError(true);
      }
      if (!cancelled) setLoading(false);
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [reloadKey, activeId]);

  async function runAssessment() {
    setRunning(true);
    try {
      const res = await fetch(`${fpBase(activeId)}/assess`, { method: "POST", headers: authHeaders() });
      if (res.ok) reload();
    } catch (err) {
      console.error("Assessment failed", err);
    }
    setRunning(false);
  }

  const step1Done = (setup?.deviceCount ?? 0) > 0;
  const step2Done = (setup?.assessedCount ?? 0) > 0;
  const step3Done = (setup?.priceRows ?? 0) > 0;

  const steps = [
    { n: 1, icon: Plug, label: o.step1.label, done: step1Done },
    { n: 2, icon: ShieldAlert, label: o.step2.label, done: step2Done },
    { n: 3, icon: TrendingUp, label: o.step3.label, done: step3Done },
  ];

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">{o.title}</h1>
        <p className="text-sm text-gray-500 mt-1">{o.subtitle}</p>
      </div>

      {error && <div className="rounded-2xl border border-danger/30 bg-danger/5 p-4 text-sm text-danger">{o.loadError}</div>}

      {/* Stepper */}
      <div className="flex items-center gap-2">
        {steps.map((s, i) => (
          <div key={s.n} className="flex items-center gap-2 flex-1">
            <button
              onClick={() => setStep(s.n)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border transition-colors w-full text-left ${
                step === s.n ? "border-royal bg-royal/5" : "border-gray-200 hover:bg-gray-50"
              }`}
            >
              <span className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${s.done ? "bg-primary-green text-white" : step === s.n ? "bg-royal text-white" : "bg-gray-100 text-gray-400"}`}>
                {s.done ? <Check size={16} /> : <s.icon size={16} />}
              </span>
              <span className="min-w-0">
                <span className="block text-[11px] text-gray-400">{o.stepOf} {s.n}</span>
                <span className="block text-xs font-semibold text-ink truncate">{s.label}</span>
              </span>
            </button>
            {i < steps.length - 1 && <ArrowRight size={16} className="text-gray-300 shrink-0 hidden sm:block" />}
          </div>
        ))}
      </div>

      {/* Step body */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        {step === 1 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <StepHeader title={o.step1.title} body={o.step1.body} done={step1Done}
              status={step1Done ? `${setup?.deviceCount} ${o.step1.doneMsg}` : o.step1.todoMsg} doneLabel={o.done} todoLabel={o.todo} />
            <DevicesPanel />
          </motion.div>
        )}

        {step === 2 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <StepHeader title={o.step2.title} body={o.step2.body} done={step2Done}
              status={
                step2Done
                  ? `${setup?.assessedCount} ${o.step2.doneMsg} ${setup?.topRisk ? setup.topRisk.level : ""}`
                  : step1Done ? o.step2.todoMsg : o.step2.needDevice
              }
              statusColor={step2Done && setup?.topRisk ? RISK_COLOR[setup.topRisk.level] : undefined}
              doneLabel={o.done} todoLabel={o.todo} />
            <div className="flex flex-wrap gap-3">
              <button onClick={runAssessment} disabled={running || !step1Done}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black disabled:opacity-50">
                <RefreshCw size={16} className={running ? "animate-spin" : ""} />
                {running ? o.step2.running : o.step2.run}
              </button>
              <Link href="/dashboard/maintenance" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-ink hover:bg-gray-50">
                {o.step2.openPage}
                <ArrowRight size={15} />
              </Link>
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <StepHeader title={o.step3.title} body={o.step3.body} done={step3Done}
              status={step3Done ? `${setup?.priceRows} ${o.step3.priceRows}. ${o.step3.doneMsg}` : o.step3.noPrices}
              doneLabel={o.done} todoLabel={o.todo} />
            <Link href="/dashboard/market" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-royal text-white text-sm font-semibold hover:bg-royal/90">
              {o.step3.openPage}
              <ArrowRight size={15} />
            </Link>
          </motion.div>
        )}
      </div>

      {/* Nav */}
      <div className="flex items-center justify-between">
        <button onClick={() => setStep((s) => Math.max(1, s - 1))} disabled={step === 1}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-ink hover:bg-gray-50 disabled:opacity-40">
          <ArrowLeft size={15} />
          {o.back}
        </button>
        {step < 3 ? (
          <button onClick={() => setStep((s) => Math.min(3, s + 1))}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black">
            {o.next}
            <ArrowRight size={15} />
          </button>
        ) : (
          <Link href="/dashboard" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black">
            {o.finish}
            <Check size={15} />
          </Link>
        )}
      </div>
    </div>
  );
}

function StepHeader({
  title,
  body,
  status,
  done,
  doneLabel,
  todoLabel,
  statusColor,
}: {
  title: string;
  body: string;
  status: string;
  done: boolean;
  doneLabel: string;
  todoLabel: string;
  statusColor?: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${done ? "bg-primary-green/10 text-primary-green" : "bg-gray-100 text-gray-400"}`}>
          {done ? doneLabel : todoLabel}
        </span>
      </div>
      <p className="text-sm text-gray-500">{body}</p>
      <p className={`text-sm font-medium mt-2 ${statusColor ?? "text-ink"}`}>{status}</p>
    </div>
  );
}
