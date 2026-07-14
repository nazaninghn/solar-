export type StatusVariant =
  | "healthy"
  | "warning"
  | "critical"
  | "offline"
  | "charging"
  | "discharging"
  | "optimizing"
  | "forecasting";

const config: Record<StatusVariant, { label: string; dot: string; text: string; bg: string; pulse?: boolean }> = {
  healthy: { label: "Healthy", dot: "bg-primary-green", text: "text-primary-green", bg: "bg-primary-green/10" },
  warning: { label: "Warning", dot: "bg-energy-orange", text: "text-energy-orange", bg: "bg-energy-orange/10" },
  critical: { label: "Critical", dot: "bg-danger", text: "text-danger", bg: "bg-danger/10", pulse: true },
  offline: { label: "Offline", dot: "bg-gray-300", text: "text-gray-400", bg: "bg-gray-100" },
  charging: { label: "Charging", dot: "bg-lime-dark", text: "text-lime-dark", bg: "bg-lime/15", pulse: true },
  discharging: { label: "Discharging", dot: "bg-azure", text: "text-azure", bg: "bg-azure/10", pulse: true },
  optimizing: { label: "Optimizing", dot: "bg-royal", text: "text-royal", bg: "bg-royal/10", pulse: true },
  forecasting: { label: "Forecasting", dot: "bg-steel", text: "text-steel", bg: "bg-steel/15" },
};

export default function StatusBadge({ status, label }: { status: StatusVariant; label?: string }) {
  const c = config[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      <span className={`relative flex w-1.5 h-1.5`}>
        {c.pulse && <span className={`absolute inline-flex h-full w-full rounded-full ${c.dot} opacity-60 animate-ping`} />}
        <span className={`relative inline-flex w-1.5 h-1.5 rounded-full ${c.dot}`} />
      </span>
      {label ?? c.label}
    </span>
  );
}
