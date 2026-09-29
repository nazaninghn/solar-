"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export type Organization = { id: number; name: string };

export type CurrentUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  organization: Organization;
};

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  error: boolean;
  reload: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function token(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch(`${API}/api/v1/auth/me`, {
          headers: token() ? { Authorization: `Bearer ${token()}` } : {},
        });
        if (!res.ok) throw new Error(`me ${res.status}`);
        const data: CurrentUser = await res.json();
        if (cancelled) return;
        setUser(data);
        setError(false);
      } catch (err) {
        console.error("Auth load failed", err);
        if (!cancelled) {
          setUser(null);
          setError(true);
        }
      }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  const logout = useCallback(async () => {
    const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    try {
      if (refresh) {
        await fetch(`${API}/api/v1/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
      }
    } catch (err) {
      console.error("Logout request failed", err);
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, error, reload, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

/** Initials from a full name, e.g. "Jane Doe" -> "JD". Falls back to "?" */
export function initials(name: string | undefined | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
