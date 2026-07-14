"use client";

import { useMemo, useState } from "react";
import RecommendationKPIs from "./RecommendationKPIs";
import RecommendationImpactChart from "./RecommendationImpactChart";
import AIRecommendationCard from "./AIRecommendationCard";
import { recommendations, type RecStatus } from "./data";

export default function RecommendationsBoard() {
  const [statuses, setStatuses] = useState<Record<string, RecStatus>>(
    Object.fromEntries(recommendations.map((r) => [r.id, "pending" as RecStatus]))
  );

  const stats = useMemo(() => {
    const pending = recommendations.filter((r) => statuses[r.id] === "pending");
    const approved = recommendations.filter((r) => statuses[r.id] === "approved");
    const totalPotentialSavings = pending.reduce((s, r) => s + (r.savings ?? 0), 0);
    const avgConfidence =
      recommendations.reduce((s, r) => s + r.confidence, 0) / recommendations.length;

    return {
      totalPotentialSavings,
      pendingCount: pending.length,
      avgConfidence,
      approvedCount: approved.length,
    };
  }, [statuses]);

  const setStatus = (id: string, status: RecStatus) =>
    setStatuses((prev) => ({ ...prev, [id]: status }));

  return (
    <>
      <RecommendationKPIs {...stats} />

      <RecommendationImpactChart />

      <div>
        <h2 className="text-lg font-bold text-ink tracking-tight mb-4">Active Recommendations</h2>
        <div className="space-y-4">
          {recommendations.map((item, i) => (
            <AIRecommendationCard
              key={item.id}
              item={item}
              status={statuses[item.id]}
              delay={i * 0.05}
              onApprove={() => setStatus(item.id, "approved")}
              onReject={() => setStatus(item.id, "rejected")}
              onReset={() => setStatus(item.id, "pending")}
            />
          ))}
        </div>
      </div>
    </>
  );
}
