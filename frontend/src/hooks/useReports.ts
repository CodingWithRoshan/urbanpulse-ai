"use client";

import { useCallback, useEffect, useState } from "react";
import { listReports, updateReportStatus } from "@/lib/apiClient";
import type { Report, ReportStatus } from "@/types/api";
import { useAuth } from "@/lib/AuthContext";

export function useReports() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!user) {
      setReports([]);
      return;
    }
    setIsLoading(true);
    try {
      const data = await listReports(true);
      setReports(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const changeStatus = useCallback(
    async (reportId: string, status: ReportStatus) => {
      const updated = await updateReportStatus(reportId, status);
      setReports((prev) => prev.map((r) => (r.id === reportId ? updated : r)));
    },
    []
  );

  return { reports, isLoading, error, refresh, changeStatus };
}
