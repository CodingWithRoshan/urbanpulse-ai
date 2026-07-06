"""Derives citizen-facing alerts from live weather/AQI/flood signals."""
from app.domain.schemas import AqiSnapshot, Alert, FloodPrediction, TrafficSnapshot


class AlertsService:
    def build(
        self, aqi: AqiSnapshot, flood: FloodPrediction, traffic: TrafficSnapshot
    ) -> list[Alert]:
        alerts: list[Alert] = []

        if flood.risk in ("Moderate", "High"):
            severity = "high" if flood.risk == "High" else "medium"
            alerts.append(Alert(title="Waterlogging Warning", severity=severity))

        if aqi.aqi > 150:
            alerts.append(Alert(title="AQI Advisory", severity="high" if aqi.aqi > 200 else "medium"))

        if traffic.avg_delay_min > 20:
            alerts.append(Alert(title="Heavy Traffic Congestion", severity="medium"))

        return alerts
