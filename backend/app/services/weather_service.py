"""Real-time weather via Google's Weather API, with OpenWeather as fallback."""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.domain.schemas import WeatherSnapshot

logger = logging.getLogger(__name__)

_GOOGLE_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"
_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    async def _fetch_google(self, lat: float, lng: float) -> WeatherSnapshot:
        params = {
            "key": self._settings.weather_key,
            "location.latitude": lat,
            "location.longitude": lng,
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(_GOOGLE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        return WeatherSnapshot(
            temp_c=round(data["temperature"]["degrees"], 1),
            condition=data["weatherCondition"]["description"]["text"],
            humidity=int(data.get("relativeHumidity", 0)),
            source="google-weather",
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    async def _fetch_openweather(self, lat: float, lng: float) -> WeatherSnapshot:
        params = {
            "lat": lat,
            "lon": lng,
            "appid": self._settings.openweather_api_key,
            "units": "metric",
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(_OPENWEATHER_URL, params=params)
            response.raise_for_status()
            data = response.json()

        return WeatherSnapshot(
            temp_c=round(data["main"]["temp"], 1),
            condition=data["weather"][0]["main"],
            humidity=data["main"]["humidity"],
            source="openweather",
        )

    async def get_current(self, lat: float, lng: float) -> WeatherSnapshot:
        if self._settings.google_weather_configured:
            try:
                return await self._fetch_google(lat, lng)
            except Exception:  # noqa: BLE001
                logger.exception("Google Weather API call failed; trying OpenWeather")

        if self._settings.openweather_api_key:
            try:
                return await self._fetch_openweather(lat, lng)
            except Exception:  # noqa: BLE001
                logger.exception("OpenWeather call failed; falling back to mock data")

        return self._mock()

    @staticmethod
    def _mock() -> WeatherSnapshot:
        return WeatherSnapshot(temp_c=34.0, condition="Hazy Sunshine", humidity=61, source="mock")
