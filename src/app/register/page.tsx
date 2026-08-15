"use client";

import { useState } from "react";
import Link from "next/link";
import { User, Mail, Lock, Building2 } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FormField from "@/components/auth/FormField";
import SocialButtons from "@/components/auth/SocialButtons";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function RegisterPage() {
  const { t } = useLanguage();
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
      eyebrow={t.auth.getStarted}
      title={t.auth.createAccount}
      subtitle={t.auth.createAccountSubtitle}
      footer={
        <>
          {t.auth.haveAccount}{" "}
          <Link href="/login" className="font-semibold text-ink hover:text-lime-dark transition-colors">
            {t.auth.signInLink}
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <FormField
          label={t.auth.fullName}
          icon={User}
          placeholder="Jane Doe"
          autoComplete="name"
          value={name}
          onChange={setName}
        />
        <FormField
          label={t.auth.company}
          icon={Building2}
          placeholder="Acme Industrial GmbH"
          autoComplete="organization"
          value={company}
          onChange={setCompany}
        />
        <FormField
          label={t.auth.workEmail}
          type="email"
          icon={Mail}
          placeholder="you@company.com"
          autoComplete="email"
          value={email}
          onChange={setEmail}
        />
        <FormField
          label={t.auth.password}
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
            {t.auth.agreeTerms}{" "}
            <a href="#" className="font-semibold text-ink hover:text-lime-dark transition-colors">
              {t.auth.termsOfService}
            </a>{" "}
            {t.auth.and}{" "}
            <a href="#" className="font-semibold text-ink hover:text-lime-dark transition-colors">
              {t.auth.privacyPolicy}
            </a>
          </span>
        </label>

        <button
          type="submit"
          disabled={loading || !agree}
          className="w-full py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors disabled:opacity-50"
        >
          {loading ? t.auth.creatingBtn : t.auth.createBtn}
        </button>

        <div className="flex items-center gap-3 py-1">
          <div className="h-px flex-1 bg-gray-200" />
          <span className="text-xs text-gray-400 uppercase tracking-wide">{t.auth.orContinueWith}</span>
          <div className="h-px flex-1 bg-gray-200" />
        </div>

        <SocialButtons />
      </form>
    </AuthLayout>
  );
}
