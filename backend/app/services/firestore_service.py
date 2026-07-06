"""Thin wrapper around the Firestore async client, shared by repositories."""
import logging
from typing import Optional

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore
except ImportError:  # pragma: no cover
    firestore = None


class FirestoreService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client = None
        if self._is_configured:
            try:
                self._client = firestore.AsyncClient(project=self._settings.firestore_project_id)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to initialize Firestore client")
                self._client = None

    @property
    def _is_configured(self) -> bool:
        """Whether Firestore *should* be usable, based on config alone.

        This must not depend on self._client: it is evaluated inside
        __init__ before the client exists, to decide whether to create it.
        (A previous version checked `self._client is not None` here, which
        is always False during __init__, so the client was never created
        even with FIRESTORE_ENABLED=true and a valid project ID.)
        """
        return firestore is not None and self._settings.firestore_configured

    @property
    def is_available(self) -> bool:
        """Whether a live Firestore client is actually up and usable now."""
        return self._is_configured and self._client is not None

    @property
    def client(self):
        return self._client
