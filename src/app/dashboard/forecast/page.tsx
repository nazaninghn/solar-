"use client";

import ForecastInsightBanner from "@/components/dashboard/forecast/ForecastInsightBanner";
import ForecastKPIs from "@/components/dashboard/forecast/ForecastKPIs";
import SevenDayStrip from "@/components/dashboard/forecast/SevenDayStrip";
import ForecastChart from "@/components/dashboard/forecast/ForecastChart";
import FinancialImpact from "@/components/dashboard/forecast/FinancialImpact";
import ForecastTable from "@/components/dashboard/forecast/ForecastTable";

export default function ForecastPage() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Energy Forecast</h1>
        <p className="text-sm text-gray-500 mt-1">
          AI-predicted production, consumption, and pricing for the week ahead.
        </p>
      </div>

      <ForecastInsightBanner />

      <ForecastKPIs />

      <SevenDayStrip />

      <ForecastChart />

      <FinancialImpact />

      <ForecastTable />
    </>
  );
}
