"""
Report persistence.

`FirestoreReportRepository` is the production implementation; when Firestore
isn't configured (local dev, CI, or a judge running the hackathon build
without cloud credentials), `InMemoryReportRepository` implements the exact
same protocol so the rest of the app is unaffected — this mirrors the
original prototype's REPORTS_DB dict but behind a clean interface.
"""
import logging
from typing import Optional

from app.domain.schemas import Report
from app.repositories.base_repository import ReportRepositoryProtocol
from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

_COLLECTION = "reports"


class InMemoryReportRepository(ReportRepositoryProtocol):
    def __init__(self):
        self._store: dict[str, Report] = {}

    async def create(self, report: Report) -> Report:
        self._store[report.id] = report
        return report

    async def get(self, report_id: str) -> Optional[Report]:
        return self._store.get(report_id)

    async def list_all(self, sort_by_priority: bool = True) -> list[Report]:
        reports = list(self._store.values())
        if sort_by_priority:
            reports.sort(key=lambda r: r.priority, reverse=True)
        return reports

    async def list_for_user(self, user_id: str) -> list[Report]:
        return [r for r in self._store.values() if r.reported_by == user_id]

    async def update_status(self, report_id: str, status: str) -> Optional[Report]:
        report = self._store.get(report_id)
        if report is None:
            return None
        updated = report.model_copy(update={"status": status})
        self._store[report_id] = updated
        return updated


class FirestoreReportRepository(ReportRepositoryProtocol):
    def __init__(self, firestore_service: FirestoreService):
        self._db = firestore_service.client

    async def create(self, report: Report) -> Report:
        await self._db.collection(_COLLECTION).document(report.id).set(report.model_dump(mode="json"))
        return report

    async def get(self, report_id: str) -> Optional[Report]:
        doc = await self._db.collection(_COLLECTION).document(report_id).get()
        return Report(**doc.to_dict()) if doc.exists else None

    async def list_all(self, sort_by_priority: bool = True) -> list[Report]:
        docs = self._db.collection(_COLLECTION).stream()
        reports = [Report(**doc.to_dict()) async for doc in docs]
        if sort_by_priority:
            reports.sort(key=lambda r: r.priority, reverse=True)
        return reports

    async def list_for_user(self, user_id: str) -> list[Report]:
        docs = self._db.collection(_COLLECTION).where("reported_by", "==", user_id).stream()
        return [Report(**doc.to_dict()) async for doc in docs]

    async def update_status(self, report_id: str, status: str) -> Optional[Report]:
        doc_ref = self._db.collection(_COLLECTION).document(report_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        await doc_ref.update({"status": status})
        data = doc.to_dict()
        data["status"] = status
        return Report(**data)


def build_report_repository() -> ReportRepositoryProtocol:
    firestore_service = FirestoreService()
    if firestore_service.is_available:
        logger.info("Using FirestoreReportRepository")
        return FirestoreReportRepository(firestore_service)
    logger.warning("Firestore not configured; using InMemoryReportRepository (dev mode)")
    return InMemoryReportRepository()


# Process-wide singleton so in-memory data survives across requests
_report_repository_singleton: Optional[ReportRepositoryProtocol] = None


def get_report_repository() -> ReportRepositoryProtocol:
    global _report_repository_singleton
    if _report_repository_singleton is None:
        _report_repository_singleton = build_report_repository()
    return _report_repository_singleton
