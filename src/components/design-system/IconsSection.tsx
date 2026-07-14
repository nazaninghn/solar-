"use client";

import {
  Sun,
  Zap,
  Battery,
  BatteryCharging,
  Euro,
  PiggyBank,
  Leaf,
  CloudSun,
  Wind,
  Droplets,
  TrendingUp,
  ArrowRightLeft,
  ShoppingCart,
  Sparkles,
  Bell,
  Search,
  Settings,
  FileText,
  Receipt,
  BarChart3,
  LayoutDashboard,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  Download,
  Calendar,
  ChevronDown,
  ArrowUpRight,
  HeartPulse,
  RefreshCw,
  LucideIcon,
} from "lucide-react";
import SectionHeader from "./SectionHeader";

const icons: { icon: LucideIcon; name: string }[] = [
  { icon: Sun, name: "Sun" },
  { icon: Zap, name: "Zap" },
  { icon: Battery, name: "Battery" },
  { icon: BatteryCharging, name: "BatteryCharging" },
  { icon: Euro, name: "Euro" },
  { icon: PiggyBank, name: "PiggyBank" },
  { icon: Leaf, name: "Leaf" },
  { icon: CloudSun, name: "CloudSun" },
  { icon: Wind, name: "Wind" },
  { icon: Droplets, name: "Droplets" },
  { icon: TrendingUp, name: "TrendingUp" },
  { icon: ArrowRightLeft, name: "ArrowRightLeft" },
  { icon: ShoppingCart, name: "ShoppingCart" },
  { icon: Sparkles, name: "Sparkles" },
  { icon: Bell, name: "Bell" },
  { icon: Search, name: "Search" },
  { icon: Settings, name: "Settings" },
  { icon: FileText, name: "FileText" },
  { icon: Receipt, name: "Receipt" },
  { icon: BarChart3, name: "BarChart3" },
  { icon: LayoutDashboard, name: "LayoutDashboard" },
  { icon: CheckCircle2, name: "CheckCircle2" },
  { icon: AlertTriangle, name: "AlertTriangle" },
  { icon: XCircle, name: "XCircle" },
  { icon: Info, name: "Info" },
  { icon: Download, name: "Download" },
  { icon: Calendar, name: "Calendar" },
  { icon: ChevronDown, name: "ChevronDown" },
  { icon: ArrowUpRight, name: "ArrowUpRight" },
  { icon: HeartPulse, name: "HeartPulse" },
  { icon: RefreshCw, name: "RefreshCw" },
];

export default function IconsSection() {
  return (
    <section id="icons" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Foundations"
        title="Icons"
        description="Lucide React, 1.5–2px stroke weight, sized 14–24px depending on context. A sample of the set used across the product."
      />

      <div className="rounded-3xl bg-white border border-gray-100 p-6">
        <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-3">
          {icons.map(({ icon: Icon, name }) => (
            <div
              key={name}
              className="flex flex-col items-center justify-center gap-2 py-4 rounded-2xl hover:bg-mist/50 transition-colors"
              title={name}
            >
              <Icon size={20} className="text-ink" strokeWidth={1.75} />
              <span className="text-[10px] text-gray-400 truncate max-w-full px-1">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
