"use client";

import AIInsightBanner from "@/components/dashboard/AIInsightBanner";
import KPIGrid from "@/components/dashboard/KPIGrid";
import RecommendationCard from "@/components/dashboard/RecommendationCard";
import AnalyticsChart from "@/components/dashboard/AnalyticsChart";
import PriceChart from "@/components/dashboard/PriceChart";
import WeatherCard from "@/components/dashboard/WeatherCard";

export default function DashboardPage() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">
          Good afternoon, Jane
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Here&apos;s how your facility is performing right now.
        </p>
      </div>

      <AIInsightBanner />

      <KPIGrid />

      <RecommendationCard />

      <div className="grid xl:grid-cols-3 gap-6 lg:gap-8">
        <div className="xl:col-span-2 space-y-6 lg:space-y-8">
          <AnalyticsChart />
          <PriceChart />
        </div>
        <WeatherCard />
      </div>
    </>
  );
}
