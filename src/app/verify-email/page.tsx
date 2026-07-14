"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Mail } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";

const CODE_LENGTH = 6;

export default function VerifyEmailPage() {
  const [digits, setDigits] = useState<string[]>(Array(CODE_LENGTH).fill(""));
  const [verified, setVerified] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [cooldown, setCooldown] = useState(30);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const code = digits.join("");

  useEffect(() => {
    if (code.length === CODE_LENGTH && !verified) {
      setVerifying(true);
      const t = setTimeout(() => {
        setVerifying(false);
        setVerified(true);
      }, 1000);
      return () => clearTimeout(t);
    }
  }, [code, verified]);

  function updateDigit(index: number, value: string) {
    const v = value.replace(/[^0-9]/g, "").slice(-1);
    const next = [...digits];
    next[index] = v;
    setDigits(next);
    if (v && index < CODE_LENGTH - 1) {
      inputs.current[index + 1]?.focus();
    }
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  }

  function handlePaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text").replace(/[^0-9]/g, "").slice(0, CODE_LENGTH);
    if (!text) return;
    e.preventDefault();
    const next = Array(CODE_LENGTH).fill("");
    text.split("").forEach((d, i) => (next[i] = d));
    setDigits(next);
    inputs.current[Math.min(text.length, CODE_LENGTH - 1)]?.focus();
  }

  return (
    <AuthLayout
      eyebrow="Almost There"
      title="Verify your email"
      subtitle="We sent a 6-digit code to your inbox. Enter it below to confirm your account."
    >
      {verified ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-lime-dark/30 bg-lime/10 p-6 flex items-start gap-3"
        >
          <CheckCircle2 size={22} className="text-lime-dark shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-ink">Email verified</p>
            <p className="mt-1 text-sm text-gray-600 leading-relaxed">
              Your account is now active. Head to your dashboard to get started.
            </p>
            <a
              href="/login"
              className="mt-4 inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors"
            >
              Continue to Sign In
            </a>
          </div>
        </motion.div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-2.5 rounded-2xl border border-gray-200 bg-mist/40 px-4 py-3">
            <Mail size={16} className="text-gray-400 shrink-0" />
            <p className="text-sm text-gray-500">
              Code sent to <span className="font-medium text-ink">you@company.com</span>
            </p>
          </div>

          <div className="flex justify-between gap-2 sm:gap-3">
            {digits.map((d, i) => (
              <input
                key={i}
                ref={(el) => {
                  inputs.current[i] = el;
                }}
                value={d}
                onChange={(e) => updateDigit(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                onPaste={handlePaste}
                inputMode="numeric"
                maxLength={1}
                disabled={verifying}
                className="w-full aspect-square text-center text-xl font-bold text-ink rounded-2xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all disabled:opacity-50"
              />
            ))}
          </div>

          {verifying && (
            <p className="text-sm text-gray-500 text-center">Verifying…</p>
          )}

          <div className="text-center text-sm text-gray-500">
            {cooldown > 0 ? (
              <span>Resend code in {cooldown}s</span>
            ) : (
              <button
                onClick={() => setCooldown(30)}
                className="font-semibold text-ink hover:text-lime-dark transition-colors"
              >
                Resend code
              </button>
            )}
          </div>
        </div>
      )}
    </AuthLayout>
  );
}
