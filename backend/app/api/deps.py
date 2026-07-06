"""Shared FastAPI dependency providers (thin functions the routers Depends() on)."""
from app.agents.complaint_agent import ComplaintAgent, get_complaint_agent
from app.agents.orchestrator import Orchestrator, get_orchestrator
from app.repositories.base_repository import ReportRepositoryProtocol
from app.repositories.report_repository import get_report_repository
from app.services.storage_service import StorageService

_storage_service_singleton: StorageService | None = None


def get_orchestrator_dep() -> Orchestrator:
    return get_orchestrator()


def get_complaint_agent_dep() -> ComplaintAgent:
    return get_complaint_agent()


def get_report_repository_dep() -> ReportRepositoryProtocol:
    return get_report_repository()


def get_storage_service_dep() -> StorageService:
    global _storage_service_singleton
    if _storage_service_singleton is None:
        _storage_service_singleton = StorageService()
    return _storage_service_singleton
