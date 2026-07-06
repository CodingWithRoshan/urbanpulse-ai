export type BadgeType = "good" | "warn" | "bad";

function sparkPath(values: number[], w = 160, h = 28): string {
  if (values.length < 2) return "";
  const max = Math.max(...values);
  const min = Math.min(...values);
  const points = values.map(
    (v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / (max - min + 0.001)) * h}`
  );
  return "M" + points.join(" L");
}

const badgeClasses: Record<BadgeType, string> = {
  good: "bg-pulse/10 text-pulse",
  warn: "bg-amber/10 text-amber",
  bad: "bg-red/10 text-red",
};

export function KpiCard({
  icon,
  label,
  value,
  unit,
  badge,
  badgeType,
  trend,
  color,
}: {
  icon: string;
  label: string;
  value: number | string;
  unit: string;
  badge: string;
  badgeType: BadgeType;
  trend: number[];
  color: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-panel border border-border bg-panel p-[18px] transition-transform hover:-translate-y-[3px] hover:border-pulse-dim">
      <div className="mb-2.5 flex items-start justify-between">
        <span className="text-xl">{icon}</span>
        <span
          className={`rounded-full px-2 py-[3px] font-mono text-[10.5px] font-bold tracking-wide ${badgeClasses[badgeType]}`}
        >
          {badge}
        </span>
      </div>
      <div className="font-display text-[30px] font-bold leading-none">
        {value}
        <span className="ml-1 text-sm font-medium text-muted">{unit}</span>
      </div>
      <div className="mt-1 text-[12.5px] text-muted">{label}</div>
      <svg className="mt-2.5 h-7 w-full" viewBox="0 0 160 28" preserveAspectRatio="none">
        <path d={sparkPath(trend)} fill="none" stroke={color} strokeWidth="2" />
      </svg>
    </div>
  );
}
