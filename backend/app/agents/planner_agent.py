"""Understands citizen intent and reads/writes session memory."""
from app.domain.enums import Intent
from app.repositories.base_repository import SessionRepositoryProtocol

_FLOOD_KEYWORDS = ("flood", "water", "drain", "waterlogging")
_OUTDOOR_KEYWORDS = ("jog", "walk", "outdoor", "safe to", "run", "cycle")


class PlannerAgent:
    def __init__(self, session_repository: SessionRepositoryProtocol):
        self._sessions = session_repository

    async def plan(self, question: str, session_id: str) -> dict:
        q = question.lower()
        if any(k in q for k in _FLOOD_KEYWORDS):
            intent = Intent.FLOOD_RISK
        elif any(k in q for k in _OUTDOOR_KEYWORDS):
            intent = Intent.OUTDOOR_SAFETY
        else:
            intent = Intent.COMMUTE_DECISION

        history = await self._sessions.append(session_id, {"question": question, "intent": intent.value})
        return {"intent": intent, "history_length": len(history)}
