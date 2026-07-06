"""
Uploads citizen-report photos to Google Cloud Storage.

Falls back to an in-memory data URL when GCS is not configured, so image
upload keeps working end-to-end in a local/dev environment without a bucket.
"""
import base64
import logging
import uuid
from typing import Optional

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage as gcs_storage
except ImportError:  # pragma: no cover
    gcs_storage = None


class StorageService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client = None
        if self.is_available:
            try:
                self._client = gcs_storage.Client(project=self._settings.firestore_project_id or None)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to initialize Cloud Storage client")
                self._client = None

    @property
    def is_available(self) -> bool:
        return gcs_storage is not None and self._settings.gcs_configured

    async def upload_report_image(self, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        object_name = f"reports/{uuid.uuid4()}.jpg"

        if self._client:
            try:
                bucket = self._client.bucket(self._settings.gcs_bucket_name)
                blob = bucket.blob(object_name)
                blob.upload_from_string(image_bytes, content_type=content_type)
                return blob.public_url
            except Exception:  # noqa: BLE001
                logger.exception("GCS upload failed; falling back to inline data URL")

        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{content_type};base64,{encoded}"
