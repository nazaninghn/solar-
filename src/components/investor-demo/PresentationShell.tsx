"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Play, Pause, X } from "lucide-react";
import { scenes } from "./data";

export default function PresentationShell({
  renderScene,
}: {
  renderScene: (id: (typeof scenes)[number]["id"], active: boolean) => React.ReactNode;
}) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [direction, setDirection] = useState(1);

  const goTo = (i: number) => {
    setDirection(i > index ? 1 : -1);
    setIndex(Math.max(0, Math.min(scenes.length - 1, i)));
  };
  const next = () => goTo(index + 1);
  const prev = () => goTo(index - 1);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [index]);

  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setIndex((i) => {
        if (i >= scenes.length - 1) {
          setPlaying(false);
          return i;
        }
        setDirection(1);
        return i + 1;
      });
    }, 6000);
    return () => clearInterval(t);
  }, [playing]);

  return (
    <div className="fixed inset-0 bg-ink overflow-hidden flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 shrink-0 z-20">
        <Link href="/" className="flex items-center gap-2 text-white/50 hover:text-white transition-colors text-sm">
          <X size={16} />
          Exit
        </Link>
        <div className="flex items-center gap-3 text-xs text-white/40">
          <span className="font-mono">{String(index + 1).padStart(2, "0")}</span>
          <span className="text-white font-semibold">{scenes[index].title}</span>
          <span className="font-mono">/ {String(scenes.length).padStart(2, "0")}</span>
        </div>
        <button
          onClick={() => setPlaying((p) => !p)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/10 text-white text-xs font-semibold hover:bg-white/15 transition-colors"
        >
          {playing ? <Pause size={12} /> : <Play size={12} />}
          {playing ? "Pause" : "Play"}
        </button>
      </div>

      {/* Scene */}
      <div className="relative flex-1 min-h-0">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={scenes[index].id}
            custom={direction}
            initial={{ opacity: 0, x: direction * 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -direction * 40 }}
            transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
            className="absolute inset-0 overflow-y-auto"
          >
            {renderScene(scenes[index].id, true)}
          </motion.div>
        </AnimatePresence>

        {/* Prev / Next edge controls */}
        {index > 0 && (
          <button
            onClick={prev}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/10 backdrop-blur text-white flex items-center justify-center hover:bg-white/20 transition-colors"
            aria-label="Previous scene"
          >
            <ChevronLeft size={18} />
          </button>
        )}
        {index < scenes.length - 1 && (
          <button
            onClick={next}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-lime text-ink flex items-center justify-center hover:bg-lime/90 transition-colors"
            aria-label="Next scene"
          >
            <ChevronRight size={18} />
          </button>
        )}
      </div>

      {/* Progress dots */}
      <div className="flex items-center justify-center gap-2 py-4 shrink-0 z-20">
        {scenes.map((s, i) => (
          <button
            key={s.id}
            onClick={() => goTo(i)}
            aria-label={`Go to ${s.title}`}
            className={`h-1.5 rounded-full transition-all ${
              i === index ? "w-8 bg-lime" : "w-1.5 bg-white/20 hover:bg-white/40"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
