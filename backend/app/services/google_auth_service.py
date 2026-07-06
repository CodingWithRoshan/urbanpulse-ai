"""Verifies Google Identity Services ID tokens for the /auth/google endpoint."""
import logging
from typing import Optional

from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import Settings, get_settings
from app.domain.exceptions import InvalidGoogleTokenError

logger = logging.getLogger(__name__)


class GoogleAuthService:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._request = google_requests.Request()

    def verify(self, token: str) -> dict:
        """Returns the decoded Google payload (sub, email, name, picture)."""
        if not self._settings.google_oauth_client_id:
            raise InvalidGoogleTokenError(
                "GOOGLE_OAUTH_CLIENT_ID is not configured on the server."
            )
        try:
            payload = google_id_token.verify_oauth2_token(
                token, self._request, self._settings.google_oauth_client_id
            )
        except ValueError as exc:
            logger.warning("Google ID token verification failed: %s", exc)
            raise InvalidGoogleTokenError(str(exc)) from exc
        except google_auth_exceptions.TransportError as exc:
            # Treat as a retryable auth failure, not a 500
            logger.warning("Could not reach Google to verify token: %s", exc)
            raise InvalidGoogleTokenError(
                "Could not verify Google sign-in right now. Please try again."
            ) from exc

        return {
            "sub": payload["sub"],
            "email": payload.get("email", ""),
            "name": payload.get("name", payload.get("email", "")),
        }


_google_auth_service_singleton: Optional["GoogleAuthService"] = None


def get_google_auth_service() -> "GoogleAuthService":
    """FastAPI dependency provider.

    Do NOT use `Depends(GoogleAuthService)` directly in routers: FastAPI
    inspects `__init__`'s parameters to build the dependency, and since
    `settings` is a plain (non-Depends) parameter typed as a Pydantic
    model, FastAPI mistakes it for a second request-body field, forcing
    clients to send `{"payload": ..., "settings": ...}` instead of the
    plain request body (this is exactly the `body.payload` 422 you get
    on `/auth/google` otherwise). Routers should depend on this factory
    function instead.
    """
    global _google_auth_service_singleton
    if _google_auth_service_singleton is None:
        _google_auth_service_singleton = GoogleAuthService()
    return _google_auth_service_singleton
