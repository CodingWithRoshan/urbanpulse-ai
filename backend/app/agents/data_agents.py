"""
Traffic / Environment / Prediction agents.

These are the three agents that run concurrently inside the ADK
`ParallelAgent` (see orchestrator.py) or, in fallback mode, via
`asyncio.gather`. Each wraps exactly one real external integration so the
concurrency boundary lines up with the I/O boundary.
"""
from app.domain.schemas import FloodPrediction, TrafficSnapshot
from app.services.aqi_service import AqiService
from app.services.flood_prediction_service import FloodPredictionService
from app.services.traffic_service import TrafficService
from app.services.weather_service import WeatherService


class TrafficAgent:
    def __init__(self, traffic_service: TrafficService):
        self._traffic_service = traffic_service

    async def run(self, lat: float, lng: float) -> TrafficSnapshot:
        return await self._traffic_service.get_current(lat, lng)


class EnvironmentAgent:
    def __init__(self, weather_service: WeatherService, aqi_service: AqiService):
        self._weather_service = weather_service
        self._aqi_service = aqi_service

    async def run(self, lat: float, lng: float) -> dict:
        weather = await self._weather_service.get_current(lat, lng)
        aqi = await self._aqi_service.get_current(lat, lng)
        return {"weather": weather, "aqi": aqi}


class PredictionAgent:
    def __init__(self, flood_service: FloodPredictionService):
        self._flood_service = flood_service

    async def run(self, environment: dict) -> FloodPrediction:
        return await self._flood_service.predict(environment["weather"], environment["aqi"])
