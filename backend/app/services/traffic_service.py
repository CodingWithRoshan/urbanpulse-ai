"""
Real-time congestion via the Google Maps Distance Matrix API.

We sample a short radial route around the requested point (center -> a point
~3km north) and compare live duration-in-traffic against free-flow duration
to derive a delay-per-average-trip figure the rest of the pipeline can use.
"""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.domain.schemas import TrafficSnapshot

logger = logging.getLogger(__name__)

_BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
_SAMPLE_OFFSET_DEG = 0.03  # ~3 km


class TrafficService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    async def _fetch_live(self, lat: float, lng: float) -> TrafficSnapshot:
        origin = f"{lat},{lng}"
        destination = f"{lat + _SAMPLE_OFFSET_DEG},{lng}"
        params = {
            "origins": origin,
            "destinations": destination,
            "departure_time": "now",
            "traffic_model": "best_guess",
            "key": self._settings.maps_key,
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        element = data["rows"][0]["elements"][0]
        duration_s = element["duration"]["value"]
        duration_in_traffic_s = element.get("duration_in_traffic", element["duration"])["value"]
        delay_min = max(0.0, (duration_in_traffic_s - duration_s) / 60)

        if delay_min >= 15:
            level = "Heavy"
        elif delay_min >= 6:
            level = "Moderate"
        else:
            level = "Light"

        return TrafficSnapshot(level=level, avg_delay_min=round(delay_min, 1), source="google-maps")

    async def get_current(self, lat: float, lng: float) -> TrafficSnapshot:
        if not self._settings.maps_configured:
            return self._mock()
        try:
            return await self._fetch_live(lat, lng)
        except Exception:  # noqa: BLE001
            logger.exception("Google Maps Distance Matrix call failed; falling back to mock data")
            return self._mock()

    @staticmethod
    def _mock() -> TrafficSnapshot:
        return TrafficSnapshot(level="Heavy", avg_delay_min=22.0, source="mock")
