"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchMe, loginWithGoogle, setAuthToken } from "@/lib/apiClient";
import type { AuthenticatedUser, Role } from "@/types/api";

const STORAGE_KEY = "urbanpulse.jwt";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  isLoading: boolean;
  loginWithGoogleIdToken: (idToken: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (!stored) {
      setIsLoading(false);
      return;
    }
    setAuthToken(stored);
    fetchMe()
      .then(setUser)
      .catch(() => {
        window.localStorage.removeItem(STORAGE_KEY);
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const loginWithGoogleIdToken = useCallback(async (idToken: string) => {
    const tokenResponse = await loginWithGoogle(idToken);
    window.localStorage.setItem(STORAGE_KEY, tokenResponse.access_token);
    setAuthToken(tokenResponse.access_token);
    const me = await fetchMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    setAuthToken(null);
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (...roles: Role[]) => !!user && roles.includes(user.role),
    [user]
  );

  const value = useMemo(
    () => ({ user, isLoading, loginWithGoogleIdToken, logout, hasRole }),
    [user, isLoading, loginWithGoogleIdToken, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
