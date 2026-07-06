"""
JWT issuance/verification and role-based access control (RBAC).

Flow:
  1. The Next.js frontend runs Google Identity Services and gets a Google
     ID token.
  2. Frontend calls POST /api/v1/auth/google with that ID token.
  3. Backend verifies it against Google's public keys (google-auth), looks up
     or creates the user, and issues our own short-lived JWT carrying the
     user's role (Citizen / Authority / Admin).
  4. All subsequent requests send `Authorization: Bearer <jwt>`.
"""
import datetime as dt
from typing import Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.domain.enums import Role
from app.domain.schemas import AuthenticatedUser

_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, email: str, role: Role, name: str = "") -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "name": name,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    return AuthenticatedUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        role=Role(payload.get("role", Role.CITIZEN.value)),
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AuthenticatedUser | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_roles(allowed: Iterable[Role]):
    """Dependency factory enforcing role-based access control on a route."""
    allowed_set = set(allowed)

    async def _dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed_set:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Role '{user.role.value}' is not permitted to perform this action.",
            )
        return user

    return _dependency
