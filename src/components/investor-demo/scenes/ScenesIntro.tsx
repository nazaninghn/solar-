"use client";

import { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { ArrowDown, Mail, Lock, CheckCircle2, Loader2 } from "lucide-react";

export function Scene1Landing() {
  return (
    <div className="relative min-h-full flex items-center justify-center">
      <Image src="/hero-solar-panel.png" alt="" fill priority className="object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/70 to-ink/40" />

      <div className="relative z-10 text-center px-6 max-w-3xl">
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xs font-semibold text-lime uppercase tracking-widest mb-5"
        >
          SolarFlow · AI Energy Intelligence
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="text-4xl sm:text-6xl font-bold text-white tracking-tight leading-[1.05]"
        >
          AI Energy Intelligence for Industrial Facilities
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-6 text-white/60 text-lg max-w-xl mx-auto"
        >
          One platform to forecast, optimize, and trade every kilowatt-hour your factory touches.
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }} className="mt-9">
          <button className="px-8 py-4 rounded-full bg-lime text-ink text-sm font-semibold hover:bg-lime/90 transition-colors">
            Book a Demo
          </button>
        </motion.div>

        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 1.8 }}
          className="mt-16 flex justify-center text-white/40"
        >
          <ArrowDown size={18} />
        </motion.div>
      </div>
    </div>
  );
}

export function Scene2Login() {
  const [status, setStatus] = useState<"idle" | "loading" | "done">("idle");

  function signIn() {
    if (status !== "idle") return;
    setStatus("loading");
    setTimeout(() => setStatus("done"), 1200);
  }

  return (
    <div className="min-h-full flex items-center justify-center bg-warm-bg px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm rounded-3xl bg-white border border-gray-100 p-8 shadow-xl"
      >
        {status === "done" ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center text-center py-6">
            <CheckCircle2 size={40} className="text-primary-green" />
            <p className="text-lg font-semibold text-ink mt-4">Welcome back, Jane.</p>
            <p className="text-sm text-gray-400 mt-1">Opening your dashboard…</p>
          </motion.div>
        ) : (
          <>
            <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-2">Welcome Back</p>
            <h2 className="text-2xl font-bold text-ink tracking-tight">Sign in to SolarFlow</h2>

            <div className="mt-6 space-y-4">
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <div className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-gray-200 text-sm text-gray-400">jane@acme-industrial.com</div>
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <div className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-gray-200 text-sm text-gray-400">••••••••</div>
              </div>
            </div>

            <button
              onClick={signIn}
              className="w-full mt-6 py-3.5 rounded-full bg-ink text-white text-sm font-semibold hover:bg-black transition-colors inline-flex items-center justify-center gap-2"
            >
              {status === "loading" ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Signing in…
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
}
