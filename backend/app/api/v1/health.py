from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz():
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "adk_active": settings.adk_active,
        "firestore_configured": settings.firestore_configured,
        "gcs_configured": settings.gcs_configured,
        "gemini_configured": settings.gemini_configured,
    }
