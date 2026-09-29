"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Building2, User, Bell, Shield, Globe, Cpu } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useAuth } from "@/lib/auth/AuthContext";
import { useFactory } from "@/lib/factory/FactoryContext";
import DevicesPanel from "@/components/dashboard/DevicesPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function authHeaders(json = false): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

type SaveState = "idle" | "saving" | "saved" | "error";

export default function SettingsPage() {
  const { t, locale, setLocale } = useLanguage();
  const s = t.dashboard.settings;
  const [activeTab, setActiveTab] = useState("factory");

  const tabs = [
    { id: "factory", label: s.factory, icon: Building2 },
    { id: "profile", label: s.profile, icon: User },
    { id: "notifications", label: s.notifications, icon: Bell },
    { id: "security", label: s.security, icon: Shield },
    { id: "devices", label: s.devices, icon: Cpu },
    { id: "locale", label: s.language, icon: Globe },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{s.title}</h1>
        <p className="text-sm text-gray-500 mt-1">{s.subtitle}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id ? "bg-white text-ink shadow-sm" : "text-gray-500 hover:text-ink"
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "factory" && <FactoryTab />}
      {activeTab === "profile" && <ProfileTab />}
      {activeTab === "notifications" && <NotificationsTab />}
      {activeTab === "security" && <SecurityTab />}
      {activeTab === "devices" && <DevicesPanel />}
      {activeTab === "locale" && <LocaleTab locale={locale} setLocale={setLocale} />}
    </div>
  );
}

function SaveButton({ state, label, savingLabel, savedLabel }: { state: SaveState; label: string; savingLabel: string; savedLabel: string }) {
  return (
    <button
      type="submit"
      disabled={state === "saving"}
      className="px-6 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors disabled:opacity-60"
    >
      {state === "saving" ? savingLabel : state === "saved" ? savedLabel : label}
    </button>
  );
}

const inputCls = "w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm text-ink focus:outline-none focus:border-royal";

function FactoryTab() {
  const { activeId } = useFactory();
  // Remount the form whenever the active factory changes, so its fields
  // re-initialise from the new factory without a state-syncing effect
  // (this Next/React version's lint forbids setState inside an effect).
  return <FactoryForm key={activeId} />;
}

function FactoryForm() {
  const { t } = useLanguage();
  const s = t.dashboard.settings;
  const { active, activeId, reload } = useFactory();

  const [name, setName] = useState(active?.name ?? "");
  const [address, setAddress] = useState(active?.address ?? "");
  const [industry, setIndustry] = useState(active?.industry ?? "");
  const [currency, setCurrency] = useState(active?.currency ?? "");
  const [solar, setSolar] = useState(active?.solar_capacity_kw != null ? String(active.solar_capacity_kw) : "");
  const [battery, setBattery] = useState(active?.battery_capacity_kwh != null ? String(active.battery_capacity_kwh) : "");
  const [state, setState] = useState<SaveState>("idle");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("saving");
    try {
      const res = await fetch(`${API}/api/v1/factories/${activeId}`, {
        method: "PATCH",
        headers: authHeaders(true),
        body: JSON.stringify({
          name: name.trim(),
          address: address.trim() || null,
          industry: industry.trim() || null,
          currency: currency.trim() || null,
          solar_capacity_kw: solar === "" ? null : Number(solar),
          battery_capacity_kwh: battery === "" ? null : Number(battery),
        }),
      });
      if (!res.ok) throw new Error(`factory patch ${res.status}`);
      setState("saved");
      reload();
      setTimeout(() => setState("idle"), 2000);
    } catch (err) {
      console.error("Factory save failed", err);
      setState("error");
    }
  }

  return (
    <motion.form onSubmit={submit} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
      <h2 className="text-base font-semibold text-ink">{s.factoryInfo}</h2>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.factoryName}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.address}</label>
          <input value={address} onChange={(e) => setAddress(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.industry}</label>
          <input value={industry} onChange={(e) => setIndustry(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.currency}</label>
          <input value={currency} onChange={(e) => setCurrency(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.solarCapacity}</label>
          <input type="number" value={solar} onChange={(e) => setSolar(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.batteryCapacity}</label>
          <input type="number" value={battery} onChange={(e) => setBattery(e.target.value)} className={inputCls} />
        </div>
      </div>
      {state === "error" && <p className="text-sm text-danger">{s.saveError}</p>}
      <SaveButton state={state} label={s.save} savingLabel={s.saving} savedLabel={s.saved} />
    </motion.form>
  );
}

function ProfileTab() {
  const { t } = useLanguage();
  const s = t.dashboard.settings;
  const { user } = useAuth();

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
      <h2 className="text-base font-semibold text-ink">{s.userProfile}</h2>
      <p className="text-xs text-gray-500 rounded-xl bg-gray-50 border border-gray-100 p-3">{s.profileReadOnly}</p>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.name}</label>
          <input value={user?.full_name ?? ""} readOnly disabled className={`${inputCls} bg-gray-50 text-gray-500`} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.email}</label>
          <input value={user?.email ?? ""} readOnly disabled className={`${inputCls} bg-gray-50 text-gray-500`} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.role}</label>
          <input value={user?.role ?? ""} readOnly disabled className={`${inputCls} bg-gray-50 text-gray-500`} />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">{s.organization}</label>
          <input value={user?.organization?.name ?? ""} readOnly disabled className={`${inputCls} bg-gray-50 text-gray-500`} />
        </div>
      </div>
    </motion.div>
  );
}

function SecurityTab() {
  const { t } = useLanguage();
  const s = t.dashboard.settings;
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
      <h2 className="text-base font-semibold text-ink">{s.securitySettings}</h2>
      <p className="text-sm text-gray-600 rounded-xl bg-gray-50 border border-gray-100 p-4">{s.passwordReadOnly}</p>
      <div className="pt-2 border-t border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-2">{s.twoFactor}</h3>
        <p className="text-xs text-gray-500">{s.twoFactorDesc}</p>
        <button disabled className="mt-3 px-4 py-2 border border-gray-200 rounded-xl text-sm font-medium text-gray-400 cursor-not-allowed">
          {s.enable2FA}
        </button>
      </div>
    </motion.div>
  );
}

function NotificationsTab() {
  const { t } = useLanguage();
  const s = t.dashboard.settings;
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-4">
      <h2 className="text-base font-semibold text-ink">{s.notifPrefs}</h2>
      {t.settingsPage.notificationItems.map((item) => (
        <div key={item} className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
          <span className="text-sm text-ink">{item}</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" defaultChecked className="sr-only peer" />
            <div className="w-9 h-5 bg-gray-200 peer-checked:bg-primary-green rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
          </label>
        </div>
      ))}
    </motion.div>
  );
}

function LocaleTab({ locale, setLocale }: { locale: "en" | "tr"; setLocale: (l: "en" | "tr") => void }) {
  const { t } = useLanguage();
  const s = t.dashboard.settings;
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-4">
      <h2 className="text-base font-semibold text-ink">{s.langRegion}</h2>
      <div>
        <label className="text-xs text-gray-500 mb-1 block">{s.displayLang}</label>
        <select value={locale} onChange={(e) => setLocale(e.target.value as "en" | "tr")} className={inputCls}>
          <option value="en">English</option>
          <option value="tr">Türkçe</option>
        </select>
      </div>
    </motion.div>
  );
}
