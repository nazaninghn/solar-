import { UserRound } from "lucide-react";
import SectionHeader from "@/components/design-system/SectionHeader";
import { personas } from "./data";

export default function PersonasSection() {
  return (
    <section id="personas" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Who we're designing for"
        title="Target Users"
        description="Six roles, six different relationships with the same data — the dashboard has to serve all of them without becoming six dashboards."
      />
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {personas.map((p) => (
          <div key={p.role} className="rounded-3xl bg-white border border-gray-100 p-6">
            <div className="w-11 h-11 rounded-2xl bg-ink flex items-center justify-center">
              <UserRound size={20} className="text-lime" />
            </div>
            <h4 className="text-sm font-semibold text-ink mt-4">{p.role}</h4>
            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{p.goal}</p>
            <span className="inline-block mt-3 text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full bg-mist text-gray-500">
              {p.frequency} use
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
