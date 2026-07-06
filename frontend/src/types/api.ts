// Mirrors backend/app/domain/schemas.py and enums.py

export type Role = "citizen" | "authority" | "admin";

export type ReportStatus = "Pending" | "In Progress" | "Resolved" | "Rejected";

export type ComplaintCategory =
  | "Pothole"
  | "Garbage Overflow"
  | "Waterlogging"
  | "Broken Streetlight"
  | "Other";

export type Intent = "flood_risk" | "outdoor_safety" | "commute_decision";

// Auth
export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  email: string;
  name: string;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  name: string;
  role: Role;
}

// City vitals
export interface WeatherSnapshot {
  temp_c: number;
  condition: string;
  humidity: number;
  source: string;
}

export interface AqiSnapshot {
  aqi: number;
  category: string;
  dominant_pollutant: string;
  source: string;
}

export interface TrafficSnapshot {
  level: string;
  avg_delay_min: number;
  source: string;
}

export interface FloodPrediction {
  risk: string;
  confidence: number;
  rationale: string;
  source: string;
}

export interface CityAlert {
  title: string;
  severity: string;
}

export interface CityTime {
  local_time: string;
  timezone_id: string;
  utc_offset_minutes: number;
  source: string;
}

export interface CityVitals {
  weather: WeatherSnapshot;
  aqi: AqiSnapshot;
  traffic: TrafficSnapshot;
  flood_risk: FloodPrediction;
  alerts: CityAlert[];
  community_health_score: number;
  city_time: CityTime;
}

// Assistant / decision pipeline
export interface DecisionQuery {
  question: string;
  lat?: number;
  lng?: number;
  session_id?: string;
}

export interface RiskComponents {
  aqi_risk: number;
  traffic_risk: number;
  flood_risk: number;
}

export interface RiskScore {
  composite: number;
  components: RiskComponents;
}

export interface Recommendation {
  verdict: string;
  reason: string;
  risk_score: number;
}

export interface DecisionResponse {
  intent: Intent;
  traffic: TrafficSnapshot;
  environment: Record<string, unknown>;
  prediction: FloodPrediction;
  risk: RiskScore;
  recommendation: Recommendation;
}

// Citizen reports / complaints
export interface Report {
  id: string;
  category: ComplaintCategory;
  severity: number;
  priority: number;
  department: string;
  justification: string;
  status: ReportStatus;
  lat: number;
  lng: number;
  image_url?: string | null;
  reported_by?: string | null;
}

export interface ApiErrorPayload {
  detail: string;
}
