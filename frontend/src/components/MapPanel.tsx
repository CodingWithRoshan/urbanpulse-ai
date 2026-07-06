"use client";

import { useEffect, useMemo, useState } from "react";
import { GoogleMap, InfoWindow, Marker, useJsApiLoader } from "@react-google-maps/api";
import type { Report } from "@/types/api";
import { useRuntimeConfig } from "@/lib/RuntimeConfigContext";

const AUTH_FAILURE_EVENT = "urbanpulse:gmaps-auth-failure";

declare global {
  interface Window {
    // Google calls this on API key rejection; catches errors loadError misses
    gm_authFailure?: () => void;
  }
}

if (typeof window !== "undefined") {
  window.gm_authFailure = () => {
    window.dispatchEvent(new Event(AUTH_FAILURE_EVENT));
  };
}

// Dark basemap to match the dashboard theme
const DARK_MAP_STYLES: google.maps.MapTypeStyle[] = [
  { elementType: "geometry", stylers: [{ color: "#111827" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#111827" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8496ad" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#151d2e" }] },
  { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#22304a" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0d3b4a" }] },
  { featureType: "poi", elementType: "geometry", stylers: [{ color: "#151d2e" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#22304a" }] },
  { featureType: "transit", elementType: "geometry", stylers: [{ color: "#151d2e" }] },
];

function severityColor(severity: number): string {
  if (severity > 70) return "#FF5A66";
  if (severity > 40) return "#F5A623";
  return "#22D3B8";
}

function markerIcon(severity: number): google.maps.Symbol {
  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale: 6 + severity / 12,
    fillColor: severityColor(severity),
    fillOpacity: 0.85,
    strokeColor: "#0a0e17",
    strokeWeight: 1.5,
  };
}

export function MapPanel({
  reports,
  centerLat,
  centerLng,
}: {
  reports: Report[];
  centerLat: number;
  centerLng: number;
}) {
  const { googleMapsApiKey } = useRuntimeConfig();
  const { isLoaded, loadError } = useJsApiLoader({
    id: "google-map-script",
    googleMapsApiKey,
  });
  const [activeReportId, setActiveReportId] = useState<string | null>(null);
  const [authFailed, setAuthFailed] = useState(false);

  useEffect(() => {
    const handler = () => setAuthFailed(true);
    window.addEventListener(AUTH_FAILURE_EVENT, handler);
    return () => window.removeEventListener(AUTH_FAILURE_EVENT, handler);
  }, []);

  const center = useMemo(() => ({ lat: centerLat, lng: centerLng }), [centerLat, centerLng]);
  const activeReport = reports.find((r) => r.id === activeReportId) ?? null;

  if (!googleMapsApiKey) {
    return (
      <div className="flex h-[280px] w-full items-center justify-center rounded-[10px] border border-red/30 bg-red/5 p-4 text-center text-sm text-red sm:h-[360px]">
        GOOGLE_MAPS_API_KEY is not set on the backend/frontend service&apos;s environment — add it
        in Cloud Run and restart to load the map.
      </div>
    );
  }

  if (loadError || authFailed) {
    return (
      <div className="flex h-[280px] w-full flex-col items-center justify-center gap-1 rounded-[10px] border border-red/30 bg-red/5 p-4 text-center text-sm text-red sm:h-[360px]">
        <p className="font-semibold">Google Maps rejected this API key.</p>
        <p className="text-xs opacity-90">
          In Google Cloud Console: enable the &quot;Maps JavaScript API&quot;, confirm billing is
          active on the project, and check that HTTP referrer restrictions on the key allow this
          origin.
        </p>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex h-[280px] w-full items-center justify-center text-sm text-muted sm:h-[360px]">
        Loading map…
      </div>
    );
  }

  return (
    <div className="h-[280px] w-full sm:h-[360px]">
    <GoogleMap
      mapContainerStyle={{ height: "100%", width: "100%", borderRadius: "10px" }}
      center={center}
      zoom={12.5}
      options={{
        styles: DARK_MAP_STYLES,
        disableDefaultUI: true,
        zoomControl: true,
        scrollwheel: false,
      }}
    >
      {reports.map((r) => (
        <Marker
          key={r.id}
          position={{ lat: r.lat, lng: r.lng }}
          icon={markerIcon(r.severity)}
          onClick={() => setActiveReportId(r.id)}
        />
      ))}

      {activeReport && (
        <InfoWindow
          position={{ lat: activeReport.lat, lng: activeReport.lng }}
          onCloseClick={() => setActiveReportId(null)}
        >
          <div style={{ color: "#111827", fontSize: "13px", lineHeight: 1.5 }}>
            <b>{activeReport.category}</b>
            <br />
            Severity: {activeReport.severity}/100
            <br />
            Priority: {activeReport.priority}
            <br />
            Status: {activeReport.status}
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
    </div>
  );
}
