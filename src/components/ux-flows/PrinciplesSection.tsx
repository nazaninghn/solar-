import { HelpCircle, Euro, Gauge, ShieldAlert, Target, Sun, Zap, Battery, PiggyBank, Sparkles, AlertTriangle } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";

const explainability = [
  { icon: HelpCircle, label: "Why?", body: "The reasoning in plain language — what data triggered this." },
  { icon: Euro, label: "How much money?", body: "A concrete € figure, never a vague 'save energy'." },
  { icon: Gauge, label: "Confidence level", body: "A percentage, tied to model track record, not marketing." },
  { icon: ShieldAlert, label: "Potential risks", body: "What could make this recommendation wrong." },
  { icon: Target, label: "Expected outcome", body: "What changes if the user approves — stated as a fact." },
];

const dashboardChecks = [
  { icon: Sun, label: "Today's production" },
  { icon: Zap, label: "Today's consumption" },
  { icon: Battery, label: "Battery status" },
  { icon: Euro, label: "Electricity prices" },
  { icon: PiggyBank, label: "Financial savings" },
  { icon: Sparkles, label: "AI recommendation" },
  { icon: AlertTriangle, label: "Risk level" },
];

export default function PrinciplesSection() {
  return (
    <section id="principles" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Rules the product follows"
        title="AI Explainability & the 10-Second Dashboard"
        description="Two constraints that shape every screen in this system, not just guidelines for a few of them."
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-3xl bg-white border border-gray-100 p-6 lg:p-8">
          <h4 className="text-sm font-semibold text-ink mb-1">Every AI recommendation must answer:</h4>
          <p className="text-xs text-gray-400 mb-5">No exceptions — a recommendation missing any of these five doesn't ship.</p>
          <div className="space-y-3">
            {explainability.map((e) => (
              <div key={e.label} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-lime/15 flex items-center justify-center shrink-0">
                  <e.icon size={15} className="text-lime-dark" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink">{e.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{e.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-ink text-white p-6 lg:p-8">
          <h4 className="text-sm font-semibold mb-1">Within 10 seconds, the dashboard must communicate:</h4>
          <p className="text-xs text-white/40 mb-5">If a user can't answer all seven from the first screen, the layout has failed.</p>
          <div className="grid grid-cols-2 gap-3">
            {dashboardChecks.map((d) => (
              <div key={d.label} className="flex items-center gap-2.5 rounded-2xl bg-white/5 px-3.5 py-3">
                <d.icon size={15} className="text-lime shrink-0" />
                <span className="text-xs">{d.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
