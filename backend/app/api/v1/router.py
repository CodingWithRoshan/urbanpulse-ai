from fastapi import APIRouter

from app.api.v1 import assistant, auth, health, reports, vitals

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(vitals.router)
api_router.include_router(assistant.router)
api_router.include_router(reports.router)
