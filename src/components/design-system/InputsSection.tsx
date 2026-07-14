"use client";

import { useState } from "react";
import { Mail, Search, Eye, EyeOff, ChevronDown } from "lucide-react";
import SectionHeader from "./SectionHeader";

export default function InputsSection() {
  const [show, setShow] = useState(false);
  const [toggle, setToggle] = useState(true);

  return (
    <section id="inputs" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Components"
        title="Inputs"
        description="Form controls used across authentication and settings — consistent 2xl radius, lime focus ring."
      />

      <div className="rounded-3xl border border-gray-100 bg-white p-6 lg:p-8 grid md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-ink mb-2">Text input</label>
          <div className="relative">
            <Mail size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="email"
              placeholder="you@company.com"
              className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">Password input</label>
          <div className="relative">
            <input
              type={show ? "text" : "password"}
              placeholder="••••••••"
              className="w-full pl-4 pr-11 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all"
            />
            <button
              onClick={() => setShow((s) => !s)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-ink"
            >
              {show ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">Search</label>
          <div className="relative">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search facilities, reports…"
              className="w-full pl-11 pr-4 py-3 rounded-full border border-gray-200 bg-mist/40 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/30 focus:border-lime-dark transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">Select</label>
          <div className="relative">
            <select className="w-full appearance-none pl-4 pr-10 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all">
              <option>Self-Consumption</option>
              <option>Cost Optimization</option>
              <option>Backup Reserve</option>
            </select>
            <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">Textarea</label>
          <textarea
            rows={3}
            placeholder="Add a note for the maintenance team…"
            className="w-full px-4 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-lime-dark/40 focus:border-lime-dark transition-all resize-none"
          />
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-ink mb-2">Checkbox &amp; Radio</p>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input type="checkbox" defaultChecked className="w-4 h-4 rounded accent-[#ADC825]" />
                <span className="text-sm text-gray-600">Remember me</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input type="radio" name="ds-radio" defaultChecked className="w-4 h-4 accent-[#ADC825]" />
                <span className="text-sm text-gray-600">Option A</span>
              </label>
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input type="radio" name="ds-radio" className="w-4 h-4 accent-[#ADC825]" />
                <span className="text-sm text-gray-600">Option B</span>
              </label>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-ink mb-2">Toggle switch</p>
            <button
              onClick={() => setToggle((t) => !t)}
              className={`relative w-11 h-6 rounded-full transition-colors ${toggle ? "bg-lime-dark" : "bg-gray-200"}`}
              aria-pressed={toggle}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  toggle ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
