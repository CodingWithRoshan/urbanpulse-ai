"""
Thin async wrapper around `google-genai` for both text reasoning
(Gemini 2.5 Flash) and vision-based image classification.

If no API key / Vertex credentials are configured, `is_available` is False
and callers fall back to deterministic heuristics — the rest of the app
never has to special-case "Gemini is missing".
"""
import asyncio
import json
import logging
from typing import Any, Optional

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - library always in requirements.txt
    genai = None
    genai_types = None


class GeminiService:
    """Wraps google-genai's Client so the rest of the app talks to a single,
    swappable interface instead of the SDK directly (dependency inversion)."""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client = None
        if self.is_available:
            try:
                if self._settings.google_genai_use_vertexai:
                    self._client = genai.Client(
                        vertexai=True,
                        project=self._settings.google_cloud_project,
                        location=self._settings.google_cloud_location,
                    )
                else:
                    self._client = genai.Client(api_key=self._settings.gemini_api_key)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to initialize google-genai client")
                self._client = None

    @property
    def is_available(self) -> bool:
        return genai is not None and self._settings.gemini_configured

    async def generate_json(self, prompt: str, system_instruction: str = "") -> Optional[dict[str, Any]]:
        """Ask Gemini to reason over `prompt` and return strict JSON."""
        if not (self.is_available and self._client):
            return None

        def _call() -> str:
            response = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            return response.text

        try:
            raw_text = await asyncio.to_thread(_call)
            return json.loads(raw_text)
        except Exception:  # noqa: BLE001
            logger.exception("Gemini text generation failed; caller will fall back")
            return None

    async def classify_image(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Optional[dict[str, Any]]:
        """Vision classification via Gemini multimodal input."""
        if not (self.is_available and self._client):
            return None

        def _call() -> str:
            response = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=[
                    genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            return response.text

        try:
            raw_text = await asyncio.to_thread(_call)
            return json.loads(raw_text)
        except Exception:  # noqa: BLE001
            logger.exception("Gemini vision classification failed; caller will fall back")
            return None
