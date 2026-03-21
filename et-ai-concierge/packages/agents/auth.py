"""
ET AI Concierge — Authentication Module
JWT verification for FastAPI endpoints using NextAuth.js v5 tokens.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from config import settings


# ─── Auth Models ──────────────────────────────────────────────────────────────

class AuthUser(BaseModel):
    """Verified user extracted from JWT."""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None


# ─── Security Scheme ──────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


# ─── JWT Verification ────────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """
    Decode and verify a NextAuth.js v5 JWT.
    NextAuth v5 uses a "raw" HS256 JWT signed with AUTH_SECRET.
    """
    if not settings.AUTH_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_SECRET not configured on server",
        )

    try:
        # NextAuth v5 signs JWTs with the AUTH_SECRET using HS256
        payload = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthUser:
    """
    FastAPI dependency: Extract and verify the user from the JWT.
    Use as: auth_user: AuthUser = Depends(get_current_user)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    # NextAuth v5 puts user info in the token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthUser(
        user_id=user_id,
        email=payload.get("email"),
        name=payload.get("name"),
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[AuthUser]:
    """
    Optional auth dependency — returns None instead of 401 if no token.
    Use for endpoints that work both authenticated and unauthenticated.
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return AuthUser(
            user_id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
        )
    except HTTPException:
        return None
