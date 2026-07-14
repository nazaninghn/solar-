import { Folder, FileText } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import { sitemap } from "./data";

export default function InformationArchitectureSection() {
  return (
    <section id="ia" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Structure"
        title="Information Architecture & Navigation"
        description="Three top-level zones. Marketing exists to get a visitor to Dashboard; Reference exists so the product doesn't drift from itself."
      />
      <div className="grid sm:grid-cols-3 gap-5">
        {sitemap.map((zone) => (
          <div key={zone.label} className="rounded-3xl bg-white border border-gray-100 p-6">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-royal/10 flex items-center justify-center">
                <Folder size={16} className="text-royal" />
              </div>
              <h4 className="text-sm font-semibold text-ink">{zone.label}</h4>
            </div>
            <div className="mt-4 space-y-2 pl-1">
              {zone.children.map((c) => (
                <div key={c} className="flex items-center gap-2 text-xs text-gray-600">
                  <FileText size={12} className="text-gray-300 shrink-0" />
                  {c}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
