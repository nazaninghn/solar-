"use client";

import RecommendationsBoard from "@/components/dashboard/recommendations/RecommendationsBoard";

export default function RecommendationsPage() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">AI Recommendations</h1>
        <p className="text-sm text-gray-500 mt-1">
          Review, approve, or reject AI-generated actions across your facility.
        </p>
      </div>

      <RecommendationsBoard />
    </>
  );
}
