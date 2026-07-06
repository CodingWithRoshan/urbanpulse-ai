import type {
  ApiErrorPayload,
  AuthenticatedUser,
  CityVitals,
  DecisionQuery,
  DecisionResponse,
  Report,
  ReportStatus,
  TokenResponse,
} from "@/types/api";
import { getRuntimeConfig } from "./runtimeConfig";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

let authToken: string | null = null;

/** Called once on app boot (and after login/logout) to keep the in-memory token in sync. */
export function setAuthToken(token: string | null) {
  authToken = token;
}

/**
 * Second, independent layer of defense against the `/api/v1/api/v1/...`
 * duplication bug: even though `/api/config` (route.ts) already normalizes
 * the base URL server-side, this strips a trailing "/api/v1" or "/api" again
 * here, right before it's concatenated with a path. This means the bug
 * cannot recur even if `getRuntimeConfig()` ever returns an unnormalized
 * value from a different source (e.g. FALLBACK_CONFIG is hand-edited later,
 * or a future config provider is swapped in without going through route.ts).
 */
function normalizeApiBaseUrl(raw: string): string {
  let url = raw.trim().replace(/\/+$/, "");
  url = url.replace(/\/api\/v1$/i, "");
  url = url.replace(/\/api$/i, "");
  return url;
}

async function request<T>(
  path: string,
  options: RequestInit & { asFormData?: boolean } = {}
): Promise<T> {
  const { apiBaseUrl: rawApiBaseUrl } = await getRuntimeConfig();
  const apiBaseUrl = normalizeApiBaseUrl(rawApiBaseUrl);

  const headers = new Headers(options.headers);
  if (!options.asFormData && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const res = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const payload = (await res.json()) as ApiErrorPayload;
      detail = payload.detail || detail;
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Auth
export function loginWithGoogle(idToken: string): Promise<TokenResponse> {
  return request<TokenResponse>("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
}

export function fetchMe(): Promise<AuthenticatedUser> {
  return request<AuthenticatedUser>("/api/v1/auth/me");
}

// City vitals
export function fetchCityVitals(): Promise<CityVitals> {
  return request<CityVitals>("/api/v1/city-vitals");
}

// Assistant / decision pipeline
export function askAssistant(query: DecisionQuery): Promise<DecisionResponse> {
  return request<DecisionResponse>("/api/v1/assistant/ask", {
    method: "POST",
    body: JSON.stringify(query),
  });
}

// Reports
export function createReport(file: File, lat: number, lng: number): Promise<Report> {
  const formData = new FormData();
  formData.append("file", file);
  return request<Report>(`/api/v1/reports?lat=${lat}&lng=${lng}`, {
    method: "POST",
    body: formData,
    asFormData: true,
  });
}

export function listReports(sortByPriority = true): Promise<Report[]> {
  return request<Report[]>(`/api/v1/reports?sort_by_priority=${sortByPriority}`);
}

export function updateReportStatus(reportId: string, status: ReportStatus): Promise<Report> {
  return request<Report>(`/api/v1/reports/${reportId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
