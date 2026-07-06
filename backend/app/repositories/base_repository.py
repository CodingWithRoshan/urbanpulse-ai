"""Abstract repository interfaces so services depend on protocols, not
concrete storage engines (Dependency Inversion Principle)."""
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.schemas import Report


class ReportRepositoryProtocol(ABC):
    @abstractmethod
    async def create(self, report: Report) -> Report: ...

    @abstractmethod
    async def get(self, report_id: str) -> Optional[Report]: ...

    @abstractmethod
    async def list_all(self, sort_by_priority: bool = True) -> list[Report]: ...

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[Report]: ...

    @abstractmethod
    async def update_status(self, report_id: str, status: str) -> Optional[Report]: ...


class SessionRepositoryProtocol(ABC):
    @abstractmethod
    async def append(self, session_id: str, entry: dict) -> list[dict]: ...

    @abstractmethod
    async def history(self, session_id: str) -> list[dict]: ...
