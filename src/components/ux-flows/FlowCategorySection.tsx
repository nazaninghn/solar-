import SectionHeader from "@/components/design-system/SectionHeader";
import FlowDiagram from "./FlowDiagram";
import type { FlowCategory } from "./data";

export default function FlowCategorySection({ category }: { category: FlowCategory }) {
  return (
    <section id={category.id} className="scroll-mt-24">
      <SectionHeader eyebrow="User Journey" title={category.title} description={category.description} />
      <div className="space-y-4">
        {category.flows.map((flow) => (
          <FlowDiagram key={flow.number} flow={flow} />
        ))}
      </div>
    </section>
  );
}
