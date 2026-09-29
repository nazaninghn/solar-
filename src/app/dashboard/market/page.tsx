"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip, Legend,
} from "recharts";
import { TrendingUp, RefreshCw, Clock, Gavel, Info, FlaskConical } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useFactory } from "@/lib/factory/FactoryContext";
import { marketText } from "@/lib/i18n/market";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type Status = {
  epias_configured: boolean; price_rows: number; last_price_at: string | null;
  next_delivery_date: string;
  model: { version: string; trained_through: string; backtest: Backtest | null } | null;
};
type Backtest = {
  test_weeks: number; test_hours: number;
  models: Record<string, { mae: number; rmse: number; rel_mae_pct: number }>;
  interval: { p10_p90_coverage_pct: number };
  skill_vs_best_naive_pct: number;
};
type ForecastPoint = { timestamp: string; p10_try_mwh: number; p50_try_mwh: number; p90_try_mwh: number };
type Forecast = {
  delivery_date: string; model_version: string | null; points: ForecastPoint[];
  actual: { timestamp: string; ptf_try_mwh: number | null }[];
};
type OfferRow = {
  id: number; timestamp: string; tier: number; action: string; quantity_mwh: number;
  price_try_mwh: number | null; expected_ptf_try_mwh: number | null; expected_revenue_try: number | null;
};
type Offer = {
  delivery_date: string; gate_closure: string; status: string | null; total_quantity_mwh: number;
  expected_revenue_try: number; revenue_p10_try: number; revenue_p90_try: number;
  rows: OfferRow[]; notes: string[];
};

function headers(json = false): Record<string, string> {
  const h: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (json) h["Content-Type"] = "application/json";
  return h;
}

async function detail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`;
  } catch {
    return `HTTP ${res.status}`;
  }
}

const tl = (v: number | null | undefined, digits = 0) =>
  v == null ? "—" : v.toLocaleString("tr-TR", { maximumFractionDigits: digits, minimumFractionDigits: digits });

export default function MarketPage() {
  const { locale } = useLanguage();
  const m = marketText[locale];
  const { activeId } = useFactory();

  const [status, setStatus] = useState<Status | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [offer, setOffer] = useState<Offer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"sync" | "offer" | null>(null);
  const [mode, setMode] = useState("GOP_BID");
  const [minPrice, setMinPrice] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const s = await fetch(`${API}/api/v1/market/status`, { headers: headers() });
        if (!s.ok) throw new Error(await detail(s));
        const statusData: Status = await s.json();
        const day = statusData.next_delivery_date;
        const [f, o] = await Promise.all([
          statusData.price_rows > 0
            ? fetch(`${API}/api/v1/market/ptf/forecast?delivery_date=${day}`, { headers: headers() })
            : Promise.resolve(null),
          fetch(`${API}/api/v1/factories/${activeId}/sell-offers?delivery_date=${day}`, { headers: headers() }),
        ]);
        const forecastData = f && f.ok ? await f.json() : null;
        const offerData = o.ok ? await o.json() : null;
        if (cancelled) return;
        setStatus(statusData);
        setForecast(forecastData);
        setOffer(offerData);
        setError(f && !f.ok ? await detail(f) : null);
      } catch (err) {
        console.error("Market load failed", err);
        if (!cancelled) setError(m.loadError);
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadKey, m.loadError, activeId]);

  async function sync() {
    setBusy("sync");
    const res = await fetch(`${API}/api/v1/market/sync`, {
      method: "POST", headers: headers(true), body: JSON.stringify({ days: 30 }),
    }).catch(() => null);
    if (res && !res.ok) setError(await detail(res));
    setBusy(null);
    reload();
  }

  async function generate() {
    if (!status) return;
    setBusy("offer");
    const res = await fetch(`${API}/api/v1/factories/${activeId}/sell-offers`, {
      method: "POST", headers: headers(true),
      body: JSON.stringify({ delivery_date: status.next_delivery_date, mode, min_price_try_mwh: minPrice }),
    }).catch(() => null);
    if (res && res.ok) {
      setOffer(await res.json());
      setError(null);
    } else if (res) {
      setError(await detail(res));
    }
    setBusy(null);
  }

  async function markSubmitted() {
    if (!status) return;
    const res = await fetch(
      `${API}/api/v1/factories/${activeId}/sell-offers/mark-submitted?delivery_date=${status.next_delivery_date}`,
      { method: "POST", headers: headers() },
    ).catch(() => null);
    if (res && res.ok) setOffer(await res.json());
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  const hourLabel = (ts: string) =>
    new Date(ts).toLocaleTimeString(m.dateLocale, { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Istanbul" });
  const actualByTs = new Map((forecast?.actual ?? []).map((a) => [a.timestamp, a.ptf_try_mwh]));
  const chart = (forecast?.points ?? []).map((p) => ({
    hour: hourLabel(p.timestamp),
    band: [p.p10_try_mwh, p.p90_try_mwh],
    p50: p.p50_try_mwh,
    actual: actualByTs.get(p.timestamp) ?? null,
  }));
  const gate = offer ? new Date(offer.gate_closure).getTime() : null;
  const minutesLeft = gate ? Math.round((gate - now) / 60000) : null;
  const backtest = status?.model?.backtest ?? null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">{m.title}</h1>
          <p className="text-sm text-gray-500 mt-1">{m.subtitle}</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
            {status && <span>{m.deliveryDate}: <b className="text-ink">{status.next_delivery_date}</b></span>}
            {minutesLeft != null && (
              <span className="inline-flex items-center gap-1">
                <Clock size={12} />
                {m.gateClosure} 12:30 ·{" "}
                <b className={minutesLeft <= 0 ? "text-danger" : minutesLeft < 90 ? "text-energy-orange" : "text-ink"}>
                  {minutesLeft <= 0 ? m.closed : `${Math.floor(minutesLeft / 60)}h ${minutesLeft % 60}m ${m.left}`}
                </b>
              </span>
            )}
            {status?.last_price_at && (
              <span>{m.dataThrough}: {new Date(status.last_price_at).toLocaleString(m.dateLocale, { timeZone: "Europe/Istanbul" })}</span>
            )}
          </div>
        </div>
        <button
          onClick={sync}
          disabled={busy !== null || !status?.epias_configured}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-ink/90 disabled:opacity-50"
        >
          <RefreshCw size={16} className={busy === "sync" ? "animate-spin" : ""} />
          {busy === "sync" ? m.syncing : m.sync}
        </button>
      </div>

      {status && !status.epias_configured && (
        <div className="rounded-2xl border border-energy-orange/40 bg-energy-orange/10 p-4 text-sm text-ink flex gap-2">
          <Info size={16} className="mt-0.5 shrink-0" />{m.notConfigured}
        </div>
      )}
      {status?.epias_configured && status.price_rows === 0 && (
        <div className="rounded-2xl border border-royal/20 bg-royal/5 p-4 text-sm text-ink flex gap-2">
          <Info size={16} className="mt-0.5 shrink-0" />{m.noData}
        </div>
      )}
      {error && <div className="rounded-2xl border border-danger/30 bg-danger/5 p-4 text-sm text-danger">{error}</div>}

      {/* Forecast chart */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl p-6 border border-gray-100">
        <div className="flex flex-wrap items-baseline justify-between gap-2 mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp size={18} className="text-royal" />
            <h3 className="text-sm font-semibold text-ink">{m.forecast}</h3>
            <span className="text-xs text-gray-400">{m.forecastHint}</span>
          </div>
          <span className="text-xs text-gray-500">
            {m.model}: {status?.model ? status.model.version : m.baselineModel}
          </span>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={50} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
                formatter={(v: unknown) => (Array.isArray(v) ? `${tl(v[0])} – ${tl(v[1])}` : tl(Number(v)))}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area dataKey="band" name={m.band} stroke="none" fill="#305293" fillOpacity={0.15} />
              <Line dataKey="p50" name={m.p50} stroke="#305293" strokeWidth={2.5} dot={false} />
              <Line dataKey="actual" name={m.actual} stroke="#3CB54A" strokeWidth={2} dot={{ r: 2 }} connectNulls={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Offer */}
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-5">
          <div className="flex items-center gap-2">
            <Gavel size={18} className="text-royal" />
            <h3 className="text-sm font-semibold text-ink">{m.offer}</h3>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-xs text-gray-500">
              {m.mode}
              <select value={mode} onChange={(e) => setMode(e.target.value)} className="block mt-1 rounded-xl border border-gray-200 px-3 py-2 text-sm text-ink">
                {Object.entries(m.modes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            {mode === "GOP_BID" && (
              <label className="text-xs text-gray-500">
                {m.minPrice}
                <input type="number" min={0} value={minPrice} onChange={(e) => setMinPrice(Math.max(0, Number(e.target.value)))}
                  className="block mt-1 w-36 rounded-xl border border-gray-200 px-3 py-2 text-sm text-ink" />
              </label>
            )}
            <button onClick={generate} disabled={busy !== null || offer?.status === "SUBMITTED" || !forecast}
              className="px-4 py-2 rounded-xl bg-royal text-white text-sm font-semibold hover:bg-royal/90 disabled:opacity-50">
              {busy === "offer" ? m.generating : m.generate}
            </button>
            {offer?.status === "DRAFT" && (
              <button onClick={markSubmitted} className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-semibold text-ink hover:bg-gray-50">
                {m.markSubmitted}
              </button>
            )}
          </div>
        </div>

        {offer && offer.rows.length > 0 ? (
          <>
            <div className="grid sm:grid-cols-3 gap-4 mb-5">
              <div className="rounded-xl bg-gray-50 p-4">
                <p className="text-xs text-gray-400">{m.totalQty}</p>
                <p className="text-xl font-bold text-ink">{tl(offer.total_quantity_mwh, 1)} MWh</p>
              </div>
              <div className="rounded-xl bg-gray-50 p-4">
                <p className="text-xs text-gray-400">{m.expectedRevenue}</p>
                <p className="text-xl font-bold text-primary-green">₺{tl(offer.expected_revenue_try)}</p>
              </div>
              <div className="rounded-xl bg-gray-50 p-4">
                <p className="text-xs text-gray-400">{m.range}</p>
                <p className="text-xl font-bold text-ink">₺{tl(offer.revenue_p10_try)} – ₺{tl(offer.revenue_p90_try)}</p>
              </div>
            </div>
            {offer.status === "SUBMITTED" && <p className="text-xs text-primary-green mb-3">{m.submittedNote}</p>}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-400">
                    <th className="py-2 pr-3 font-medium">{m.hour}</th>
                    <th className="py-2 pr-3 font-medium">{m.action}</th>
                    <th className="py-2 pr-3 font-medium text-right">{m.quantity}</th>
                    <th className="py-2 pr-3 font-medium text-right">{m.bidPrice}</th>
                    <th className="py-2 pr-3 font-medium text-right">{m.expectedPtf}</th>
                    <th className="py-2 font-medium text-right">{m.revenue}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {offer.rows.map((r) => (
                    <tr key={r.id}>
                      <td className="py-2 pr-3 text-ink">{hourLabel(r.timestamp)}</td>
                      <td className="py-2 pr-3 text-gray-600">{m.actions[r.action] ?? r.action}</td>
                      <td className="py-2 pr-3 text-right font-semibold text-ink">{tl(r.quantity_mwh, r.quantity_mwh < 1 ? 3 : 1)}</td>
                      <td className="py-2 pr-3 text-right text-gray-600">{r.price_try_mwh == null ? "—" : tl(r.price_try_mwh, 2)}</td>
                      <td className="py-2 pr-3 text-right text-gray-600">{tl(r.expected_ptf_try_mwh)}</td>
                      <td className="py-2 text-right text-ink">₺{tl(r.expected_revenue_try)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {offer.notes.length > 0 && (
              <ul className="mt-4 space-y-1 text-xs text-gray-500 list-disc pl-4">
                {offer.notes.map((n) => <li key={n}>{n}</li>)}
              </ul>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-400">{m.noOffer}</p>
        )}
        <p className="text-xs text-gray-400 mt-5 flex gap-1.5"><Info size={13} className="mt-0.5 shrink-0" />{m.disclaimer}</p>
      </div>

      {/* Backtest */}
      {backtest && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <FlaskConical size={18} className="text-royal" />
            <h3 className="text-sm font-semibold text-ink">{m.backtest}</h3>
            <span className="text-xs text-gray-400">{backtest.test_weeks} × 7 × 24h</span>
          </div>
          <table className="w-full text-sm max-w-2xl">
            <thead>
              <tr className="text-left text-xs text-gray-400">
                <th className="py-2 pr-3 font-medium">{m.method}</th>
                <th className="py-2 pr-3 font-medium text-right">{m.mae} (TL/MWh)</th>
                <th className="py-2 font-medium text-right">{m.relMae}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {Object.entries(backtest.models).map(([k, v]) => (
                <tr key={k} className={k === "xgboost_p50" ? "font-semibold" : ""}>
                  <td className="py-2 pr-3 text-ink">{m.methods[k] ?? k}</td>
                  <td className="py-2 pr-3 text-right">{tl(v.mae, 1)}</td>
                  <td className="py-2 text-right">{tl(v.rel_mae_pct, 1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex flex-wrap gap-6 mt-4 text-xs text-gray-500">
            <span>{m.skill}: <b className={backtest.skill_vs_best_naive_pct > 0 ? "text-primary-green" : "text-danger"}>{tl(backtest.skill_vs_best_naive_pct, 1)}%</b></span>
            <span>{m.coverage}: <b className="text-ink">{tl(backtest.interval.p10_p90_coverage_pct, 1)}%</b> (target 80%)</span>
          </div>
        </div>
      )}
    </div>
  );
}
