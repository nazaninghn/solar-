"use client";

import AnalyticsNav from "@/components/analytics/AnalyticsNav";
import ChartGallerySection from "@/components/analytics/sections/ChartGallerySection";
import EnergyFlowSection from "@/components/analytics/sections/EnergyFlowSection";
import KPISection from "@/components/analytics/sections/KPISection";
import AISection from "@/components/analytics/sections/AISection";
import WeatherSection from "@/components/analytics/sections/WeatherSection";
import BatterySection from "@/components/analytics/sections/BatterySection";
import GridSection from "@/components/analytics/sections/GridSection";
import FactorySection from "@/components/analytics/sections/FactorySection";
import FinancialSection from "@/components/analytics/sections/FinancialSection";
import StatusStatesSection from "@/components/analytics/sections/StatusStatesSection";

export default function AnalyticsSystemPage() {
  return (
    <div className="flex min-h-screen bg-warm-bg">
      <AnalyticsNav />

      <main className="flex-1 min-w-0 px-6 sm:px-10 lg:px-14 py-10 lg:py-14 space-y-20">
        <div>
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">SolarFlow</p>
          <h1 className="text-4xl sm:text-5xl font-bold text-ink tracking-tight">Data Visualization System</h1>
          <p className="mt-4 text-base text-gray-500 max-w-2xl leading-relaxed">
            A reusable analytics component library for industrial energy intelligence — charts, KPIs, AI signals,
            and domain widgets for production, battery, weather, pricing, factory, and financial data. Every widget
            below is composed from a small set of primitives: <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">ChartCard</code>,{" "}
            <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">MetricCard</code>,{" "}
            <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">GaugeRadial</code>,{" "}
            <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">GaugeSemi</code>,{" "}
            <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">ConfidenceMeter</code>, and{" "}
            <code className="font-mono bg-mist px-1.5 py-0.5 rounded text-[13px]">StatusBadge</code>.
          </p>
        </div>

        <ChartGallerySection />
        <EnergyFlowSection />
        <KPISection />
        <AISection />
        <WeatherSection />
        <BatterySection />
        <GridSection />
        <FactorySection />
        <FinancialSection />
        <StatusStatesSection />
      </main>
    </div>
  );
}
