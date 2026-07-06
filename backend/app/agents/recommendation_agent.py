"""
Produces the final citizen-facing verdict.

Uses Gemini 2.5 Flash to phrase a grounded recommendation from the upstream
agents' structured outputs. Falls back to the original prototype's
deterministic rules (still fully explainable) if Gemini is unavailable.
"""
from app.domain.enums import Intent
from app.domain.schemas import FloodPrediction, Recommendation, RiskScore, TrafficSnapshot
from app.services.gemini_service import GeminiService

_PROMPT_TEMPLATE = """You are UrbanPulse AI's recommendation engine for a citizen in North Delhi.
Intent: {intent}
Composite risk score (0-100): {composite}
Traffic: {traffic_level}, average delay {delay} minutes
AQI: {aqi} ({aqi_category})
Flood risk: {flood_risk} (confidence {confidence})

Write a short, direct, practical recommendation for the citizen.
Respond ONLY as JSON: {{"verdict": "<one actionable sentence>", "reason": "<one grounding sentence citing the numbers above>"}}
"""


class RecommendationAgent:
    def __init__(self, gemini_service: GeminiService):
        self._gemini = gemini_service

    async def recommend(
        self,
        intent: Intent,
        risk: RiskScore,
        traffic: TrafficSnapshot,
        environment: dict,
        prediction: FloodPrediction,
    ) -> Recommendation:
        aqi = environment["aqi"]
        result = await self._gemini.generate_json(
            prompt=_PROMPT_TEMPLATE.format(
                intent=intent.value,
                composite=risk.composite,
                traffic_level=traffic.level,
                delay=traffic.avg_delay_min,
                aqi=aqi.aqi,
                aqi_category=aqi.category,
                flood_risk=prediction.risk,
                confidence=prediction.confidence,
            ),
            system_instruction="You output only valid, minified JSON. Be concise and practical.",
        )
        if result and {"verdict", "reason"} <= result.keys():
            return Recommendation(verdict=result["verdict"], reason=result["reason"], risk_score=risk.composite)

        return self._deterministic(intent, risk, traffic, environment, prediction)

    @staticmethod
    def _deterministic(
        intent: Intent,
        risk: RiskScore,
        traffic: TrafficSnapshot,
        environment: dict,
        prediction: FloodPrediction,
    ) -> Recommendation:
        aqi = environment["aqi"]
        composite = risk.composite

        if intent == Intent.FLOOD_RISK:
            verdict = (
                "Avoid low-lying routes for the next 2-3 hours."
                if prediction.risk in ("Moderate", "High")
                else "Low-lying areas are currently manageable."
            )
            reason = f"Flood model shows {prediction.risk} risk based on current weather and drainage load."
        elif intent == Intent.OUTDOOR_SAFETY:
            verdict = (
                "Better to postpone strenuous outdoor activity today."
                if aqi.aqi > 150
                else "Conditions are reasonable for light outdoor activity."
            )
            reason = f"AQI is {aqi.aqi} ({aqi.category})."
        else:
            verdict = (
                "Consider leaving 20-25 minutes earlier, or shifting by an hour if flexible."
                if composite > 60
                else "You're clear to leave now - conditions are near normal."
            )
            reason = f"Traffic delay ~{traffic.avg_delay_min} min above baseline; composite risk {composite}/100."

        return Recommendation(verdict=verdict, reason=reason, risk_score=composite)
