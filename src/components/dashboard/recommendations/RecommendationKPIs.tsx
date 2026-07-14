"use client";

import { PiggyBank, ListChecks, Gauge, CheckCircle2 } from "lucide-react";
import KPICard from "../KPICard";

export default function RecommendationKPIs({
  totalPotentialSavings,
  pendingCount,
  avgConfidence,
  approvedCount,
}: {
  totalPotentialSavings: number;
  pendingCount: number;
  avgConfidence: number;
  approvedCount: number;
}) {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
      <KPICard
        icon={PiggyBank}
        label="Total Potential Savings"
        value={totalPotentialSavings.toFixed(0)}
        unit="€"
        subtext="If all pending are approved"
        trend="+18%"
        trendUp={true}
        sparkline={[62, 84, 71, 105, 96, 128, 142, 137]}
        sparklineColor="#3CB54A"
        iconBg="bg-primary-green/15"
        iconColor="text-primary-green"
      />
      <KPICard
        icon={ListChecks}
        label="Pending Recommendations"
        value={pendingCount.toString()}
        subtext="Awaiting your decision"
        trend={pendingCount > 0 ? "Action needed" : "All clear"}
        trendUp={pendingCount === 0}
        sparkline={[6, 7, 5, 8, 6, 7, 6, pendingCount]}
        sparklineColor="#4A70BE"
        iconBg="bg-azure/15"
        iconColor="text-azure"
      />
      <KPICard
        icon={Gauge}
        label="Average Confidence"
        value={avgConfidence.toFixed(0)}
        unit="%"
        subtext="Across active recommendations"
        trend="High reliability"
        trendUp={true}
        sparkline={[81, 83, 79, 85, 84, 86, 85, avgConfidence]}
        sparklineColor="#ADC825"
        iconBg="bg-lime/15"
        iconColor="text-lime-dark"
      />
      <KPICard
        icon={CheckCircle2}
        label="Approved This Session"
        value={approvedCount.toString()}
        subtext="Recommendations actioned"
        trend="+100%"
        trendUp={true}
        sparkline={[0, 1, 1, 2, 2, 3, 3, approvedCount]}
        sparklineColor="#305293"
        iconBg="bg-royal/15"
        iconColor="text-royal"
      />
    </div>
  );
}
