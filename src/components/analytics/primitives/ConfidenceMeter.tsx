export default function ConfidenceMeter({
  label,
  value,
  detail,
}: {
  label: string;
  value: number;
  detail?: string;
}) {
  const tier = value >= 85 ? "high" : value >= 65 ? "medium" : "low";
  const colors = {
    high: { bar: "bg-lime-dark", text: "text-lime-dark", tag: "High confidence" },
    medium: { bar: "bg-azure", text: "text-azure", tag: "Medium confidence" },
    low: { bar: "bg-energy-orange", text: "text-energy-orange", tag: "Low confidence" },
  }[tier];

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-ink">{label}</span>
        <span className={`text-xs font-bold ${colors.text}`}>{value}%</span>
      </div>
      <div className="h-2 rounded-full bg-mist overflow-hidden">
        <div className={`h-full rounded-full ${colors.bar} transition-all duration-700`} style={{ width: `${value}%` }} />
      </div>
      <div className="flex items-center justify-between mt-1.5">
        <span className={`text-[10px] font-semibold uppercase tracking-wide ${colors.text}`}>{colors.tag}</span>
        {detail && <span className="text-[10px] text-gray-400">{detail}</span>}
      </div>
    </div>
  );
}
