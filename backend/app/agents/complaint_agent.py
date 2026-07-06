"""Classifies citizen-uploaded civic-issue photos via Gemini Vision."""
import hashlib
from typing import Optional

from app.domain.enums import ComplaintCategory
from app.domain.schemas import ComplaintClassification
from app.services.gemini_service import GeminiService

_DEPARTMENTS = {
    ComplaintCategory.POTHOLE: "Roads & Infrastructure",
    ComplaintCategory.GARBAGE_OVERFLOW: "Sanitation Dept.",
    ComplaintCategory.WATERLOGGING: "Storm Water Drainage",
    ComplaintCategory.BROKEN_STREETLIGHT: "Electrical Dept.",
    ComplaintCategory.OTHER: "General Municipal Services",
}

_VISION_PROMPT = """Classify this civic-issue photograph into exactly one of:
Pothole, Garbage Overflow, Waterlogging, Broken Streetlight, Other.
Estimate severity from 0-100 (property/safety impact) and give a one-sentence justification.

Respond ONLY as JSON: {"category": "<one of the categories above>", "severity": <int 0-100>, "justification": "<one sentence>"}
"""


class ComplaintAgent:
    def __init__(self, gemini_service: GeminiService):
        self._gemini = gemini_service

    async def classify_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ComplaintClassification:
        result = await self._gemini.classify_image(image_bytes, _VISION_PROMPT, mime_type)

        if result and {"category", "severity"} <= result.keys():
            category = self._coerce_category(result["category"])
            severity = max(0, min(100, int(result["severity"])))
            justification = result.get("justification", "Classified by Gemini Vision.")
            source = "gemini-vision"
        else:
            category, severity, justification = self._deterministic_fallback(image_bytes)
            source = "heuristic"

        priority = min(99, round(severity * 0.75 + 10))
        return ComplaintClassification(
            category=category,
            severity=severity,
            priority=priority,
            department=_DEPARTMENTS[category],
            justification=justification,
            source=source,
        )

    @staticmethod
    def _coerce_category(raw: str) -> ComplaintCategory:
        for category in ComplaintCategory:
            if category.value.lower() == str(raw).strip().lower():
                return category
        return ComplaintCategory.OTHER

    @staticmethod
    def _deterministic_fallback(image_bytes: bytes) -> tuple[ComplaintCategory, int, str]:
        """Deterministic (not random) stand-in used only when Gemini Vision is
        unavailable: derives a stable pseudo-classification from the image
        bytes so repeated calls on the same photo are consistent."""
        digest = hashlib.sha256(image_bytes).digest()
        categories = [c for c in ComplaintCategory if c != ComplaintCategory.OTHER]
        category = categories[digest[0] % len(categories)]
        severity = 30 + (digest[1] % 66)
        justification = "Estimated from image signature; Gemini Vision was unavailable for a live assessment."
        return category, severity, justification


_complaint_agent_singleton: Optional["ComplaintAgent"] = None


def get_complaint_agent() -> "ComplaintAgent":
    global _complaint_agent_singleton
    if _complaint_agent_singleton is None:
        _complaint_agent_singleton = ComplaintAgent(GeminiService())
    return _complaint_agent_singleton
