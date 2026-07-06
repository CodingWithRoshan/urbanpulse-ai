"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";
import { useTheme } from "@/lib/ThemeContext";

export type ViewId = "dashboard" | "assistant" | "report" | "authority";

const TABS: { id: ViewId; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "🏙️" },
  { id: "assistant", label: "AI Assistant", icon: "🤖" },
  { id: "report", label: "Report Issue", icon: "📷" },
  { id: "authority", label: "Authority Console", icon: "🏛️" },
];

export function Header({
  activeView,
  onChangeView,
}: {
  activeView: ViewId;
  onChangeView: (view: ViewId) => void;
}) {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [clock, setClock] = useState("");

  useEffect(() => {
    const tick = () =>
      setClock(new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }));
    tick();
    const id = setInterval(tick, 30_000);
    return () => clearInterval(id);
  }, []);

  const visibleTabs = TABS.filter((tab) => {
    if (tab.id === "authority") return user?.role === "authority" || user?.role === "admin";
    return true;
  });

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-3 px-3 py-3 sm:gap-6 sm:px-7 sm:py-3.5">
        <div className="flex items-center gap-2.5 whitespace-nowrap font-display text-[16px] font-bold sm:text-[19px]">
          <svg width="28" height="28" viewBox="0 0 30 30" className="shrink-0">
            <path
              d="M2 15 L9 15 L12 6 L16 24 L19 15 L28 15"
              fill="none"
              stroke="#22D3B8"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="hidden sm:inline">UrbanPulse</span>
          <span className="sm:hidden">UP</span> <span className="text-pulse">AI</span>
        </div>

        <nav className="order-3 flex w-full min-w-0 flex-1 gap-1 overflow-x-auto rounded-[11px] border border-border bg-panel2 p-1 sm:order-none sm:max-w-[640px] sm:overflow-visible">
          {visibleTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onChangeView(tab.id)}
              className={`flex flex-1 items-center justify-center gap-1.5 whitespace-nowrap rounded-lg px-2 py-2 text-[12.5px] font-semibold transition-colors sm:px-2.5 sm:text-[13.5px] ${
                activeView === tab.id
                  ? "bg-pulse text-[#04140F]"
                  : "text-muted hover:bg-white/5 hover:text-text"
              }`}
            >
              <span>{tab.icon}</span>
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3.5">
          <div className="hidden items-center gap-2 font-mono text-xs text-muted md:flex">
            <span className="h-2 w-2 animate-pulseDot rounded-full bg-pulse" />
            LIVE · <span>{clock}</span>
          </div>
          <button
            onClick={toggleTheme}
            className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[10px] border border-border bg-panel2 text-base sm:h-[38px] sm:w-[38px]"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? "🌙" : "☀️"}
          </button>
          {user ? (
            <div className="flex items-center gap-2">
              <div className="hidden text-right leading-tight sm:block">
                <div className="text-xs font-semibold">{user.name}</div>
                <div className="text-[10px] uppercase tracking-wide text-muted">{user.role}</div>
              </div>
              <button
                onClick={logout}
                className="whitespace-nowrap rounded-[10px] border border-border bg-panel2 px-2.5 py-2 text-xs font-semibold text-muted hover:text-text sm:px-3"
              >
                Sign out
              </button>
            </div>
          ) : (
            <a
              href="/login"
              className="whitespace-nowrap rounded-[10px] bg-pulse px-3 py-2 text-xs font-bold text-[#04140F] sm:px-4"
            >
              Sign in
            </a>
          )}
        </div>
      </div>
      <div className="h-[34px] w-full overflow-hidden border-b border-border bg-panel">
        <svg viewBox="0 0 600 34" preserveAspectRatio="none" className="h-full w-[200%] animate-[scrollWave_6s_linear_infinite]">
          <path
            d="M0,17 L60,17 L75,4 L90,30 L105,17 L160,17 L175,10 L190,24 L205,17 L300,17 L315,4 L330,30 L345,17 L400,17 L415,10 L430,24 L445,17 L600,17 L660,17 L675,4 L690,30 L705,17 L760,17 L775,10 L790,24 L805,17 L900,17 L915,4 L930,30 L945,17 L1000,17 L1015,10 L1030,24 L1045,17 L1200,17"
            fill="none"
            stroke="#22D3B8"
            strokeWidth="1.6"
            opacity="0.55"
          />
        </svg>
      </div>
    </header>
  );
}
