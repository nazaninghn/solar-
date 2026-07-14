"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail, Lock } from "lucide-react";
import { useRouter } from "next/navigation";
import AuthLayout from "@/components/auth/AuthLayout";
import FormField from "@/components/auth/FormField";
import SocialButtons from "@/components/auth/SocialButtons";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    // بدون بک‌اند: بعد از 1 ثانیه ریدایرکت به داشبورد
    setTimeout(() => {
      router.push("/dashboard");
    }, 1000);
  }

  return (
    <AuthLayout
      eyebrow="Welcome Back"
      title="Sign in to SolarFlow"
      subtitle="Access your energy dashboard, forecasts, and savings reports."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-semibold text-ink hover:text-lime-dark transition-colors">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          label="Email"
          type="email"
          icon={Mail}
          placeholder="you@company.com"
          autoComplete="email"
          value={email}
          onChange={setEmail}
        />
        <FormField
          label="Password"
          type="password"
          icon={Lock}
          placeholder="••••••••"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="w-4 h-4 rounded accent-[#ADC825] cursor-pointer"
            />
            <span className="text-sm text-gray-600">Remember me</span>
          </label>
          <Link
            href="/forgot-password"
            className="text-sm font-semibold text-ink hover:text-lime-dark transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors disabled:opacity-60"
        >
          {loading ? "Signing in…" : "Sign In"}
        </button>

        <div className="flex items-center gap-3 py-1">
          <div className="h-px flex-1 bg-gray-200" />
          <span className="text-xs text-gray-400 uppercase tracking-wide">or continue with</span>
          <div className="h-px flex-1 bg-gray-200" />
        </div>

        <SocialButtons />

        <a
          href="#cta"
          className="flex items-center justify-center w-full py-3.5 rounded-full border border-lime-dark/40 bg-lime/10 text-sm font-semibold text-ink hover:bg-lime/20 transition-colors"
        >
          Book a Demo Instead
        </a>
      </form>
    </AuthLayout>
  );
}
