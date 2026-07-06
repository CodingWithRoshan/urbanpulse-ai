"""
Backward-compatible route aliases.

The original prototype's frontend calls `/api/city-vitals`, `/api/assistant/ask`,
`/api/reports`, and `/healthz` (no version segment). Rather than break that
contract, we mount the same v1 endpoint handlers a second time under the
legacy paths, so both the existing frontend and the new versioned API
(`/api/v1/...`) work against one implementation.
"""
from fastapi import APIRouter

from app.api.v1 import assistant, auth, health, reports, vitals

legacy_router = APIRouter(prefix="/api")
legacy_router.include_router(auth.router)
legacy_router.include_router(vitals.router)
legacy_router.include_router(assistant.router)
legacy_router.include_router(reports.router)

legacy_health_router = APIRouter()
legacy_health_router.include_router(health.router)
