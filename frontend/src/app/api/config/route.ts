import { NextResponse } from "next/server";

// Force this route to actually run per-request on the server rather than
// being statically optimized/cached at build time - the whole point is that
// these values can change after the image is built, just by editing the
// Cloud Run service's environment variables and restarting.
export const dynamic = "force-dynamic";

/**
 * Normalizes whatever is set as the backend base URL so that apiClient.ts's
 * `${apiBaseUrl}${path}` concatenation can never produce a duplicated path
 * segment such as `/api/v1/api/v1/...`.
 *
 * Root cause this guards against: apiClient.ts always calls paths like
 * "/api/v1/city-vitals" itself, expecting `apiBaseUrl` to be the bare origin
 * (e.g. "https://backend-xxxx.run.app"). If whoever configures the
 * BACKEND_API_URL / NEXT_PUBLIC_API_BASE_URL environment variable instead
 * points it at the API root - e.g. "https://backend-xxxx.run.app/api/v1" -
 * every request doubles up to "https://backend-xxxx.run.app/api/v1/api/v1/...".
 * That's an environment-variable misconfiguration, not a code bug, but since
 * it's easy to reintroduce by hand, we strip a trailing "/api/v1" or "/api"
 * (in that order, with or without a trailing slash) here so the deployed
 * value is self-healing regardless of which form someone enters.
 */
function normalizeApiBaseUrl(raw: string): string {
  let url = raw.trim().replace(/\/+$/, ""); // drop trailing slash(es)
  url = url.replace(/\/api\/v1$/i, ""); // drop trailing /api/v1
  url = url.replace(/\/api$/i, ""); // drop trailing /api (in case v1 was already stripped or never present)
  return url;
}

export async function GET() {
  const rawApiBaseUrl =
    process.env.BACKEND_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8080";

  return NextResponse.json({
    // Plain (non-NEXT_PUBLIC_) server-side env vars, read fresh on every
    // request. Falls back to the old NEXT_PUBLIC_* names too, in case
    // someone still sets those as build args - harmless either way.
    apiBaseUrl: normalizeApiBaseUrl(rawApiBaseUrl),
    googleClientId: process.env.GOOGLE_CLIENT_ID || process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
    googleMapsApiKey:
      process.env.GOOGLE_MAPS_API_KEY || process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    defaultLat: Number(process.env.DEFAULT_LAT || process.env.NEXT_PUBLIC_DEFAULT_LAT || 28.716),
    defaultLng: Number(process.env.DEFAULT_LNG || process.env.NEXT_PUBLIC_DEFAULT_LNG || 77.164),
  });
}
