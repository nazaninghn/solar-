"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { FACTORY_ID as FALLBACK_FACTORY_ID } from "@/lib/factory";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const SELECTED_KEY = "solarflow-factory-id";

export type Factory = {
  id: number;
  organization_id: number;
  name: string;
  address: string | null;
  industry: string | null;
  currency: string;
  solar_capacity_kw: number | null;
  battery_capacity_kwh: number | null;
  solar_installation_cost: number | null;
  created_at: string;
  updated_at: string;
};

interface FactoryContextValue {
  factories: Factory[];
  activeId: number;
  active: Factory | null;
  loading: boolean;
  error: boolean;
  setActiveId: (id: number) => void;
  reload: () => void;
}

const FactoryContext = createContext<FactoryContextValue | null>(null);

function token(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
}

function storedId(): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SELECTED_KEY);
  const n = raw ? Number(raw) : NaN;
  return Number.isFinite(n) ? n : null;
}

export function FactoryProvider({ children }: { children: React.ReactNode }) {
  const [factories, setFactories] = useState<Factory[]>([]);
  const [activeId, setActiveIdState] = useState<number>(FALLBACK_FACTORY_ID);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch(`${API}/api/v1/factories`, {
          headers: token() ? { Authorization: `Bearer ${token()}` } : {},
        });
        if (!res.ok) throw new Error(`factories ${res.status}`);
        const data: Factory[] = await res.json();
        if (cancelled) return;
        setFactories(data);
        setError(false);

        // Pick: stored selection if it's still accessible, else first factory,
        // else keep the env fallback so single-tenant dev keeps working.
        const stored = storedId();
        const ids = data.map((f) => f.id);
        if (stored && ids.includes(stored)) {
          setActiveIdState(stored);
        } else if (data.length > 0) {
          setActiveIdState(data[0].id);
        }
      } catch (err) {
        console.error("Factories load failed", err);
        if (!cancelled) setError(true);
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  const setActiveId = useCallback((id: number) => {
    setActiveIdState(id);
    if (typeof window !== "undefined") window.localStorage.setItem(SELECTED_KEY, String(id));
  }, []);

  const active = factories.find((f) => f.id === activeId) ?? null;

  return (
    <FactoryContext.Provider value={{ factories, activeId, active, loading, error, setActiveId, reload }}>
      {children}
    </FactoryContext.Provider>
  );
}

export function useFactory() {
  const ctx = useContext(FactoryContext);
  if (!ctx) throw new Error("useFactory must be used within a FactoryProvider");
  return ctx;
}
