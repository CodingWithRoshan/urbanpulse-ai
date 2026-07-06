"use client";

import { useEffect, useState } from "react";
import { Header, type ViewId } from "@/components/Header";
import { DashboardView } from "@/components/views/DashboardView";
import { AssistantView } from "@/components/views/AssistantView";
import { ReportView } from "@/components/views/ReportView";
import { AuthorityView } from "@/components/views/AuthorityView";
import { useAuth } from "@/lib/AuthContext";

export function AppShell() {
  const [activeView, setActiveView] = useState<ViewId>("dashboard");
  const { user } = useAuth();

  // Redirect non-authority roles away from the Authority Console
  useEffect(() => {
    if (activeView === "authority" && user?.role !== "authority" && user?.role !== "admin") {
      setActiveView("dashboard");
    }
  }, [activeView, user]);

  return (
    <>
      <Header activeView={activeView} onChangeView={setActiveView} />
      <main className="mx-auto max-w-[1440px] px-7 pb-16 pt-6.5">
        {activeView === "dashboard" && <DashboardView />}
        {activeView === "assistant" && <AssistantView />}
        {activeView === "report" && <ReportView />}
        {activeView === "authority" && <AuthorityView />}
      </main>
      <footer className="pb-8 pt-2 text-center text-xs text-muted2">
        UrbanPulse AI — Decision Intelligence Platform · Real-time multi-agent architecture (Google ADK + Gemini
        2.5 Flash) · Live weather, AQI, traffic and flood data
      </footer>
    </>
  );
}
