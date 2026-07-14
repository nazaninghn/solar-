"use client";

import { useRef, useState } from "react";
import { UploadCloud, Euro, Phone, X, Search } from "lucide-react";
import SectionHeader from "./SectionHeader";

const comboOptions = ["Munich HQ", "Lyon Plant", "Turin Depot", "Rotterdam Hub"];
const segments = ["Day", "Week", "Month"];
const chipOptions = ["Healthy", "Warning", "Critical", "Offline"];

export default function AdvancedInputsSection() {
  const [otp, setOtp] = useState(Array(6).fill(""));
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [comboOpen, setComboOpen] = useState(false);
  const [comboValue, setComboValue] = useState("");
  const [segment, setSegment] = useState("Week");
  const [tags, setTags] = useState(["inverter", "battery"]);
  const [tagDraft, setTagDraft] = useState("");
  const [activeChips, setActiveChips] = useState<string[]>(["Healthy"]);
  const [dragOver, setDragOver] = useState(false);

  function updateOtp(i: number, v: string) {
    const val = v.replace(/[^0-9]/g, "").slice(-1);
    const next = [...otp];
    next[i] = val;
    setOtp(next);
    if (val && i < 5) otpRefs.current[i + 1]?.focus();
  }

  function toggleChip(c: string) {
    setActiveChips((prev) => (prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]));
  }

  function addTag() {
    if (tagDraft.trim()) {
      setTags((prev) => [...prev, tagDraft.trim()]);
      setTagDraft("");
    }
  }

  const filteredCombo = comboOptions.filter((o) => o.toLowerCase().includes(comboValue.toLowerCase()));

  return (
    <section id="advanced-inputs" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Advanced Inputs & Selection"
        description="Specialized entry patterns — OTP, ranges, uploads, formatted values — plus combobox, segmented control, and chip-based selection."
      />

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">OTP Input</label>
          <div className="flex gap-2">
            {otp.map((d, i) => (
              <input
                key={i}
                ref={(el) => { otpRefs.current[i] = el; }}
                value={d}
                onChange={(e) => updateOtp(i, e.target.value)}
                inputMode="numeric"
                maxLength={1}
                className="w-9 h-11 text-center text-sm font-bold rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark"
              />
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">Date Range Picker</label>
          <div className="flex items-center gap-2">
            <input type="date" defaultValue="2026-07-01" className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-lime-dark/40" />
            <span className="text-xs text-gray-400">to</span>
            <input type="date" defaultValue="2026-07-13" className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-lime-dark/40" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-3 px-1">Currency &amp; Phone</label>
          <div className="rounded-3xl bg-white border border-gray-100 p-6 space-y-3">
            <div className="relative">
              <Euro size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input placeholder="0.00" className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-lime-dark/40" />
            </div>
            <div className="relative">
              <Phone size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input placeholder="+49 89 1234 5678" className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-lime-dark/40" />
            </div>
          </div>
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
          className={`rounded-3xl border-2 border-dashed p-6 flex flex-col items-center justify-center text-center transition-colors ${
            dragOver ? "border-lime-dark bg-lime/10" : "border-gray-200 bg-white"
          }`}
        >
          <UploadCloud size={22} className={dragOver ? "text-lime-dark" : "text-gray-400"} />
          <p className="text-sm font-medium text-ink mt-2">Drag &amp; Drop Upload</p>
          <p className="text-xs text-gray-400 mt-1">CSV, XLSX up to 10MB</p>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">Combobox</label>
          <div className="relative">
            <div className="relative">
              <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={comboValue}
                onChange={(e) => setComboValue(e.target.value)}
                onFocus={() => setComboOpen(true)}
                placeholder="Search facility…"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-lime-dark/40"
              />
            </div>
            {comboOpen && (
              <div className="absolute left-0 right-0 mt-1.5 rounded-xl border border-gray-100 bg-white shadow-lg z-10 overflow-hidden">
                {filteredCombo.length ? (
                  filteredCombo.map((o) => (
                    <button
                      key={o}
                      onClick={() => { setComboValue(o); setComboOpen(false); }}
                      className="w-full text-left px-4 py-2.5 text-sm text-ink hover:bg-mist/50"
                    >
                      {o}
                    </button>
                  ))
                ) : (
                  <p className="px-4 py-2.5 text-xs text-gray-400">No matches</p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">Segmented Control</label>
          <div className="flex items-center gap-1 bg-mist/60 rounded-full p-1 w-fit">
            {segments.map((s) => (
              <button
                key={s}
                onClick={() => setSegment(s)}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                  segment === s ? "bg-ink text-white" : "text-gray-500 hover:text-ink"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">Tag Input</label>
          <div className="flex flex-wrap items-center gap-1.5 px-3 py-2 rounded-xl border border-gray-200 focus-within:ring-2 focus-within:ring-lime-dark/40">
            {tags.map((t) => (
              <span key={t} className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-mist text-xs font-medium text-ink">
                {t}
                <button onClick={() => setTags((prev) => prev.filter((x) => x !== t))} className="text-gray-400 hover:text-ink">
                  <X size={11} />
                </button>
              </span>
            ))}
            <input
              value={tagDraft}
              onChange={(e) => setTagDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
              placeholder="Add tag…"
              className="flex-1 min-w-[60px] text-sm outline-none py-1"
            />
          </div>
        </div>

        <div className="rounded-3xl bg-white border border-gray-100 p-6">
          <label className="block text-sm font-medium text-ink mb-3">Filter Chips</label>
          <div className="flex flex-wrap gap-2">
            {chipOptions.map((c) => (
              <button
                key={c}
                onClick={() => toggleChip(c)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                  activeChips.includes(c)
                    ? "bg-ink text-white border-ink"
                    : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
