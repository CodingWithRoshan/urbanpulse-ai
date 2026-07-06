"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { FALLBACK_CONFIG, getRuntimeConfig, type RuntimeConfig } from "./runtimeConfig";

const RuntimeConfigCtx = createContext<RuntimeConfig>(FALLBACK_CONFIG);

/**
 * Fetches /api/config once and holds children until it resolves, so every
 * descendant (GoogleOAuthProvider, MapPanel, DashboardView, ReportView) always
 * mounts with the real backend URL / Google IDs already known - no flash of
 * "localhost" and no components mounting a Google script loader with an
 * empty key that never gets retried.
 */
export function RuntimeConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<RuntimeConfig | null>(null);

  useEffect(() => {
    let mounted = true;
    getRuntimeConfig().then((resolved) => {
      if (mounted) setConfig(resolved);
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (!config) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0A0E17",
          color: "#8496AD",
          fontFamily: "sans-serif",
          fontSize: "13px",
        }}
      >
        Loading UrbanPulse AI…
      </div>
    );
  }

  return <RuntimeConfigCtx.Provider value={config}>{children}</RuntimeConfigCtx.Provider>;
}

export function useRuntimeConfig(): RuntimeConfig {
  return useContext(RuntimeConfigCtx);
}
