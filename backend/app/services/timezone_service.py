"""Local time for a location via the Google Time Zone API."""
import logging
import time
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.domain.schemas import CityTime

logger = logging.getLogger(__name__)

_BASE_URL = "https://maps.googleapis.com/maps/api/timezone/json"


class TimeZoneService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    async def _fetch_live(self, lat: float, lng: float) -> CityTime:
        timestamp = int(time.time())
        params = {
            "location": f"{lat},{lng}",
            "timestamp": timestamp,
            "key": self._settings.timezone_key,
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "OK":
            raise ValueError(f"Time Zone API error: {data.get('status')}")

        offset_seconds = data["rawOffset"] + data["dstOffset"]
        local_time = time.strftime("%I:%M %p", time.gmtime(timestamp + offset_seconds))

        return CityTime(
            local_time=local_time.lstrip("0"),
            timezone_id=data["timeZoneId"],
            utc_offset_minutes=offset_seconds // 60,
            source="google-timezone",
        )

    async def get_current(self, lat: float, lng: float) -> CityTime:
        if not self._settings.timezone_configured:
            return self._mock()
        try:
            return await self._fetch_live(lat, lng)
        except Exception:  # noqa: BLE001
            logger.exception("Google Time Zone call failed; falling back to mock data")
            return self._mock()

    @staticmethod
    def _mock() -> CityTime:
        local_time = time.strftime("%I:%M %p").lstrip("0")
        return CityTime(local_time=local_time, timezone_id="Asia/Kolkata", utc_offset_minutes=330, source="mock")
