"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";

export default function AuthLayout({
  eyebrow,
  title,
  subtitle,
  children,
  footer,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">
      {/* Left: form */}
      <div className="flex flex-col min-h-screen px-6 sm:px-10 lg:px-16 xl:px-20 py-10">
        <Link href="/" className="flex items-center gap-2.5 w-fit">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-green to-secondary-green flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
            </svg>
          </div>
          <span className="text-lg font-bold text-ink">
            Solar<span className="text-lime-dark">Flow</span>
          </span>
        </Link>

        <div className="flex-1 flex items-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md mx-auto py-10"
          >
            <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">
              {eyebrow}
            </p>
            <h1 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight">
              {title}
            </h1>
            <p className="mt-3 text-sm text-gray-500 leading-relaxed">
              {subtitle}
            </p>

            <div className="mt-8">{children}</div>

            {footer && (
              <div className="mt-8 text-center text-sm text-gray-500">{footer}</div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Right: illustration */}
      <div className="hidden lg:block relative overflow-hidden bg-ink">
        <div className="absolute inset-0">
          <Image
            src="/auth-bg.png"
            alt="Solar panel installed among green foliage"
            fill
            priority
            className="object-cover"
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/40 to-ink/50" />
        <div className="absolute inset-0 bg-gradient-to-br from-royal/30 via-transparent to-transparent mix-blend-color" />

        {/* Headline overlay */}
        <div className="absolute top-14 left-14 right-14">
          <p className="text-xs font-semibold text-lime uppercase tracking-widest mb-3">
            Enterprise Energy Intelligence
          </p>
          <h2 className="text-3xl xl:text-4xl font-bold text-white leading-tight tracking-tight max-w-md">
            Powering industrial facilities with AI-driven energy decisions.
          </h2>
        </div>

        {/* Floating stat chips */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="absolute bottom-16 left-14 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl px-5 py-4"
        >
          <p className="text-[11px] text-white/60">Generation Today</p>
          <p className="text-xl font-bold text-white">4.2 MWh</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.5 }}
          className="absolute bottom-16 right-14 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl px-5 py-4"
        >
          <p className="text-[11px] text-white/60">Uptime</p>
          <p className="text-xl font-bold text-white">99.9%</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="absolute top-1/2 right-14 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl px-5 py-4 flex items-center gap-3"
        >
          <div className="w-9 h-9 rounded-full bg-lime/20 flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D5F332" strokeWidth="2">
              <polyline points="23,6 13.5,15.5 8.5,10.5 1,18" />
              <polyline points="17,6 23,6 23,12" />
            </svg>
          </div>
          <div>
            <p className="text-[11px] text-white/60">Cost Reduction</p>
            <p className="text-sm font-bold text-white">40% avg.</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
