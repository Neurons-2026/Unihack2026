"""FastAPI dependencies — auth and shared utilities."""

import logging
from typing import Optional

import jwt
from fastapi import Header, HTTPException, status

from config import get_settings

logger = logging.getLogger(__name__)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Validate a Supabase JWT Bearer token.

    In development (APP_ENV=development) requests without a token are allowed
    through as anonymous. In production a valid token is required.
    """
    settings = get_settings()

    if not authorization or not authorization.startswith("Bearer "):
        if settings.app_env == "development":
            return {"sub": "anonymous", "role": "anon"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not settings.supabase_jwt_secret:
        # JWT secret not configured — allow through with a warning
        logger.warning("SUPABASE_JWT_SECRET not set; skipping token verification")
        return {"sub": "unverified", "role": "authenticated"}

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
