"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Lock, CheckCircle2 } from "lucide-react";
import AuthLayout from "@/components/auth/AuthLayout";
import FormField from "@/components/auth/FormField";

function getStrength(pw: string) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

const labels = ["Too weak", "Weak", "Fair", "Good", "Strong"];
const colors = ["bg-danger", "bg-energy-orange", "bg-lime-dark", "bg-lime-dark", "bg-primary-green"];

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const strength = useMemo(() => getStrength(password), [password]);
  const mismatch = confirm.length > 0 && confirm !== password;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mismatch || password.length === 0) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setDone(true);
    }, 1200);
  }

  return (
    <AuthLayout
      eyebrow="Account Recovery"
      title="Set a new password"
      subtitle="Choose a strong password you haven't used before."
    >
      {done ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-lime-dark/30 bg-lime/10 p-6 flex items-start gap-3"
        >
          <CheckCircle2 size={22} className="text-lime-dark shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-ink">Password updated</p>
            <p className="mt-1 text-sm text-gray-600 leading-relaxed">
              Your password has been reset successfully. You can now sign in with your new password.
            </p>
            <a
              href="/login"
              className="mt-4 inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors"
            >
              Back to Sign In
            </a>
          </div>
        </motion.div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <FormField
              label="New Password"
              type="password"
              icon={Lock}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              value={password}
              onChange={setPassword}
            />
            {password.length > 0 && (
              <div className="mt-2.5">
                <div className="flex gap-1.5">
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        i < strength ? colors[strength] : "bg-gray-200"
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-1.5 text-xs text-gray-500">{labels[strength]}</p>
              </div>
            )}
          </div>

          <div>
            <FormField
              label="Confirm New Password"
              type="password"
              icon={Lock}
              placeholder="Re-enter your password"
              autoComplete="new-password"
              value={confirm}
              onChange={setConfirm}
            />
            {mismatch && (
              <p className="mt-1.5 text-xs text-danger">Passwords do not match</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !password || mismatch}
            className="w-full py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors disabled:opacity-50"
          >
            {loading ? "Resetting…" : "Reset Password"}
          </button>
        </form>
      )}
    </AuthLayout>
  );
}
