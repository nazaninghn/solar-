"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, ReferenceLine,
} from "recharts";
import { Wrench, RefreshCw, ChevronDown, ChevronRight, ShieldAlert, Cpu, ClipboardList } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { FACTORY_ID } from "@/lib/factory";
import { maintenanceText } from "@/lib/i18n/maintenance";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const BASE = `${API}/api/v1/factories/${FACTORY_ID}/failure-prediction`;

type Indicator = {
  code: string; category: string; label: string; value: number | null;
  unit: string; threshold: number | null; score: number; message: string;
};
type Assessment = {
  id: number; assessed_at: string; risk_score: number; risk_level: string; method: string;
  ml_status: string; failure_probability: number | null; fault_type: string | null;
  irradiance_source: string | null; indicators: Indicator[]; top_reason: string | null;
  recommended_action: string | null; days_to_threshold: number | null;
};
type DeviceRisk = {
  device_id: number; device_name: string; device_type: string; status: string;
  assessment: Assessment | null;
};
type Overview = { assessed_at: string | null; counts: Record<string, number>; devices: DeviceRisk[] };
type HistoryPoint = { assessed_at: string; risk_score: number };
type FailureEvent = {
  id: number; device_id: number; occurred_at: string; failure_type: string;
  severity: string; description: string | null;
};
type ModelInfo = {
  horizon_minutes: number; test_metrics: Record<string, number>;
  lead_time: { mean_lead_min: number | null; detected: number; fault_onsets: number };
  limitations: string[];
};

const LEVEL_STYLE: Record<string, { text: string; bg: string; bar: string }> = {
  LOW: { text: "text-primary-green", bg: "bg-primary-green/10", bar: "bg-primary-green" },
  MEDIUM: { text: "text-warning", bg: "bg-warning/10", bar: "bg-warning" },
  HIGH: { text: "text-energy-orange", bg: "bg-energy-orange/15", bar: "bg-energy-orange" },
  CRITICAL: { text: "text-danger", bg: "bg-danger/10", bar: "bg-danger" },
  UNASSESSED: { text: "text-gray-400", bg: "bg-gray-100", bar: "bg-gray-300" },
};

function authHeaders(json = false): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

export default function MaintenancePage() {
  const { locale } = useLanguage();
  const m = maintenanceText[locale];

  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<FailureEvent[]>([]);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const [reloadKey, setReloadKey] = useState(0);
  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [o, e, mi] = await Promise.all([
          fetch(`${BASE}/overview`, { headers: authHeaders() }),
          fetch(`${BASE}/events`, { headers: authHeaders() }),
          fetch(`${BASE}/model`, { headers: authHeaders() }),
        ]);
        if (!o.ok) throw new Error(`overview ${o.status}`);
        const [overviewData, eventData, modelData] = await Promise.all([
          o.json(),
          e.ok ? e.json() : [],
          mi.ok ? mi.json() : null,
        ]);
        if (cancelled) return;
        setOverview(overviewData);
        setEvents(eventData);
        setModel(modelData);
        setError(false);
      } catch (err) {
        console.error("Failure prediction load failed", err);
        if (!cancelled) setError(true);
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  async function runAssessment() {
    setRunning(true);
    try {
      const res = await fetch(`${BASE}/assess`, { method: "POST", headers: authHeaders() });
      if (res.ok) setOverview(await res.json());
    } catch (err) {
      console.error("Assessment failed", err);
    }
    setRunning(false);
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  const levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNASSESSED"];
  const deviceName = (id: number) => overview?.devices.find((d) => d.device_id === id)?.device_name ?? `#${id}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">{m.title}</h1>
          <p className="text-sm text-gray-500 mt-1">{m.subtitle}</p>
          <p className="text-xs text-gray-400 mt-1">
            {m.lastAssessed}: {overview?.assessed_at ? new Date(overview.assessed_at).toLocaleString(m.dateLocale) : m.never}
          </p>
        </div>
        <button
          onClick={runAssessment}
          disabled={running}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-ink/90 disabled:opacity-60"
        >
          <RefreshCw size={16} className={running ? "animate-spin" : ""} />
          {running ? m.running : m.runAssessment}
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger/5 p-4 text-sm text-danger">{m.loadError}</div>
      )}

      {/* Risk counts */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {levels.map((level, i) => (
          <motion.div
            key={level}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="bg-white rounded-2xl p-5 border border-gray-100"
          >
            <p className="text-xs text-gray-400">{m.levels[level]}</p>
            <p className={`text-3xl font-bold mt-1 ${LEVEL_STYLE[level].text}`}>{overview?.counts[level] ?? 0}</p>
          </motion.div>
        ))}
      </div>

      {/* Device triage list */}
      <div className="bg-white rounded-2xl border border-gray-100">
        <div className="flex items-center gap-2 px-6 pt-6 pb-4">
          <ShieldAlert size={18} className="text-royal" />
          <h3 className="text-sm font-semibold text-ink">{m.devices}</h3>
        </div>
        {!overview || overview.devices.length === 0 ? (
          <p className="px-6 pb-6 text-sm text-gray-400">{m.noDevices}</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {overview.devices.map((d) => (
              <DeviceRow
                key={d.device_id}
                device={d}
                open={expanded === d.device_id}
                onToggle={() => setExpanded(expanded === d.device_id ? null : d.device_id)}
              />
            ))}
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Failure log */}
        <div className="lg:col-span-3 bg-white rounded-2xl p-6 border border-gray-100">
          <div className="flex items-center gap-2">
            <ClipboardList size={18} className="text-royal" />
            <h3 className="text-sm font-semibold text-ink">{m.events}</h3>
          </div>
          <p className="text-xs text-gray-400 mt-1 mb-4">{m.eventsHint}</p>
          {overview && overview.devices.length > 0 && (
            <EventForm devices={overview.devices} onCreated={reload} />
          )}
          {events.length === 0 ? (
            <p className="text-sm text-gray-400 mt-4">{m.noEvents}</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400">
                    <th className="py-2 pr-3 font-medium">{m.occurredAt}</th>
                    <th className="py-2 pr-3 font-medium">{m.device}</th>
                    <th className="py-2 pr-3 font-medium">{m.failureType}</th>
                    <th className="py-2 font-medium">{m.severity}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {events.map((e) => (
                    <tr key={e.id}>
                      <td className="py-2 pr-3 text-gray-500 whitespace-nowrap">{new Date(e.occurred_at).toLocaleString(m.dateLocale)}</td>
                      <td className="py-2 pr-3 text-ink">{deviceName(e.device_id)}</td>
                      <td className="py-2 pr-3 text-ink">{e.failure_type}{e.description ? <span className="block text-xs text-gray-400">{e.description}</span> : null}</td>
                      <td className={`py-2 font-semibold ${LEVEL_STYLE[e.severity]?.text ?? ""}`}>{m.levels[e.severity] ?? e.severity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Model card */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={18} className="text-royal" />
            <h3 className="text-sm font-semibold text-ink">{m.model}</h3>
          </div>
          {model && (
            <>
              <p className="text-sm text-gray-600">{m.modelHorizon} <span className="font-semibold text-ink">{model.horizon_minutes} {m.minutes}</span></p>
              <div className="grid grid-cols-2 gap-3 mt-4">
                {[
                  { label: m.rocAuc, value: model.test_metrics.roc_auc.toFixed(3) },
                  { label: m.precision, value: `${Math.round(model.test_metrics.precision * 100)}%` },
                  { label: m.recall, value: `${Math.round(model.test_metrics.recall * 100)}%` },
                  { label: m.leadTime, value: model.lead_time.mean_lead_min ? `${Math.round(model.lead_time.mean_lead_min)} ${m.minutes}` : "—" },
                ].map((s) => (
                  <div key={s.label} className="rounded-xl bg-gray-50 p-3">
                    <p className="text-xs text-gray-400">{s.label}</p>
                    <p className="text-sm font-bold text-ink">{s.value}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs font-semibold text-ink mt-5 mb-2">{m.limitations}</p>
              <ul className="space-y-1.5 text-xs text-gray-500 list-disc pl-4">
                {model.limitations.map((l) => <li key={l}>{l}</li>)}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function DeviceRow({ device, open, onToggle }: { device: DeviceRisk; open: boolean; onToggle: () => void }) {
  const { locale } = useLanguage();
  const m = maintenanceText[locale];
  const a = device.assessment;
  const level = a?.risk_level ?? "UNASSESSED";
  const style = LEVEL_STYLE[level];
  const top = a?.indicators.find((i) => i.code === a.top_reason);

  return (
    <div>
      <button onClick={onToggle} className="w-full text-left px-6 py-4 hover:bg-gray-50/60 transition-colors">
        <div className="flex items-start gap-3">
          {open ? <ChevronDown size={16} className="mt-1 text-gray-400 shrink-0" /> : <ChevronRight size={16} className="mt-1 text-gray-400 shrink-0" />}
          <div className="flex-1 min-w-0 grid md:grid-cols-12 gap-3 items-start">
            <div className="md:col-span-3 min-w-0">
              <p className="text-sm font-semibold text-ink truncate">{device.device_name}</p>
              <p className="text-xs text-gray-400">{device.device_type} · {device.status}</p>
            </div>
            <div className="md:col-span-3">
              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}>{m.levels[level]}</span>
              {a && (
                <div className="flex items-center gap-2 mt-1.5">
                  <div className="h-1.5 flex-1 rounded-full bg-gray-100 overflow-hidden">
                    <div className={`h-full rounded-full ${style.bar}`} style={{ width: `${a.risk_score}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-ink w-8 text-right">{Math.round(a.risk_score)}</span>
                </div>
              )}
            </div>
            <div className="md:col-span-2">
              <p className="text-xs text-gray-400">{m.faultIn3h}</p>
              <p className="text-sm font-semibold text-ink">
                {a?.failure_probability != null ? `${Math.round(a.failure_probability * 100)}%` : "—"}
              </p>
            </div>
            <div className="md:col-span-4 min-w-0">
              {a ? (
                <>
                  <p className="text-xs text-gray-600">{top ? top.message : m.mlStatus[a.ml_status]}</p>
                  {a.days_to_threshold != null && (
                    <p className="text-xs text-energy-orange mt-0.5">{m.daysToLimit}: {a.days_to_threshold} {m.days}</p>
                  )}
                </>
              ) : (
                <p className="text-xs text-gray-400">{m.notAssessed}</p>
              )}
            </div>
          </div>
        </div>
      </button>
      {open && a && <DeviceDetail deviceId={device.device_id} assessment={a} />}
    </div>
  );
}

function DeviceDetail({ deviceId, assessment }: { deviceId: number; assessment: Assessment }) {
  const { locale } = useLanguage();
  const m = maintenanceText[locale];
  const [history, setHistory] = useState<HistoryPoint[]>([]);

  useEffect(() => {
    fetch(`${BASE}/devices/${deviceId}/history?days=7`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : []))
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [deviceId]);

  const chart = history.map((h) => ({
    time: new Date(h.assessed_at).toLocaleString(m.dateLocale, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
    risk: h.risk_score,
  }));
  const indicators = [...assessment.indicators].sort((x, y) => y.score - x.score);

  return (
    <div className="px-6 pb-6 pl-12 grid lg:grid-cols-2 gap-6">
      <div>
        <p className="text-xs text-gray-500 mb-2">
          {m.mlStatus[assessment.ml_status] ?? assessment.ml_status}
          {assessment.fault_type ? ` · ${m.resembles}: ${assessment.fault_type}` : ""}
          {assessment.irradiance_source === "weather" ? ` · ${m.irradianceFromWeather}` : ""}
        </p>
        {assessment.recommended_action && (
          <div className="rounded-xl bg-royal/5 border border-royal/10 p-3 mb-3 flex gap-2">
            <Wrench size={14} className="text-royal mt-0.5 shrink-0" />
            <p className="text-xs text-ink"><span className="font-semibold">{m.action}:</span> {assessment.recommended_action}</p>
          </div>
        )}
        <p className="text-xs font-semibold text-ink mb-2">{m.indicators}</p>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-gray-400">
              <th className="py-1.5 pr-2 font-medium">{m.indicator}</th>
              <th className="py-1.5 pr-2 font-medium">{m.value}</th>
              <th className="py-1.5 font-medium text-right">{m.score}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {indicators.map((i) => (
              <tr key={i.code} title={i.message}>
                <td className="py-1.5 pr-2 text-ink">{i.label}</td>
                <td className="py-1.5 pr-2 text-gray-500">{i.value ?? "—"} {i.unit}</td>
                <td className={`py-1.5 text-right font-semibold ${i.score >= 50 ? "text-danger" : i.score > 0 ? "text-energy-orange" : "text-gray-400"}`}>{Math.round(i.score)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <p className="text-xs font-semibold text-ink mb-2">{m.history}</p>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} minTickGap={30} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <ReferenceLine y={50} stroke="#FDB94C" strokeDasharray="4 4" />
              <ReferenceLine y={75} stroke="#EF4444" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="risk" name={m.risk} stroke="#305293" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function EventForm({ devices, onCreated }: { devices: DeviceRisk[]; onCreated: () => void }) {
  const { locale } = useLanguage();
  const m = maintenanceText[locale];
  const [deviceId, setDeviceId] = useState(devices[0].device_id);
  const [occurredAt, setOccurredAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [failureType, setFailureType] = useState("");
  const [severity, setSeverity] = useState("HIGH");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!failureType.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${BASE}/events`, {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          device_id: deviceId,
          occurred_at: new Date(occurredAt).toISOString(),
          failure_type: failureType.trim(),
          severity,
          description: description.trim() || null,
        }),
      });
      if (res.ok) {
        setFailureType("");
        setDescription("");
        onCreated();
      }
    } catch (err) {
      console.error("Failed to log failure", err);
    }
    setSaving(false);
  }

  const input = "w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-ink focus:outline-none focus:border-royal";

  return (
    <form onSubmit={submit} className="grid sm:grid-cols-2 gap-3">
      <label className="text-xs text-gray-500">
        {m.device}
        <select className={input} value={deviceId} onChange={(e) => setDeviceId(Number(e.target.value))}>
          {devices.map((d) => <option key={d.device_id} value={d.device_id}>{d.device_name}</option>)}
        </select>
      </label>
      <label className="text-xs text-gray-500">
        {m.occurredAt}
        <input type="datetime-local" className={input} value={occurredAt} onChange={(e) => setOccurredAt(e.target.value)} />
      </label>
      <label className="text-xs text-gray-500">
        {m.failureType}
        <input className={input} value={failureType} maxLength={50} placeholder="STRING_FAULT" onChange={(e) => setFailureType(e.target.value)} />
      </label>
      <label className="text-xs text-gray-500">
        {m.severity}
        <select className={input} value={severity} onChange={(e) => setSeverity(e.target.value)}>
          {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((s) => <option key={s} value={s}>{m.levels[s]}</option>)}
        </select>
      </label>
      <label className="text-xs text-gray-500 sm:col-span-2">
        {m.description}
        <input className={input} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      <div className="sm:col-span-2">
        <button type="submit" disabled={saving || !failureType.trim()} className="px-4 py-2 rounded-xl bg-royal text-white text-sm font-semibold hover:bg-royal/90 disabled:opacity-50">
          {m.logFailure}
        </button>
      </div>
    </form>
  );
}
