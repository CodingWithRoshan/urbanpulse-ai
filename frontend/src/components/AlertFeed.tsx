import type { CityAlert } from "@/types/api";

function dotColor(severity: string): string {
  const s = severity.toLowerCase();
  if (s.includes("bad") || s.includes("high") || s.includes("severe")) return "var(--red)";
  return "var(--amber)";
}

export function AlertFeed({ alerts }: { alerts: CityAlert[] }) {
  if (alerts.length === 0) {
    return <div className="text-[13px] text-muted">No active alerts right now — conditions are normal.</div>;
  }
  return (
    <div>
      {alerts.map((a, i) => (
        <div key={`${a.title}-${i}`} className="flex gap-2.5 border-b border-border py-2.5 last:border-none last:pb-0">
          <div className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full" style={{ background: dotColor(a.severity) }} />
          <div className="text-[13px]">
            <b className="block">{a.title}</b>
            <span className="text-[11.5px] text-muted">Severity: {a.severity}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
