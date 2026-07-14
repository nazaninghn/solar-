"use client";

import UXFlowsNav from "@/components/ux-flows/UXFlowsNav";
import PersonasSection from "@/components/ux-flows/PersonasSection";
import InformationArchitectureSection from "@/components/ux-flows/InformationArchitectureSection";
import FlowCategorySection from "@/components/ux-flows/FlowCategorySection";
import PrinciplesSection from "@/components/ux-flows/PrinciplesSection";
import { flowCategories } from "@/components/ux-flows/data";

export default function UXFlowsPage() {
  return (
    <div className="flex min-h-screen bg-warm-bg">
      <UXFlowsNav />

      <main className="flex-1 min-w-0 px-6 sm:px-10 lg:px-14 py-10 lg:py-14 space-y-20">
        <div>
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">SolarFlow</p>
          <h1 className="text-4xl sm:text-5xl font-bold text-ink tracking-tight">UX Flows &amp; User Journey</h1>
          <p className="mt-4 text-base text-gray-500 max-w-2xl leading-relaxed">
            Every path through SolarFlow, from a cold landing-page visit to a daily 10-second dashboard check —
            mapped step by step. Each flow is marked{" "}
            <span className="text-primary-green font-semibold">Live</span> where the real screen exists today, or{" "}
            <span className="text-gray-500 font-semibold">Planned</span> where it's mapped but not yet built.
          </p>
        </div>

        <PersonasSection />
        <InformationArchitectureSection />

        {flowCategories.map((category) => (
          <FlowCategorySection key={category.id} category={category} />
        ))}

        <PrinciplesSection />
      </main>
    </div>
  );
}
