class UrbanPulseError(Exception):
    """Base class for all domain-level errors."""


class ReportNotFoundError(UrbanPulseError):
    def __init__(self, report_id: str):
        super().__init__(f"Report '{report_id}' was not found.")
        self.report_id = report_id


class InvalidGoogleTokenError(UrbanPulseError):
    def __init__(self, detail: str = "Google ID token could not be verified."):
        super().__init__(detail)


class UpstreamServiceError(UrbanPulseError):
    """Raised when an external API (Maps/Weather/AQI/Gemini) fails and no
    safe fallback value can be produced."""

    def __init__(self, service: str, detail: str):
        super().__init__(f"{service} error: {detail}")
        self.service = service
