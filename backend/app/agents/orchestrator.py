"""
Composition root for the multi-agent pipeline.

Builds every agent/service once (simple manual dependency injection — no
need for a heavier DI framework at this scale), then exposes a single
`Orchestrator` facade the API layer talks to. This is the only place that
decides whether requests run through the real Google ADK graph or the
dependency-free fallback graph, so `app/api` never has to know which one is
active.
"""
import logging
from typing import Optional

from app.agents.data_agents import EnvironmentAgent, PredictionAgent, TrafficAgent
from app.agents.fallback_orchestrator import FallbackOrchestrator
from app.agents.planner_agent import PlannerAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.risk_score_agent import RiskScoreAgent
from app.core.config import Settings, get_settings
from app.domain.schemas import CityVitals, DecisionResponse
from app.repositories.base_repository import SessionRepositoryProtocol
from app.repositories.session_repository import get_session_repository
from app.services.alerts_service import AlertsService
from app.services.aqi_service import AqiService
from app.services.flood_prediction_service import FloodPredictionService
from app.services.gemini_service import GeminiService
from app.services.timezone_service import TimeZoneService
from app.services.traffic_service import TrafficService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        session_repository: Optional[SessionRepositoryProtocol] = None,
    ):
        settings = settings or get_settings()
        session_repository = session_repository or get_session_repository()

        gemini_service = GeminiService(settings)
        weather_service = WeatherService(settings)
        aqi_service = AqiService(settings)
        traffic_service = TrafficService(settings)
        flood_service = FloodPredictionService(gemini_service)
        timezone_service = TimeZoneService(settings)

        planner = PlannerAgent(session_repository)
        traffic_agent = TrafficAgent(traffic_service)
        environment_agent = EnvironmentAgent(weather_service, aqi_service)
        prediction_agent = PredictionAgent(flood_service)
        risk_scorer = RiskScoreAgent()
        recommender = RecommendationAgent(gemini_service)
        alerts_service = AlertsService()

        self._fallback = FallbackOrchestrator(
            planner=planner,
            traffic_agent=traffic_agent,
            environment_agent=environment_agent,
            prediction_agent=prediction_agent,
            risk_scorer=risk_scorer,
            recommender=recommender,
            alerts_service=alerts_service,
            timezone_service=timezone_service,
        )

        self._adk = None
        if settings.adk_active:
            try:
                from app.agents.adk_orchestrator import AdkOrchestrator

                self._adk = AdkOrchestrator(
                    settings=settings,
                    planner=planner,
                    traffic_agent=traffic_agent,
                    environment_agent=environment_agent,
                    prediction_agent=prediction_agent,
                    risk_scorer=risk_scorer,
                    recommender=recommender,
                    alerts_service=alerts_service,
                    timezone_service=timezone_service,
                )
                logger.info("ADK orchestration graph active (ADK_ENABLED=true)")
            except Exception:  # noqa: BLE001
                logger.exception("Failed to initialize ADK orchestrator; using fallback orchestrator")
                self._adk = None
        else:
            logger.info("Running with FallbackOrchestrator (set ADK_ENABLED=true to use Google ADK)")

    async def get_city_vitals(self, lat: Optional[float] = None, lng: Optional[float] = None) -> CityVitals:
        settings = get_settings()
        lat = lat if lat is not None else settings.default_lat
        lng = lng if lng is not None else settings.default_lng

        engine = self._adk or self._fallback
        try:
            return await engine.get_city_vitals(lat, lng)
        except Exception:  # noqa: BLE001
            if engine is not self._fallback:
                logger.exception("ADK engine failed for city vitals; retrying on fallback engine")
                return await self._fallback.get_city_vitals(lat, lng)
            raise

    async def run_decision_pipeline(
        self, question: str, lat: Optional[float], lng: Optional[float], session_id: str
    ) -> DecisionResponse:
        settings = get_settings()
        lat = lat if lat is not None else settings.default_lat
        lng = lng if lng is not None else settings.default_lng
        session_id = session_id or "anonymous"

        engine = self._adk or self._fallback
        try:
            return await engine.run_decision_pipeline(question, lat, lng, session_id)
        except Exception:  # noqa: BLE001
            if engine is not self._fallback:
                logger.exception("ADK engine failed for decision pipeline; retrying on fallback engine")
                return await self._fallback.run_decision_pipeline(question, lat, lng, session_id)
            raise


_orchestrator_singleton: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator_singleton
    if _orchestrator_singleton is None:
        _orchestrator_singleton = Orchestrator()
    return _orchestrator_singleton
