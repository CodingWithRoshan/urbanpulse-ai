"use client";

import { GoogleLogin } from "@react-oauth/google";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";

export default function LoginPage() {
  const { user, loginWithGoogleIdToken } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-6">
      <div className="flex items-center gap-2.5 font-display text-2xl font-bold">
        <svg width="34" height="34" viewBox="0 0 30 30">
          <path
            d="M2 15 L9 15 L12 6 L16 24 L19 15 L28 15"
            fill="none"
            stroke="#22D3B8"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        UrbanPulse <span className="text-pulse">AI</span>
      </div>

      <div className="panel w-full max-w-sm text-center">
        <h1 className="mb-1.5 font-display text-lg font-semibold">Sign in to continue</h1>
        <p className="mb-6 text-[13px] text-muted">
          Citizens can report issues and track them. Authorities get the operations console.
        </p>
        <div className="flex justify-center">
          <GoogleLogin
            onSuccess={async (credentialResponse) => {
              if (!credentialResponse.credential) {
                setError("Google did not return a credential. Please try again.");
                return;
              }
              try {
                await loginWithGoogleIdToken(credentialResponse.credential);
                router.replace("/");
              } catch (err) {
                setError(err instanceof Error ? err.message : "Sign-in failed.");
              }
            }}
            onError={() => setError("Google sign-in was cancelled or failed.")}
            theme="filled_black"
          />
        </div>
        {error && <div className="mt-4 text-xs text-red">{error}</div>}
      </div>

      <a href="/" className="text-xs text-muted hover:text-text">
        ← Continue without signing in
      </a>
    </div>
  );
}
