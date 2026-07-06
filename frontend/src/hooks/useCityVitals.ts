"use client";

import { useEffect, useRef, useState } from "react";
import { fetchCityVitals } from "@/lib/apiClient";
import type { CityVitals } from "@/types/api";

const POLL_INTERVAL_MS = 60_000;
const HISTORY_LENGTH = 7;

export interface CityVitalsHistory {
  aqi: number[];
  trafficDelay: number[];
  healthScore: number[];
}

export function useCityVitals() {
  const [vitals, setVitals] = useState<CityVitals | null>(null);
  const [history, setHistory] = useState<CityVitalsHistory>({
    aqi: [],
    trafficDelay: [],
    healthScore: [],
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;

    async function poll() {
      try {
        const data = await fetchCityVitals();
        if (!mounted.current) return;
        setVitals(data);
        setError(null);
        setHistory((prev) => ({
          aqi: [...prev.aqi, data.aqi.aqi].slice(-HISTORY_LENGTH),
          trafficDelay: [...prev.trafficDelay, data.traffic.avg_delay_min].slice(-HISTORY_LENGTH),
          healthScore: [...prev.healthScore, data.community_health_score].slice(-HISTORY_LENGTH),
        }));
      } catch (err) {
        if (mounted.current) setError(err instanceof Error ? err.message : "Failed to load city vitals");
      } finally {
        if (mounted.current) setIsLoading(false);
      }
    }

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, []);

  return { vitals, history, error, isLoading };
}
