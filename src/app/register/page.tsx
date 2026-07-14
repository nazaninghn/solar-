"use client";

import { useState } from "react";
import Link from "next/link";
import { User, Mail, Lock, Building2 } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FormField from "@/components/auth/FormField";
import SocialButtons from "@/components/auth/SocialButtons";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree] = useState(false);
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => setLoading(false), 1200);
  }

  return (
    <AuthLayout
      eyebrow="Get Started"
      title="Create your account"
      subtitle="Start optimizing your facility's energy in minutes — free 14-day trial."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-ink hover:text-lime-dark transition-colors">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          label="Full Name"
          icon={User}
          placeholder="Jane Doe"
          autoComplete="name"
          value={name}
          onChange={setName}
        />
        <FormField
          label="Company"
          icon={Building2}
          placeholder="Acme Industrial GmbH"
          autoComplete="organization"
          value={company}
          onChange={setCompany}
        />
        <FormField
          label="Work Email"
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
          placeholder="At least 8 characters"
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
        />

        <label className="flex items-start gap-2.5 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={agree}
            onChange={(e) => setAgree(e.target.checked)}
            className="w-4 h-4 mt-0.5 rounded accent-[#ADC825] cursor-pointer"
          />
          <span className="text-sm text-gray-600">
            I agree to the{" "}
            <a href="#" className="font-semibold text-ink hover:text-lime-dark transition-colors">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="font-semibold text-ink hover:text-lime-dark transition-colors">
              Privacy Policy
            </a>
          </span>
        </label>

        <button
          type="submit"
          disabled={loading || !agree}
          className="w-full py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors disabled:opacity-50"
        >
          {loading ? "Creating account…" : "Create Account"}
        </button>

        <div className="flex items-center gap-3 py-1">
          <div className="h-px flex-1 bg-gray-200" />
          <span className="text-xs text-gray-400 uppercase tracking-wide">or continue with</span>
          <div className="h-px flex-1 bg-gray-200" />
        </div>

        <SocialButtons />
      </form>
    </AuthLayout>
  );
}
