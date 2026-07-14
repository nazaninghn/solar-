"use client";

import DesignSystemNav from "@/components/design-system/DesignSystemNav";
import FoundationsSection from "@/components/design-system/FoundationsSection";
import ButtonsSection from "@/components/design-system/ButtonsSection";
import InputsSection from "@/components/design-system/InputsSection";
import AdvancedInputsSection from "@/components/design-system/AdvancedInputsSection";
import CardsSection from "@/components/design-system/CardsSection";
import TablesSection from "@/components/design-system/TablesSection";
import DataDisplaySection from "@/components/design-system/DataDisplaySection";
import ChartsSection from "@/components/design-system/ChartsSection";
import NavigationSection from "@/components/design-system/NavigationSection";
import AdvancedNavigationSection from "@/components/design-system/AdvancedNavigationSection";
import FeedbackSection from "@/components/design-system/FeedbackSection";
import OverlaysSection from "@/components/design-system/OverlaysSection";
import NotificationsSection from "@/components/design-system/NotificationsSection";
import EmptyStatesSection from "@/components/design-system/EmptyStatesSection";
import ErrorPagesSection from "@/components/design-system/ErrorPagesSection";
import IconsSection from "@/components/design-system/IconsSection";
import AccessibilityMotionSection from "@/components/design-system/AccessibilityMotionSection";
import ThemingSection from "@/components/design-system/ThemingSection";

export default function DesignSystemPage() {
  return (
    <div className="flex min-h-screen bg-warm-bg">
      <DesignSystemNav />

      <main className="flex-1 min-w-0 px-6 sm:px-10 lg:px-14 py-10 lg:py-14 space-y-20">
        <div>
          <p className="text-xs font-semibold text-lime-dark uppercase tracking-widest mb-3">SolarFlow</p>
          <h1 className="text-4xl sm:text-5xl font-bold text-ink tracking-tight">Design System</h1>
          <p className="mt-4 text-base text-gray-500 max-w-2xl leading-relaxed">
            A production-ready, enterprise SaaS component library — every token, control, and pattern used across
            the SolarFlow marketing site, authentication flow, and analytics dashboard.
          </p>
        </div>

        <FoundationsSection />
        <ButtonsSection />
        <InputsSection />
        <AdvancedInputsSection />
        <CardsSection />
        <TablesSection />
        <DataDisplaySection />
        <ChartsSection />
        <NavigationSection />
        <AdvancedNavigationSection />
        <FeedbackSection />
        <OverlaysSection />
        <NotificationsSection />
        <EmptyStatesSection />
        <ErrorPagesSection />
        <IconsSection />
        <AccessibilityMotionSection />
        <ThemingSection />
      </main>
    </div>
  );
}
