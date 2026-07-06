import { NextResponse } from "next/server";

// Force this route to actually run per-request on the server rather than
// being statically optimized/cached at build time - the whole point is that
// these values can change after the image is built, just by editing the
// Cloud Run service's environment variables and restarting.
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    // Plain (non-NEXT_PUBLIC_) server-side env vars, read fresh on every
    // request. Falls back to the old NEXT_PUBLIC_* names too, in case
    // someone still sets those as build args - harmless either way.
    apiBaseUrl: (
      process.env.BACKEND_API_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8080"
    ).replace(/\/$/, ""),
    googleClientId: process.env.GOOGLE_CLIENT_ID || process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
    googleMapsApiKey:
      process.env.GOOGLE_MAPS_API_KEY || process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    defaultLat: Number(process.env.DEFAULT_LAT || process.env.NEXT_PUBLIC_DEFAULT_LAT || 28.716),
    defaultLng: Number(process.env.DEFAULT_LNG || process.env.NEXT_PUBLIC_DEFAULT_LNG || 77.164),
  });
}
