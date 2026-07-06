"use client";

import dynamic from "next/dynamic";
import { useCityVitals } from "@/hooks/useCityVitals";
import { useReports } from "@/hooks/useReports";
import { useAuth } from "@/lib/AuthContext";
import { useRuntimeConfig } from "@/lib/RuntimeConfigContext";
import { KpiCard } from "@/components/KpiCard";
import { AlertFeed } from "@/components/AlertFeed";
import { CategoryChart, DepartmentResolutionChart, HealthTrendChart } from "@/components/Charts";

const MapPanel = dynamic(() => import("@/components/MapPanel").then((m) => m.MapPanel), {
  ssr: false,
  loading: () => <div className="flex h-[360px] items-center justify-center text-sm text-muted">Loading map…</div>,
});

export function DashboardView() {
  const { vitals, history, error, isLoading } = useCityVitals();
  const { user } = useAuth();
  const { reports } = useReports();
  const { defaultLat, defaultLng } = useRuntimeConfig();

  if (isLoading) {
    return <div className="py-16 text-center text-muted">Loading live city vitals…</div>;
  }
  if (error || !vitals) {
    return (
      <div className="rounded-panel border border-red/30 bg-red/5 p-6 text-sm text-red">
        Couldn&apos;t load city vitals: {error ?? "unknown error"}. Confirm the backend API is running and
        reachable at the configured URL.
      </div>
    );
  }

  const badgeFor = (val: number, warnAt: number, badAt: number) =>
    val >= badAt ? "bad" : val >= warnAt ? "warn" : "good";

  return (
    <section className="animate-fadeIn">
      <div className="section-title">
        City Vitals <div className="line" />
      </div>
      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <KpiCard
          icon="🌤️"
          label={`Weather · ${vitals.weather.condition} · ${vitals.city_time.local_time} ${vitals.city_time.timezone_id.split("/").pop()}`}
          value={vitals.weather.temp_c}
          unit="°C"
          badge="LIVE"
          badgeType="good"
          trend={history.aqi.length ? history.aqi : [vitals.weather.temp_c]}
          color="#22D3B8"
        />
        <KpiCard
          icon="🫁"
          label="Air Quality Index"
          value={vitals.aqi.aqi}
          unit={vitals.aqi.category}
          badge={vitals.aqi.category.toUpperCase()}
          badgeType={badgeFor(vitals.aqi.aqi, 100, 150)}
          trend={history.aqi.length ? history.aqi : [vitals.aqi.aqi]}
          color="#FF5A66"
        />
        <KpiCard
          icon="🚦"
          label={`Traffic · avg delay ${vitals.traffic.avg_delay_min} min`}
          value={vitals.traffic.level}
          unit=""
          badge={vitals.traffic.level.toUpperCase()}
          badgeType={badgeFor(vitals.traffic.avg_delay_min, 15, 25)}
          trend={history.trafficDelay.length ? history.trafficDelay : [vitals.traffic.avg_delay_min]}
          color="#F5A623"
        />
        <KpiCard
          icon="🌊"
          label="Flood Risk (monsoon model)"
          value={vitals.flood_risk.risk}
          unit=""
          badge="WATCH"
          badgeType={vitals.flood_risk.risk.toLowerCase() === "high" ? "bad" : "warn"}
          trend={[vitals.flood_risk.confidence * 100]}
          color="#5B9DF9"
        />
        <KpiCard
          icon="📢"
          label="Active Public Alerts"
          value={vitals.alerts.length}
          unit="live"
          badge="MONITOR"
          badgeType={vitals.alerts.length > 2 ? "warn" : "good"}
          trend={[vitals.alerts.length]}
          color="#F5A623"
        />
        <KpiCard
          icon="💚"
          label="Community Health Score"
          value={vitals.community_health_score}
          unit="/100"
          badge={vitals.community_health_score >= 60 ? "FAIR" : "LOW"}
          badgeType={vitals.community_health_score >= 60 ? "good" : "warn"}
          trend={history.healthScore.length ? history.healthScore : [vitals.community_health_score]}
          color="#22D3B8"
        />
      </div>

      <div className="section-title">
        Live Situational Map <div className="line" />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="panel">
          <h3 className="mb-3 flex items-center gap-2 font-display text-[14.5px] font-semibold">
            📍 Complaint Heatmap &amp; Active Alerts
          </h3>
          {user ? (
            <MapPanel reports={reports} centerLat={defaultLat} centerLng={defaultLng} />
          ) : (
            <div className="flex h-[360px] flex-col items-center justify-center gap-2 rounded-[10px] border border-dashed border-border text-center text-sm text-muted">
              <p>Sign in to see live citizen reports plotted on the map.</p>
              <a href="/login" className="rounded-[10px] bg-pulse px-4 py-2 text-xs font-bold text-[#04140F]">
                Sign in
              </a>
            </div>
          )}
        </div>
        <div className="panel">
          <h3 className="mb-3 flex items-center gap-2 font-display text-[14.5px] font-semibold">
            🚨 Public Alerts Feed
          </h3>
          <AlertFeed alerts={vitals.alerts} />
        </div>
      </div>

      <div className="section-title">
        Community Analytics <div className="line" />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="panel">
          <h3 className="mb-3 font-display text-[14.5px] font-semibold">📊 Complaints by Category</h3>
          <CategoryChart reports={reports} />
        </div>
        <div className="panel">
          <h3 className="mb-3 font-display text-[14.5px] font-semibold">💚 Community Health Score Trend</h3>
          <HealthTrendChart history={history.healthScore.length ? history.healthScore : [vitals.community_health_score]} />
        </div>
      </div>
      {user && (
        <div className="mt-4 panel">
          <h3 className="mb-3 font-display text-[14.5px] font-semibold">📈 Resolution Rate by Department</h3>
          <DepartmentResolutionChart reports={reports} />
        </div>
      )}
    </section>
  );
}
