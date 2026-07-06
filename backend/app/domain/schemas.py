from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import ComplaintCategory, Intent, ReportStatus, Role


# Auth
class GoogleLoginRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    email: str
    name: str


class AuthenticatedUser(BaseModel):
    id: str
    email: str
    name: str
    role: Role


# City vitals
class WeatherSnapshot(BaseModel):
    temp_c: float
    condition: str
    humidity: int
    source: str


class AqiSnapshot(BaseModel):
    aqi: int
    category: str
    dominant_pollutant: str
    source: str


class TrafficSnapshot(BaseModel):
    level: str
    avg_delay_min: float
    source: str


class FloodPrediction(BaseModel):
    risk: str
    confidence: float
    rationale: str
    source: str


class Alert(BaseModel):
    title: str
    severity: str


class CityTime(BaseModel):
    local_time: str
    timezone_id: str
    utc_offset_minutes: int
    source: str


class CityVitals(BaseModel):
    weather: WeatherSnapshot
    aqi: AqiSnapshot
    traffic: TrafficSnapshot
    flood_risk: FloodPrediction
    alerts: list[Alert]
    community_health_score: int
    city_time: CityTime


# Assistant / decision pipeline
class DecisionQuery(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    lat: Optional[float] = None
    lng: Optional[float] = None
    session_id: Optional[str] = "anonymous"


class RiskComponents(BaseModel):
    aqi_risk: float
    traffic_risk: float
    flood_risk: float


class RiskScore(BaseModel):
    composite: int
    components: RiskComponents


class Recommendation(BaseModel):
    verdict: str
    reason: str
    risk_score: int


class DecisionResponse(BaseModel):
    intent: Intent
    traffic: TrafficSnapshot
    environment: dict
    prediction: FloodPrediction
    risk: RiskScore
    recommendation: Recommendation


# Citizen reports / complaints
class ComplaintClassification(BaseModel):
    category: ComplaintCategory
    severity: int
    priority: int
    department: str
    justification: str
    source: str


class Report(BaseModel):
    id: str
    category: ComplaintCategory
    severity: int
    priority: int
    department: str
    justification: str
    status: ReportStatus = ReportStatus.PENDING
    lat: float
    lng: float
    image_url: Optional[str] = None
    reported_by: Optional[str] = None


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
