"""
Unit tests for Authentication module (auth.py).
Tests JWT decoding, HS256 validation, NextAuth.js v5 compatibility,
missing credentials, invalid tokens, and optional user dependencies.
"""
import pytest
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import settings
from auth import decode_token, get_current_user, get_optional_user, AuthUser


@pytest.fixture(autouse=True)
def setup_auth_secret():
    """Ensure AUTH_SECRET is set for tests."""
    original_secret = settings.AUTH_SECRET
    settings.AUTH_SECRET = "test_super_secret_key_for_testing_123"
    yield
    settings.AUTH_SECRET = original_secret


def create_test_token(sub="user-123", email="test@example.com", name="Test User", secret=None):
    secret = secret or settings.AUTH_SECRET
    payload = {
        "sub": sub,
        "email": email,
        "name": name,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_valid_token():
    token = create_test_token(sub="user-456", email="trader@et.com", name="Active Trader")
    payload = decode_token(token)
    assert payload["sub"] == "user-456"
    assert payload["email"] == "trader@et.com"
    assert payload["name"] == "Active Trader"


def test_decode_token_invalid_secret():
    token = create_test_token(secret="wrong_secret_key")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401
    assert "Invalid authentication token" in exc_info.value.detail


def test_decode_token_missing_secret():
    settings.AUTH_SECRET = ""
    token = create_test_token(secret="any_key")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 500
    assert "AUTH_SECRET not configured" in exc_info.value.detail


def test_decode_token_malformed():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.jwt.token")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success():
    token = create_test_token(sub="user-789", email="exec@et.com", name="Executive")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_current_user(creds)
    assert isinstance(user, AuthUser)
    assert user.user_id == "user-789"
    assert user.email == "exec@et.com"
    assert user.name == "Executive"


@pytest.mark.asyncio
async def test_get_current_user_no_credentials():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_missing_sub():
    payload = {"email": "nosub@example.com", "name": "No Sub"}
    token = jwt.encode(payload, settings.AUTH_SECRET, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(creds)
    assert exc_info.value.status_code == 401
    assert "Token missing user identifier" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_optional_user_present():
    token = create_test_token(sub="user-opt", email="opt@et.com", name="Optional")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_optional_user(creds)
    assert user is not None
    assert user.user_id == "user-opt"


@pytest.mark.asyncio
async def test_get_optional_user_missing():
    user = await get_optional_user(None)
    assert user is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage_token")
    user = await get_optional_user(creds)
    assert user is None
