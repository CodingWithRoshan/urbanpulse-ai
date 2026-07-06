"use client";

import { GoogleOAuthProvider } from "@react-oauth/google";
import type { ReactNode } from "react";
import { AuthProvider } from "@/lib/AuthContext";
import { ThemeProvider } from "@/lib/ThemeContext";
import { RuntimeConfigProvider, useRuntimeConfig } from "@/lib/RuntimeConfigContext";

function InnerProviders({ children }: { children: ReactNode }) {
  const { googleClientId } = useRuntimeConfig();
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <RuntimeConfigProvider>
      <InnerProviders>{children}</InnerProviders>
    </RuntimeConfigProvider>
  );
}
