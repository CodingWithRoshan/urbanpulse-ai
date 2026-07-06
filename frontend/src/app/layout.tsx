import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "UrbanPulse AI — Decision Intelligence for Smarter Communities",
  description:
    "Multi-agent civic intelligence platform: real-time weather/AQI/traffic/flood signals, a Gemini-powered decision pipeline, and Gemini Vision complaint triage.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body data-theme="dark" className="font-body">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
