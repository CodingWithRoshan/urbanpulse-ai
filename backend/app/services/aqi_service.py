"""Real-time air quality via the Google Air Quality API (currentConditions:lookup)."""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.domain.schemas import AqiSnapshot

logger = logging.getLogger(__name__)

_BASE_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"


class AqiService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    async def _fetch_live(self, lat: float, lng: float) -> AqiSnapshot:
        payload = {"location": {"latitude": lat, "longitude": lng}}
        params = {"key": self._settings.aqi_key}
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(_BASE_URL, params=params, json=payload)
            response.raise_for_status()
            data = response.json()

        index = data["indexes"][0]
        return AqiSnapshot(
            aqi=int(index.get("aqi", 0)),
            category=index.get("category", "Unknown"),
            dominant_pollutant=index.get("dominantPollutant", "N/A").upper(),
            source="google-air-quality",
        )

    async def get_current(self, lat: float, lng: float) -> AqiSnapshot:
        if not self._settings.aqi_configured:
            return self._mock()
        try:
            return await self._fetch_live(lat, lng)
        except Exception:  # noqa: BLE001
            logger.exception("Google AQI call failed; falling back to mock data")
            return self._mock()

    @staticmethod
    def _mock() -> AqiSnapshot:
        return AqiSnapshot(aqi=187, category="Poor", dominant_pollutant="PM2.5", source="mock")
