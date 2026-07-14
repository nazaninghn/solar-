"use client";

import { Sankey, Tooltip, ResponsiveContainer, Rectangle, Layer } from "recharts";
import SectionHeader from "@/components/design-system/SectionHeader";
import ChartCard from "../primitives/ChartCard";

const sankeyData = {
  nodes: [
    { name: "Solar" },
    { name: "Grid Import" },
    { name: "Battery" },
    { name: "Consumption" },
    { name: "Grid Export" },
  ],
  links: [
    { source: 0, target: 3, value: 480 },
    { source: 0, target: 2, value: 220 },
    { source: 0, target: 4, value: 120 },
    { source: 2, target: 3, value: 160 },
    { source: 1, target: 3, value: 140 },
  ],
};

const nodeColors = ["#ADC825", "#879DBA", "#305293", "#293234", "#4A70BE"];

function CustomNode(props: { x?: number; y?: number; width?: number; height?: number; index?: number; payload?: { name: string } }) {
  const { x = 0, y = 0, width = 0, height = 0, index = 0, payload } = props;
  return (
    <Layer>
      <Rectangle x={x} y={y} width={width} height={height} fill={nodeColors[index % nodeColors.length]} radius={4} />
      <text x={x + width + 8} y={y + height / 2} textAnchor="start" dominantBaseline="middle" fontSize={11} fill="#293234" fontWeight={600}>
        {payload?.name}
      </text>
    </Layer>
  );
}

export default function EnergyFlowSection() {
  return (
    <section id="energy-flow" className="scroll-mt-24">
      <SectionHeader
        eyebrow="Signature Visualization"
        title="Energy Flow Diagram"
        description="Sankey diagram tracing energy from source to destination — the single highest-value chart for explaining facility-wide flow at a glance."
      />

      <ChartCard title="Facility Energy Flow" subtitle="Today, cumulative kWh" tag="Sankey" height="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <Sankey
            data={sankeyData}
            node={<CustomNode />}
            link={{ stroke: "#D5F332", strokeOpacity: 0.35 }}
            nodePadding={28}
            margin={{ top: 10, bottom: 10, left: 10, right: 90 }}
          >
            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
          </Sankey>
        </ResponsiveContainer>
      </ChartCard>
    </section>
  );
}
