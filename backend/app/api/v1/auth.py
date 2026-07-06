"""Google Sign-In -> application JWT exchange, plus a `/me` introspection route."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, get_current_user
from app.domain.enums import Role
from app.domain.exceptions import InvalidGoogleTokenError
from app.domain.schemas import AuthenticatedUser, GoogleLoginRequest, TokenResponse
from app.services.google_auth_service import GoogleAuthService, get_google_auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Allowlist for elevated roles (move to Firestore in production)
_AUTHORITY_EMAILS: set[str] = set()
_ADMIN_EMAILS: set[str] = set()


def _resolve_role(email: str) -> Role:
    if email in _ADMIN_EMAILS:
        return Role.ADMIN
    if email in _AUTHORITY_EMAILS:
        return Role.AUTHORITY
    return Role.CITIZEN


@router.post("/google", response_model=TokenResponse)
def login_with_google(payload: GoogleLoginRequest, google_auth: GoogleAuthService = Depends(get_google_auth_service)):
    try:
        profile = google_auth.verify(payload.id_token)
    except InvalidGoogleTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    role = _resolve_role(profile["email"])
    token = create_access_token(user_id=profile["sub"], email=profile["email"], role=role, name=profile["name"])
    return TokenResponse(access_token=token, role=role, email=profile["email"], name=profile["name"])


@router.get("/me", response_model=AuthenticatedUser)
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return current_user
