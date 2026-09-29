"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, Plus, RefreshCw, Trash2, KeyRound, Copy, Check, Wifi, WifiOff, X } from "lucide-react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useFactory } from "@/lib/factory/FactoryContext";
import { devicesText } from "@/lib/i18n/devices";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const DEVICE_BASE = `${API}/api/v1/devices`;

type Device = {
  id: number;
  factory_id: number;
  name: string;
  device_type: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  connection_type: string;
  is_active: boolean;
  status: string;
  last_seen_at: string | null;
  created_at: string;
};

type CreatedDevice = Device & { device_key: string };

function authHeaders(json = false): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

const STATUS_STYLE: Record<string, string> = {
  online: "bg-primary-green/10 text-primary-green",
  offline: "bg-gray-100 text-gray-400",
  error: "bg-danger/10 text-danger",
  pending: "bg-warning/10 text-warning",
  unknown: "bg-gray-100 text-gray-400",
};

export default function DevicesPanel() {
  const { locale } = useLanguage();
  const d = devicesText[locale];
  const { activeId } = useFactory();
  const factoryBase = `${API}/api/v1/factories/${activeId}/devices`;

  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newKey, setNewKey] = useState<{ name: string; key: string } | null>(null);
  const [testResult, setTestResult] = useState<Record<number, { ok: boolean; latency: number | null }>>({});
  const [testingId, setTestingId] = useState<number | null>(null);

  const [reloadKey, setReloadKey] = useState(0);
  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch(`${API}/api/v1/factories/${activeId}/devices`, { headers: authHeaders() });
        if (!res.ok) throw new Error(`devices ${res.status}`);
        const data: Device[] = await res.json();
        if (cancelled) return;
        setDevices(data);
        setError(false);
      } catch (err) {
        console.error("Devices load failed", err);
        if (!cancelled) setError(true);
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadKey, activeId]);

  async function testConnection(id: number) {
    setTestingId(id);
    try {
      const res = await fetch(`${DEVICE_BASE}/${id}/test-connection`, { method: "POST", headers: authHeaders() });
      if (res.ok) {
        const body = await res.json();
        setTestResult((prev) => ({ ...prev, [id]: { ok: body.success, latency: body.latency_ms ?? null } }));
      }
    } catch (err) {
      console.error("Test connection failed", err);
    }
    setTestingId(null);
  }

  async function regenerate(device: Device) {
    if (!window.confirm(d.regenerateWarn)) return;
    try {
      const res = await fetch(`${DEVICE_BASE}/${device.id}/regenerate-key`, { method: "POST", headers: authHeaders() });
      if (res.ok) {
        const body = await res.json();
        setNewKey({ name: device.name, key: body.device_key });
      }
    } catch (err) {
      console.error("Regenerate key failed", err);
    }
  }

  async function remove(id: number) {
    if (!window.confirm(d.confirmRemove)) return;
    try {
      const res = await fetch(`${DEVICE_BASE}/${id}`, { method: "DELETE", headers: authHeaders() });
      if (res.ok || res.status === 204) reload();
    } catch (err) {
      console.error("Remove device failed", err);
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-40"><div className="animate-spin w-7 h-7 border-3 border-lime border-t-transparent rounded-full" /></div>;
  }

  const lastSeen = (ts: string | null) =>
    ts ? new Date(ts).toLocaleString(d.dateLocale) : d.never;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <div className="bg-white rounded-2xl p-6 border border-gray-100">
        <div className="flex items-start justify-between gap-3 mb-1">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-royal" />
            <h2 className="text-base font-semibold text-ink">{d.title}</h2>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black transition-colors"
          >
            {showForm ? <X size={16} /> : <Plus size={16} />}
            {showForm ? d.cancel : d.add}
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-5">{d.subtitle}</p>

        {error && (
          <div className="rounded-xl border border-danger/30 bg-danger/5 p-4 text-sm text-danger mb-4">{d.loadError}</div>
        )}

        {showForm && (
          <AddDeviceForm
            factoryBase={factoryBase}
            onCancel={() => setShowForm(false)}
            onCreated={(created) => {
              setShowForm(false);
              setNewKey({ name: created.name, key: created.device_key });
              reload();
            }}
          />
        )}

        {devices.length === 0 && !showForm ? (
          <p className="text-sm text-gray-400 py-4">{d.empty}</p>
        ) : devices.length > 0 ? (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400">
                  <th className="py-2 pr-3 font-medium">{d.name}</th>
                  <th className="py-2 pr-3 font-medium">{d.type}</th>
                  <th className="py-2 pr-3 font-medium">{d.status}</th>
                  <th className="py-2 pr-3 font-medium">{d.lastSeen}</th>
                  <th className="py-2 font-medium text-right">{d.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {devices.map((device) => {
                  const status = device.status?.toLowerCase() ?? "unknown";
                  const result = testResult[device.id];
                  return (
                    <tr key={device.id}>
                      <td className="py-3 pr-3">
                        <p className="font-semibold text-ink">{device.name}</p>
                        <p className="text-xs text-gray-400">
                          {[device.manufacturer, device.model].filter(Boolean).join(" ") || device.serial_number || device.connection_type}
                        </p>
                      </td>
                      <td className="py-3 pr-3 text-gray-600">{d.deviceTypes[device.device_type] ?? device.device_type}</td>
                      <td className="py-3 pr-3">
                        <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLE[status] ?? STATUS_STYLE.unknown}`}>
                          {d.statuses[status] ?? device.status}
                        </span>
                        {result && (
                          <span className={`ml-2 inline-flex items-center gap-1 text-xs ${result.ok ? "text-primary-green" : "text-danger"}`}>
                            {result.ok ? <Wifi size={12} /> : <WifiOff size={12} />}
                            {result.ok ? d.testOk : d.testFail}
                            {result.ok && result.latency != null ? ` · ${Math.round(result.latency)}ms` : ""}
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-3 text-gray-500 whitespace-nowrap">{lastSeen(device.last_seen_at)}</td>
                      <td className="py-3">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => testConnection(device.id)}
                            disabled={testingId === device.id}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-ink border border-gray-200 hover:bg-gray-50 disabled:opacity-50"
                          >
                            <RefreshCw size={13} className={testingId === device.id ? "animate-spin" : ""} />
                            {testingId === device.id ? d.testing : d.testConnection}
                          </button>
                          <button
                            onClick={() => regenerate(device)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-ink border border-gray-200 hover:bg-gray-50"
                          >
                            <KeyRound size={13} />
                            {d.regenerate}
                          </button>
                          <button
                            onClick={() => remove(device.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-danger border border-danger/20 hover:bg-danger/5"
                          >
                            <Trash2 size={13} />
                            {d.remove}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {newKey && <DeviceKeyModal name={newKey.name} deviceKey={newKey.key} onClose={() => setNewKey(null)} />}
    </motion.div>
  );
}

function AddDeviceForm({
  factoryBase,
  onCreated,
  onCancel,
}: {
  factoryBase: string;
  onCreated: (device: CreatedDevice) => void;
  onCancel: () => void;
}) {
  const { locale } = useLanguage();
  const d = devicesText[locale];

  const [name, setName] = useState("");
  const [deviceType, setDeviceType] = useState("inverter");
  const [manufacturer, setManufacturer] = useState("");
  const [model, setModel] = useState("");
  const [serial, setSerial] = useState("");
  const [connectionType, setConnectionType] = useState("api");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setFormError(null);
    try {
      const res = await fetch(factoryBase, {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          name: name.trim(),
          device_type: deviceType,
          manufacturer: manufacturer.trim() || null,
          model: model.trim() || null,
          serial_number: serial.trim() || null,
          connection_type: connectionType,
        }),
      });
      if (res.ok) {
        onCreated(await res.json());
      } else {
        let detail = `HTTP ${res.status}`;
        try {
          const body = await res.json();
          if (typeof body.detail === "string") detail = body.detail;
        } catch {
          // keep the HTTP status fallback
        }
        setFormError(detail);
      }
    } catch (err) {
      console.error("Create device failed", err);
      setFormError(String(err));
    }
    setSaving(false);
  }

  const input = "w-full rounded-xl border border-gray-200 px-3 py-2 text-sm text-ink focus:outline-none focus:border-royal";

  return (
    <form onSubmit={submit} className="rounded-xl bg-gray-50 border border-gray-100 p-4 mb-5 space-y-3">
      <h3 className="text-sm font-semibold text-ink">{d.formTitle}</h3>
      <div className="grid sm:grid-cols-2 gap-3">
        <label className="text-xs text-gray-500">
          {d.fieldName}
          <input className={input} value={name} maxLength={80} placeholder={d.fieldNamePlaceholder} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="text-xs text-gray-500">
          {d.fieldType}
          <select className={input} value={deviceType} onChange={(e) => setDeviceType(e.target.value)}>
            {Object.entries(d.deviceTypes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <label className="text-xs text-gray-500">
          {d.fieldConnection}
          <select className={input} value={connectionType} onChange={(e) => setConnectionType(e.target.value)}>
            {Object.entries(d.connectionTypes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <label className="text-xs text-gray-500">
          {d.fieldManufacturer} <span className="text-gray-300">({d.optional})</span>
          <input className={input} value={manufacturer} maxLength={80} onChange={(e) => setManufacturer(e.target.value)} />
        </label>
        <label className="text-xs text-gray-500">
          {d.fieldModel} <span className="text-gray-300">({d.optional})</span>
          <input className={input} value={model} maxLength={80} onChange={(e) => setModel(e.target.value)} />
        </label>
        <label className="text-xs text-gray-500">
          {d.fieldSerial} <span className="text-gray-300">({d.optional})</span>
          <input className={input} value={serial} maxLength={80} onChange={(e) => setSerial(e.target.value)} />
        </label>
      </div>
      {formError && <p className="text-xs text-danger">{formError}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={saving || !name.trim()} className="px-4 py-2 rounded-xl bg-royal text-white text-sm font-semibold hover:bg-royal/90 disabled:opacity-50">
          {saving ? d.adding : d.add}
        </button>
        <button type="button" onClick={onCancel} className="px-4 py-2 rounded-xl border border-gray-200 text-sm font-semibold text-ink hover:bg-gray-50">
          {d.cancel}
        </button>
      </div>
    </form>
  );
}

function DeviceKeyModal({ name, deviceKey, onClose }: { name: string; deviceKey: string; onClose: () => void }) {
  const { locale } = useLanguage();
  const d = devicesText[locale];
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(deviceKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed", err);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl"
      >
        <div className="flex items-center gap-2 mb-2">
          <KeyRound size={18} className="text-royal" />
          <h3 className="text-base font-semibold text-ink">{d.keyTitle}</h3>
        </div>
        <p className="text-xs text-gray-500 mb-1">{name}</p>
        <p className="text-sm text-gray-600 mb-4">{d.keyHint}</p>
        <div className="flex items-center gap-2 rounded-xl bg-gray-50 border border-gray-200 p-3 mb-4">
          <code className="flex-1 text-xs text-ink break-all font-mono">{deviceKey}</code>
          <button onClick={copy} className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-ink border border-gray-200 bg-white hover:bg-gray-50 shrink-0">
            {copied ? <Check size={13} className="text-primary-green" /> : <Copy size={13} />}
            {copied ? d.copied : d.copy}
          </button>
        </div>
        <button onClick={onClose} className="w-full px-4 py-2.5 rounded-xl bg-ink text-white text-sm font-semibold hover:bg-black transition-colors">
          {d.keyDone}
        </button>
      </motion.div>
    </div>
  );
}
