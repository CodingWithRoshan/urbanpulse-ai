"""
Session memory for the Planner Agent.

When ADK is active (see app/agents/orchestrator.py), ADK's own
`InMemorySessionService` / `VertexAiSessionService` owns session state and
this repository is not on the hot path. It remains as the session store for
the deterministic fallback orchestrator and for the `/api/v1/assistant`
history the frontend can display.
"""
import logging
from typing import Optional

from app.repositories.base_repository import SessionRepositoryProtocol
from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

_COLLECTION = "sessions"


class InMemorySessionRepository(SessionRepositoryProtocol):
    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    async def append(self, session_id: str, entry: dict) -> list[dict]:
        history = self._store.setdefault(session_id, [])
        history.append(entry)
        return history

    async def history(self, session_id: str) -> list[dict]:
        return self._store.get(session_id, [])


class FirestoreSessionRepository(SessionRepositoryProtocol):
    def __init__(self, firestore_service: FirestoreService):
        self._db = firestore_service.client

    async def append(self, session_id: str, entry: dict) -> list[dict]:
        doc_ref = self._db.collection(_COLLECTION).document(session_id)
        doc = await doc_ref.get()
        history = doc.to_dict().get("history", []) if doc.exists else []
        history.append(entry)
        await doc_ref.set({"history": history})
        return history

    async def history(self, session_id: str) -> list[dict]:
        doc = await self._db.collection(_COLLECTION).document(session_id).get()
        return doc.to_dict().get("history", []) if doc.exists else []


def build_session_repository() -> SessionRepositoryProtocol:
    firestore_service = FirestoreService()
    if firestore_service.is_available:
        logger.info("Using FirestoreSessionRepository")
        return FirestoreSessionRepository(firestore_service)
    logger.warning("Firestore not configured; using InMemorySessionRepository (dev mode)")
    return InMemorySessionRepository()


_session_repository_singleton: Optional[SessionRepositoryProtocol] = None


def get_session_repository() -> SessionRepositoryProtocol:
    global _session_repository_singleton
    if _session_repository_singleton is None:
        _session_repository_singleton = build_session_repository()
    return _session_repository_singleton
