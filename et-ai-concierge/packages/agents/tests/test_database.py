"""
Unit tests for Database layer (database.py).
Tests SQLite fallback schema initialization, user CRUD,
credentials verification, profile updates, chat history, and audit logging.
"""
import pytest
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import (
    init_db, create_user, create_or_get_user, verify_user_credentials,
    update_user_profile, get_user, save_chat_message, get_chat_history,
    log_audit,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_init_db_creates_tables():
    # Calling init_db multiple times must be idempotent
    init_db()


def test_create_user_auto_id():
    user_id = create_user()
    assert user_id is not None
    assert len(user_id) > 10


def test_create_user_explicit_id():
    fixed_id = str(uuid.uuid4())
    res_id = create_user(fixed_id)
    assert res_id == fixed_id


def test_create_or_get_user_new_and_duplicate():
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user1, is_new1 = create_or_get_user(
        email=test_email,
        name="Test User",
        password="secretpassword123",
        provider="credentials"
    )
    assert is_new1 is True
    assert user1 is not None
    assert user1["email"] == test_email

    # Duplicate call should return the existing user with is_new=False
    user2, is_new2 = create_or_get_user(
        email=test_email,
        name="Test User Updated",
        password="secretpassword123",
        provider="credentials"
    )
    assert is_new2 is False
    assert user2["id"] == user1["id"]


def test_verify_user_credentials_success_and_failure():
    test_email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "correct_password_456"
    create_or_get_user(email=test_email, password=pwd)

    # Valid password
    verified = verify_user_credentials(test_email, pwd)
    assert verified is not None
    assert verified["email"] == test_email

    # Invalid password
    wrong_pwd = verify_user_credentials(test_email, "wrong_password")
    assert wrong_pwd is None

    # Non-existent user
    non_existent = verify_user_credentials("nonexistent@et.com", "any_password")
    assert non_existent is None


def test_update_and_get_user_profile():
    test_email = f"profile_{uuid.uuid4().hex[:8]}@example.com"
    user, _ = create_or_get_user(email=test_email, name="Profile Tester")
    uid = user["id"]

    profile_data = {
        "persona": "PERSONA_ACTIVE_TRADER",
        "risk_score": 9,
        "interests": ["Markets", "Tech", "Options"],
        "goals": ["Wealth Growth"],
        "income_type": "salaried",
        "age_group": "30s",
        "has_emergency_fund": True,
        "home_ownership": "owning",
        "investment_horizon": "1-3 years",
        "is_active_trader": True,
        "primary_goal": "growing",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    }

    update_user_profile(uid, profile_data)
    fetched = get_user(uid)

    assert fetched is not None
    assert fetched["persona"] == "PERSONA_ACTIVE_TRADER"
    assert fetched["risk_score"] == 9
    assert isinstance(fetched["interests"], list)
    assert "Options" in fetched["interests"]
    assert "Wealth Growth" in fetched["goals"]
    assert fetched["onboarding_complete"] == 1 or fetched["onboarding_complete"] is True


def test_get_nonexistent_user():
    fake_id = str(uuid.uuid4())
    user = get_user(fake_id)
    assert user is None


def test_save_and_get_chat_history():
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    save_chat_message(user_id, session_id, "user", "What is Nifty doing?")
    save_chat_message(user_id, session_id, "assistant", "Nifty is up 0.68%.", agent_id="market_intelligence_agent")

    # Fetch by session
    history = get_chat_history(user_id, session_id=session_id, limit=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is Nifty doing?"
    assert history[1]["role"] == "assistant"
    assert history[1]["agent_id"] == "market_intelligence_agent"

    # Limit check
    history_limit1 = get_chat_history(user_id, session_id=session_id, limit=1)
    assert len(history_limit1) == 1


def test_log_audit():
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Should not raise exception
    log_audit(
        user_id=user_id,
        session_id=session_id,
        agent_id="marketplace_agent",
        intent="transact",
        recommendation={"content": "SBI Home Loan", "type": "loan"},
        sources=["https://economictimes.indiatimes.com"],
        reasoning_trace="User asked for home loan rates",
        model_version="test-model",
        confidence=0.95,
        hitl_triggered=False,
        disclaimer_shown=True,
    )
