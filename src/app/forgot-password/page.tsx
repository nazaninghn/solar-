"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Mail, ArrowLeft, CheckCircle2 } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FormField from "@/components/auth/FormField";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 1200);
  }

  return (
    <AuthLayout
      eyebrow="Account Recovery"
      title="Forgot your password?"
      subtitle="Enter the email linked to your account and we'll send you a reset link."
      footer={
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 font-semibold text-ink hover:text-lime-dark transition-colors"
        >
          <ArrowLeft size={15} />
          Back to sign in
        </Link>
      }
    >
      {sent ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-lime-dark/30 bg-lime/10 p-6 flex items-start gap-3"
        >
          <CheckCircle2 size={22} className="text-lime-dark shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-ink">Check your inbox</p>
            <p className="mt-1 text-sm text-gray-600 leading-relaxed">
              We&apos;ve sent a password reset link to <span className="font-medium text-ink">{email || "your email"}</span>.
              It expires in 15 minutes.
            </p>
            <button
              onClick={() => setSent(false)}
              className="mt-3 text-sm font-semibold text-ink hover:text-lime-dark transition-colors"
            >
              Didn&apos;t get it? Resend
            </button>
          </div>
        </motion.div>
      ) : (
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

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors disabled:opacity-60"
          >
            {loading ? "Sending link…" : "Send Reset Link"}
          </button>
        </form>
      )}
    </AuthLayout>
  );
}
