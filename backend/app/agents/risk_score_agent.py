"""Transparent, explainable weighted risk score — deliberately not a black box
so citizens and authorities can see exactly why a number was produced."""
from app.domain.schemas import AqiSnapshot, FloodPrediction, RiskComponents, RiskScore, TrafficSnapshot

_FLOOD_RISK_WEIGHTS = {"Low": 10, "Moderate": 45, "High": 80}


class RiskScoreAgent:
    def score(self, traffic: TrafficSnapshot, environment: dict, prediction: FloodPrediction) -> RiskScore:
        aqi: AqiSnapshot = environment["aqi"]

        aqi_risk = min(100.0, aqi.aqi / 3)
        traffic_risk = traffic.avg_delay_min * 2.2
        flood_risk = _FLOOD_RISK_WEIGHTS.get(prediction.risk, 30) * prediction.confidence \
            + _FLOOD_RISK_WEIGHTS.get(prediction.risk, 30) * (1 - prediction.confidence) * 0.5

        composite = round(aqi_risk * 0.35 + traffic_risk * 0.35 + flood_risk * 0.30)
        return RiskScore(
            composite=min(100, composite),
            components=RiskComponents(
                aqi_risk=round(aqi_risk, 1),
                traffic_risk=round(traffic_risk, 1),
                flood_risk=round(flood_risk, 1),
            ),
        )
