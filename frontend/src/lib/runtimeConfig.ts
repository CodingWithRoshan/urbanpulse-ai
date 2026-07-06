/**
 * Runtime (not build-time) app configuration.
 *
 * Previously, the backend URL and Google client IDs were read from
 * `process.env.NEXT_PUBLIC_*` directly in component/module code. Next.js
 * inlines `NEXT_PUBLIC_*` values into the JavaScript bundle at BUILD time,
 * which only works if whatever builds the image also passes them as Docker
 * `--build-arg`s. Deploying with a plain `gcloud run deploy --source .` (no
 * custom build-arg wiring) silently built the image with these unset, baking
 * in the Dockerfile's fallback (`http://localhost:8080`) permanently - no
 * environment variable set on the running Cloud Run service afterward could
 * ever fix that, because the browser never asks the server for it again.
 *
 * Fix: `/api/config` is a Next.js Route Handler that runs on the server, on
 * every request (`export const dynamic = "force-dynamic"`), and reads plain
 * (non-NEXT_PUBLIC_) environment variables at that moment. The client fetches
 * this once on load. Now the backend URL, Google Client ID, and Maps key can
 * all be changed by editing the Cloud Run service's environment variables and
 * restarting the container - no rebuild required.
 */

export type RuntimeConfig = {
  apiBaseUrl: string;
  googleClientId: string;
  googleMapsApiKey: string;
  defaultLat: number;
  defaultLng: number;
};

export const FALLBACK_CONFIG: RuntimeConfig = {
  apiBaseUrl: "http://localhost:8080",
  googleClientId: "",
  googleMapsApiKey: "",
  defaultLat: 28.716,
  defaultLng: 77.164,
};

let cached: RuntimeConfig | null = null;
let inflight: Promise<RuntimeConfig> | null = null;

export async function getRuntimeConfig(): Promise<RuntimeConfig> {
  if (cached) return cached;
  if (typeof window === "undefined") {
    // Server-side render pass (if any) — don't fetch our own route over
    // HTTP; just use the fallback, the client will fetch the real thing.
    return FALLBACK_CONFIG;
  }
  if (!inflight) {
    inflight = fetch("/api/config", { cache: "no-store" })
      .then((res) => (res.ok ? res.json() : FALLBACK_CONFIG))
      .then((data: Partial<RuntimeConfig>) => {
        cached = { ...FALLBACK_CONFIG, ...data };
        return cached;
      })
      .catch(() => {
        cached = FALLBACK_CONFIG;
        return cached;
      });
  }
  return inflight;
}
