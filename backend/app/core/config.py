"""
Centralized application configuration.

Every external integration is optional at import time: the app must boot and
serve traffic even on a laptop with zero cloud credentials configured. Each
service module checks the relevant `*_enabled` property on `Settings` and
falls back to a clearly-labelled mock implementation when it is False.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "UrbanPulse AI API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Gemini / ADK
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "asia-south1"
    adk_enabled: bool = False

    # Shared key for Google Maps Platform (Weather, Air Quality, Distance
    # Matrix, Time Zone, Maps JS...). Per-service keys below override it if
    # you'd rather use separately restricted keys per API.
    google_api_key: str = ""
    google_maps_api_key: str = ""
    google_weather_api_key: str = ""
    google_aqi_api_key: str = ""
    google_timezone_api_key: str = ""

    # OpenWeather (fallback weather source if Google Weather API key is unset)
    openweather_api_key: str = ""

    # Firestore
    firestore_project_id: str = ""
    firestore_enabled: bool = False

    # Cloud Storage
    gcs_bucket_name: str = ""
    gcs_enabled: bool = False

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    google_oauth_client_id: str = ""

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    # Default city center (Narela, North Delhi)
    default_lat: float = 28.716
    default_lng: float = 77.164

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key) or self.google_genai_use_vertexai

    @property
    def maps_key(self) -> str:
        return self.google_maps_api_key or self.google_api_key

    @property
    def weather_key(self) -> str:
        return self.google_weather_api_key or self.google_api_key

    @property
    def aqi_key(self) -> str:
        return self.google_aqi_api_key or self.google_api_key

    @property
    def timezone_key(self) -> str:
        return self.google_timezone_api_key or self.google_api_key

    @property
    def maps_configured(self) -> bool:
        return bool(self.maps_key)

    @property
    def google_weather_configured(self) -> bool:
        return bool(self.weather_key)

    @property
    def weather_configured(self) -> bool:
        return self.google_weather_configured or bool(self.openweather_api_key)

    @property
    def aqi_configured(self) -> bool:
        return bool(self.aqi_key)

    @property
    def timezone_configured(self) -> bool:
        return bool(self.timezone_key)

    @property
    def firestore_configured(self) -> bool:
        return self.firestore_enabled and bool(self.firestore_project_id)

    @property
    def gcs_configured(self) -> bool:
        return self.gcs_enabled and bool(self.gcs_bucket_name)

    @property
    def adk_active(self) -> bool:
        return self.adk_enabled and self.gemini_configured


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached; env changes require a restart."""
    return Settings()
