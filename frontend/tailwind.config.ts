import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        panel2: "var(--panel2)",
        border: "var(--border)",
        text: "var(--text)",
        muted: "var(--muted)",
        muted2: "var(--muted2)",
        pulse: "var(--pulse)",
        "pulse-dim": "var(--pulse-dim)",
        amber: "var(--amber)",
        red: "var(--red)",
        blue: "var(--blue)",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        panel: "var(--radius)",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%": { boxShadow: "0 0 0 0 rgba(34,211,184,.55)" },
          "70%": { boxShadow: "0 0 0 8px rgba(34,211,184,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(34,211,184,0)" },
        },
      },
      animation: {
        fadeIn: "fadeIn .35s ease",
        pulseDot: "pulseDot 1.8s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
