"""
UrbanPulse AI - FastAPI backend (production architecture)

Run locally:
    pip install -r requirements.txt
    cp .env.example .env   # fill in whichever keys you have
    uvicorn app.main:app --reload --port 8080

Deploy to Cloud Run:
    gcloud run deploy urbanpulse-api --source . --region asia-south1 --allow-unauthenticated
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.legacy_router import legacy_health_router, legacy_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.domain.exceptions import ReportNotFoundError, UpstreamServiceError, UrbanPulseError

settings = get_settings()
configure_logging(settings.environment)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    logger.info(
        "UrbanPulse AI started | env=%s | adk_active=%s | gemini=%s | firestore=%s | gcs=%s | "
        "weather=%s | aqi=%s | maps=%s",
        settings.environment,
        settings.adk_active,
        settings.gemini_configured,
        settings.firestore_configured,
        settings.gcs_configured,
        settings.weather_configured,
        settings.aqi_configured,
        settings.maps_configured,
    )
    yield
    logger.info("UrbanPulse AI shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Multi-agent civic intelligence platform: real-time weather/AQI/traffic/flood "
            "signals, a Gemini-powered decision pipeline, and Gemini Vision complaint triage."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(legacy_router)
    app.include_router(legacy_health_router)

    @app.exception_handler(ReportNotFoundError)
    async def _report_not_found(_: Request, exc: ReportNotFoundError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(UpstreamServiceError)
    async def _upstream_error(_: Request, exc: UpstreamServiceError):
        logger.error("Upstream service error: %s", exc)
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})

    @app.exception_handler(UrbanPulseError)
    async def _domain_error(_: Request, exc: UrbanPulseError):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    return app


app = create_app()
