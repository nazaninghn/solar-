export default function GaugeSemi({
  value,
  max = 100,
  width = 180,
  color = "#D5F332",
  track = "#E8E8EC",
  label,
  sublabel,
  zones,
}: {
  value: number;
  max?: number;
  width?: number;
  color?: string;
  track?: string;
  label?: string;
  sublabel?: string;
  /** optional colored zone markers along the arc, e.g. [{at: 20, color: '#EF4444'}] */
  zones?: { at: number; color: string }[];
}) {
  const height = width / 2 + 20;
  const radius = width / 2 - 12;
  const cx = width / 2;
  const cy = width / 2;
  const arcLength = Math.PI * radius;
  const pct = Math.min(Math.max(value / max, 0), 1);
  const offset = arcLength * (1 - pct);

  const polarToCartesian = (angleDeg: number) => {
    const angleRad = (Math.PI / 180) * angleDeg;
    return { x: cx + radius * Math.cos(angleRad), y: cy - radius * Math.sin(angleRad) };
  };

  return (
    <div className="flex flex-col items-center">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          stroke={track}
          strokeWidth={12}
          strokeLinecap="round"
          fill="none"
        />
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          stroke={color}
          strokeWidth={12}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={arcLength}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-700 ease-out"
        />
        {zones?.map((z, i) => {
          const p = polarToCartesian(180 * (z.at / max));
          return <circle key={i} cx={p.x} cy={p.y} r={4} fill={z.color} />;
        })}
      </svg>
      <div className="-mt-8 text-center">
        <p className="text-2xl font-bold text-ink tracking-tight">{label ?? Math.round(value)}</p>
        {sublabel && <p className="text-[11px] text-gray-400 mt-0.5">{sublabel}</p>}
      </div>
    </div>
  );
}
