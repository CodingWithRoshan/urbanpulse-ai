"""
Production orchestration graph built on Google's Agent Development Kit.

Activated when `ADK_ENABLED=true` and Gemini credentials are configured
(`Settings.adk_active`). This is the architecture the hackathon brief asks
for: each of the original prototype's agents becomes either an ADK
`LlmAgent` (reasoning steps) wrapping our real service calls as
`FunctionTool`s ("Agent-as-Tool"), or is composed structurally with
`SequentialAgent` / `ParallelAgent` / `LoopAgent`. Session memory is handled
by ADK's `SessionService` instead of our own dict/Firestore session store.

Graph shape:

    root (SequentialAgent)
      ├─ planner_agent                 (LlmAgent, output_key="plan")
      ├─ environment_agent             (LlmAgent + tool, output_key="environment")
      ├─ parallel_agent (ParallelAgent)
      │    ├─ traffic_agent            (LlmAgent + tool, output_key="traffic")
      │    └─ prediction_agent         (LlmAgent + tool, output_key="prediction")
      ├─ risk_score_agent              (LlmAgent + tool, output_key="risk")
      └─ refinement_loop (LoopAgent, max_iterations=2)
           ├─ recommendation_agent     (LlmAgent + tool, output_key="recommendation")
           └─ risk_score_agent_review  (LlmAgent + tool, output_key="risk")

If `google-adk` is not importable (it may lag behind a fast-moving Python
version in some environments) this module raises `AdkUnavailableError` on
first use, and `orchestrator.py` transparently falls back to
`FallbackOrchestrator` so the API never breaks because of it.
"""
import json
import logging
from typing import Optional

from app.agents.data_agents import EnvironmentAgent, PredictionAgent, TrafficAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.risk_score_agent import RiskScoreAgent
from app.core.config import Settings
from app.domain.schemas import CityVitals, DecisionResponse
from app.services.alerts_service import AlertsService
from app.services.timezone_service import TimeZoneService

logger = logging.getLogger(__name__)


class AdkUnavailableError(RuntimeError):
    pass


try:
    from google.adk.agents import Agent, LoopAgent, ParallelAgent, SequentialAgent
    from google.adk.runners import InMemoryRunner
    from google.adk.tools import FunctionTool
    from google.genai import types as genai_types

    _ADK_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:  # pragma: no cover
    Agent = LoopAgent = ParallelAgent = SequentialAgent = InMemoryRunner = FunctionTool = None
    genai_types = None
    _ADK_IMPORT_ERROR = exc


class AdkOrchestrator:
    """Builds and runs the ADK agent graph. One instance per process."""

    def __init__(
        self,
        settings: Settings,
        planner: PlannerAgent,
        traffic_agent: TrafficAgent,
        environment_agent: EnvironmentAgent,
        prediction_agent: PredictionAgent,
        risk_scorer: RiskScoreAgent,
        recommender: RecommendationAgent,
        alerts_service: AlertsService,
        timezone_service: TimeZoneService,
    ):
        if _ADK_IMPORT_ERROR is not None:
            raise AdkUnavailableError(str(_ADK_IMPORT_ERROR))

        self._settings = settings
        self._planner = planner
        self._traffic_agent = traffic_agent
        self._environment_agent = environment_agent
        self._prediction_agent = prediction_agent
        self._risk_scorer = risk_scorer
        self._recommender = recommender
        self._alerts_service = alerts_service
        self._timezone_service = timezone_service
        self._runner: Optional["InMemoryRunner"] = None
        self._latest_lat = settings.default_lat
        self._latest_lng = settings.default_lng

    # Wraps each application agent as a FunctionTool for the LLM layer
    def _build_tools(self):
        async def get_traffic() -> dict:
            snapshot = await self._traffic_agent.run(self._latest_lat, self._latest_lng)
            return snapshot.model_dump()

        async def get_environment() -> dict:
            env = await self._environment_agent.run(self._latest_lat, self._latest_lng)
            return {"weather": env["weather"].model_dump(), "aqi": env["aqi"].model_dump()}

        async def get_flood_prediction(weather_json: str, aqi_json: str) -> dict:
            from app.domain.schemas import AqiSnapshot, WeatherSnapshot

            environment = {
                "weather": WeatherSnapshot(**json.loads(weather_json)),
                "aqi": AqiSnapshot(**json.loads(aqi_json)),
            }
            prediction = await self._prediction_agent.run(environment)
            return prediction.model_dump()

        return {
            "traffic": FunctionTool(func=get_traffic),
            "environment": FunctionTool(func=get_environment),
            "prediction": FunctionTool(func=get_flood_prediction),
        }

    def _build_graph(self):
        tools = self._build_tools()
        model = self._settings.gemini_model

        environment_agent = Agent(
            name="environment_agent",
            model=model,
            description="Fetches live weather and air-quality data for the requested location.",
            instruction="Call the environment tool and return its result verbatim as your output.",
            tools=[tools["environment"]],
            output_key="environment",
        )

        traffic_agent = Agent(
            name="traffic_agent",
            model=model,
            description="Fetches live traffic congestion data for the requested location.",
            instruction="Call the traffic tool and return its result verbatim as your output.",
            tools=[tools["traffic"]],
            output_key="traffic",
        )

        prediction_agent = Agent(
            name="prediction_agent",
            model=model,
            description="Estimates flood/waterlogging risk from environment data.",
            instruction=(
                "Environment data so far: {environment}. Call the prediction tool with the "
                "weather and aqi fields (as JSON strings) and return its result verbatim."
            ),
            tools=[tools["prediction"]],
            output_key="prediction",
        )

        parallel_agent = ParallelAgent(
            name="data_collection",
            sub_agents=[traffic_agent, prediction_agent],
        )

        risk_score_agent = Agent(
            name="risk_score_agent",
            model=model,
            description="Computes a transparent composite risk score.",
            instruction=(
                "Given traffic={traffic}, environment={environment}, prediction={prediction}, "
                "compute a composite 0-100 risk score using 35% AQI, 35% traffic delay, 30% flood "
                "risk. Return JSON: {{\"composite\": <int>, \"components\": {{\"aqi_risk\": <float>, "
                "\"traffic_risk\": <float>, \"flood_risk\": <float>}}}}."
            ),
            output_key="risk",
        )

        recommendation_agent = Agent(
            name="recommendation_agent",
            model=model,
            description="Produces the final citizen-facing recommendation.",
            instruction=(
                "Given intent={plan}, risk={risk}, traffic={traffic}, environment={environment}, "
                "prediction={prediction}, write a short actionable verdict and grounding reason. "
                "Return JSON: {{\"verdict\": \"...\", \"reason\": \"...\", \"risk_score\": <int>}}."
            ),
            output_key="recommendation",
        )

        risk_score_agent_review = Agent(
            name="risk_score_agent_review",
            model=model,
            description="Re-computes the composite risk score after the recommendation is refined.",
            instruction=(
                "Given traffic={traffic}, environment={environment}, prediction={prediction}, "
                "compute a composite 0-100 risk score using 35% AQI, 35% traffic delay, 30% flood "
                "risk. Return JSON: {{\"composite\": <int>, \"components\": {{\"aqi_risk\": <float>, "
                "\"traffic_risk\": <float>, \"flood_risk\": <float>}}}}."
            ),
            output_key="risk",
        )

        refinement_loop = LoopAgent(
            name="refinement_loop",
            sub_agents=[recommendation_agent, risk_score_agent_review],
            max_iterations=2,
        )

        planner_agent = Agent(
            name="planner_agent",
            model=model,
            description="Classifies citizen intent: flood_risk, outdoor_safety, or commute_decision.",
            instruction=(
                "Classify the user's question into exactly one intent: flood_risk, "
                "outdoor_safety, or commute_decision. Return JSON: {{\"intent\": \"...\"}}."
            ),
            output_key="plan",
        )

        root_agent = SequentialAgent(
            name="urbanpulse_pipeline",
            sub_agents=[
                planner_agent,
                environment_agent,
                parallel_agent,
                risk_score_agent,
                refinement_loop,
            ],
        )
        return root_agent

    def _ensure_runner(self):
        if self._runner is None:
            self._runner = InMemoryRunner(agent=self._build_graph(), app_name="urbanpulse")
        return self._runner

    async def run_decision_pipeline(self, question: str, lat: float, lng: float, session_id: str) -> DecisionResponse:
        self._latest_lat, self._latest_lng = lat, lng
        runner = self._ensure_runner()

        session_service = runner.session_service
        await session_service.create_session(
            app_name="urbanpulse", user_id=session_id, session_id=session_id
        )

        final_state: dict = {}
        async for event in runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=genai_types.Content(role="user", parts=[genai_types.Part(text=question)]),
        ):
            if event.is_final_response():
                session = await session_service.get_session(
                    app_name="urbanpulse", user_id=session_id, session_id=session_id
                )
                final_state = dict(session.state)

        return self._parse_final_state(final_state)

    def _parse_final_state(self, state: dict) -> DecisionResponse:
        from app.domain.enums import Intent
        from app.domain.schemas import (
            AqiSnapshot,
            FloodPrediction,
            Recommendation,
            RiskComponents,
            RiskScore,
            TrafficSnapshot,
            WeatherSnapshot,
        )

        def _parse(value, default=None):
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return default
            return value if value is not None else default

        plan = _parse(state.get("plan"), {}) or {}
        environment_raw = _parse(state.get("environment"), {}) or {}
        traffic_raw = _parse(state.get("traffic"), {}) or {}
        prediction_raw = _parse(state.get("prediction"), {}) or {}
        risk_raw = _parse(state.get("risk"), {}) or {}
        recommendation_raw = _parse(state.get("recommendation"), {}) or {}

        environment = {
            "weather": WeatherSnapshot(**environment_raw.get("weather", {})),
            "aqi": AqiSnapshot(**environment_raw.get("aqi", {})),
        }
        traffic = TrafficSnapshot(**traffic_raw)
        prediction = FloodPrediction(**prediction_raw)
        risk = RiskScore(
            composite=risk_raw.get("composite", 0),
            components=RiskComponents(**risk_raw.get("components", {"aqi_risk": 0, "traffic_risk": 0, "flood_risk": 0})),
        )
        recommendation = Recommendation(
            verdict=recommendation_raw.get("verdict", "No recommendation available."),
            reason=recommendation_raw.get("reason", ""),
            risk_score=recommendation_raw.get("risk_score", risk.composite),
        )

        return DecisionResponse(
            intent=Intent(plan.get("intent", "commute_decision")),
            traffic=traffic,
            environment=environment,
            prediction=prediction,
            risk=risk,
            recommendation=recommendation,
        )

    async def get_city_vitals(self, lat: float, lng: float) -> CityVitals:
        # Direct aggregation, no LLM round trip needed
        environment = await self._environment_agent.run(lat, lng)
        traffic = await self._traffic_agent.run(lat, lng)
        prediction = await self._prediction_agent.run(environment)
        city_time = await self._timezone_service.get_current(lat, lng)
        risk = self._risk_scorer.score(traffic, environment, prediction)
        alerts = self._alerts_service.build(environment["aqi"], prediction, traffic)
        health_score = max(0, 100 - risk.composite // 2)

        return CityVitals(
            weather=environment["weather"],
            aqi=environment["aqi"],
            traffic=traffic,
            flood_risk=prediction,
            alerts=alerts,
            community_health_score=health_score,
            city_time=city_time,
        )
